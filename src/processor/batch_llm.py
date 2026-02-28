"""
批量 LLM 处理模块
支持将多条内容一次性发送给大模型处理
"""
import json
import re
from typing import List, Dict, Tuple, Optional, ClassVar, Any

import httpx

from src.config import get_settings
from src.models import ContentItem


class BatchLLMProcessor:
    """
    批量 LLM 处理器
    
    将多条内容一次性发送给 LLM，减少 API 调用次数
    
    优化：
    - 类级别客户端缓存，避免重复初始化
    - 延迟加载配置
    - 连接池复用
    """
    
    # 单次最大处理条数（减少到 20，避免 JSON 过长被截断）
    MAX_BATCH_SIZE = 20
    # 单次最大 token 数（内容长度限制）
    MAX_CONTENT_LENGTH = 48000
    # 超时时间
    TIMEOUT = 300.0  # 增加到 5 分钟，处理大量内容
    
    # 类级别客户端缓存（所有实例共享）
    _client_cache: ClassVar[Optional[Any]] = None
    _model_cache: ClassVar[Optional[str]] = None
    _init_error: ClassVar[Optional[str]] = None
    
    def __init__(self):
        # 延迟初始化，不在这里创建客户端
        self._local_client = None
    
    @classmethod
    def _get_cached_client(cls):
        """获取缓存的客户端（类级别单例）"""
        if cls._client_cache is not None:
            return cls._client_cache, cls._model_cache
        
        if cls._init_error is not None:
            return None, None
        
        try:
            from openai import AsyncOpenAI
            
            settings = get_settings()
            api_key = settings.llm_api_key or settings.openai_api_key
            base_url = settings.llm_base_url or settings.openai_base_url
            model = settings.llm_model or settings.openai_model
            
            if not api_key:
                cls._init_error = "未配置 API Key"
                return None, None
            
            # 使用 httpx.AsyncClient 连接池
            http_client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=50
                ),
                timeout=httpx.Timeout(cls.TIMEOUT, connect=10.0)
            )
            
            cls._client_cache = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url or None,
                http_client=http_client
            )
            cls._model_cache = model
            
            print(f"[BatchLLM] 客户端初始化成功，模型: {model}")
            
        except Exception as e:
            cls._init_error = str(e)
            print(f"[BatchLLM] 初始化失败: {e}")
            return None, None
        
        return cls._client_cache, cls._model_cache
    
    @property
    def client(self):
        """获取客户端（使用缓存）"""
        if self._local_client is None:
            self._local_client, _ = self._get_cached_client()
        return self._local_client
    
    @property
    def model(self):
        """获取模型（使用缓存）"""
        _, model = self._get_cached_client()
        return model
    
    async def batch_process(
        self, 
        items: List[ContentItem],
        style: str = "3_points"
    ) -> List[Tuple[str, List[str]]]:
        """
        批量处理内容
        
        Args:
            items: 内容条目列表（建议不超过 MAX_BATCH_SIZE）
            style: 摘要风格
            
        Returns:
            List[Tuple[str, List[str]]]: (摘要, 关键要点) 列表，与输入顺序一致
        """
        if not self.client or not items:
            return []
        
        # 分批处理（如果内容过多）
        if len(items) > self.MAX_BATCH_SIZE:
            results = []
            batch_count = (len(items) + self.MAX_BATCH_SIZE - 1) // self.MAX_BATCH_SIZE
            
            for i in range(0, len(items), self.MAX_BATCH_SIZE):
                batch = items[i:i + self.MAX_BATCH_SIZE]
                batch_idx = i // self.MAX_BATCH_SIZE + 1
                print(f"[BatchLLM] 处理批次 {batch_idx}/{batch_count}, {len(batch)} 条")
                
                batch_results = await self._process_single_batch(batch, style)
                results.extend(batch_results)
            
            return results
        
        return await self._process_single_batch(items, style)
    
    async def _process_single_batch(
        self, 
        items: List[ContentItem],
        style: str
    ) -> List[Tuple[str, List[str]]]:
        """处理单批内容"""
        import time
        start_time = time.time()
        
        # 构建批量 prompt
        prompt = self._build_batch_prompt(items, style)
        prompt_build_time = time.time() - start_time
        
        try:
            api_start = time.time()
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的新闻摘要助手。请为每条内容生成简洁准确的摘要，以 JSON 格式返回。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=min(16000, 1000 + len(items) * 600)  # 增加 token 限制，每条约 600 tokens
            )
            api_time = time.time() - api_start
            
            content = response.choices[0].message.content.strip()
            
            # 解析 JSON 响应
            parse_start = time.time()
            results = self._parse_batch_response(content, len(items))
            parse_time = time.time() - parse_start
            
            total_time = time.time() - start_time
            
            # 检查是否成功
            if results and len(results) == len(items):
                print(f"[BatchLLM] ✓ 批次处理成功: {len(items)} 条, "
                      f"总耗时: {total_time:.1f}s (构建: {prompt_build_time:.1f}s, "
                      f"API: {api_time:.1f}s, 解析: {parse_time:.1f}s)")
                return results
            
            print(f"[BatchLLM] ✗ 解析失败或结果不完整，降级处理")
            return await self._fallback_process(items, style)
            
        except Exception as e:
            print(f"[BatchLLM] ✗ API 调用失败: {e}，降级到逐条处理")
            return await self._fallback_process(items, style)
    
    def _build_batch_prompt(self, items: List[ContentItem], style: str) -> str:
        """构建批量处理的 prompt"""
        
        style_instructions = {
            "1_sentence": "用一句话概括核心观点（50字以内）",
            "3_points": "提取3-5个关键要点，每个要点用一句话描述",
            "paragraph": "生成1-2段简短的总结（200字以内）",
            "detailed": "生成详细的摘要，保留关键细节（500字以内）"
        }
        
        instruction = style_instructions.get(style, style_instructions["3_points"])
        
        # 构建内容列表
        contents = []
        for i, item in enumerate(items):
            content_text = item.content or ""
            # 截断过长的内容
            max_per_item = self.MAX_CONTENT_LENGTH // len(items)
            if len(content_text) > max_per_item:
                content_text = content_text[:max_per_item] + "..."
            
            contents.append(f"""[{i}]
标题：{item.title}
来源：{item.source}
内容：{content_text}
""")
        
        prompt = f"""请为以下 {len(items)} 条内容生成摘要。

要求：
- {instruction}
- 保留关键事实和数据
- 语言简洁准确
- 必须以有效的 JSON 数组格式返回

内容列表：
{''.join(contents)}

重要：请严格按以下 JSON 格式返回，确保是有效的 JSON：
1. 返回一个 JSON 数组
2. 每个元素包含 "summary"（字符串）和 "key_points"（字符串数组）
3. 字符串使用双引号
4. 数组元素之间用逗号分隔
5. 不要包含任何 markdown 标记或其他文字

正确格式示例：
[
  {{"summary": "摘要内容", "key_points": ["要点1", "要点2"]}},
  {{"summary": "摘要内容", "key_points": ["要点1", "要点2"]}}
]

请返回 {len(items)} 个元素的 JSON 数组：
"""
        return prompt
    
    def _parse_batch_response(
        self, 
        content: str, 
        expected_count: int
    ) -> List[Tuple[str, List[str]]]:
        """
        解析批量响应（增强版，处理各种格式问题）
        """
        import json
        
        # 清理可能的 markdown 标记
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # 尝试多种解析策略
        strategies = [
            self._parse_strict_json,
            self._parse_with_regex,
            self._parse_truncated_json,  # 新增：处理被截断的 JSON
            self._parse_line_by_line,
            self._parse_flexible,
        ]
        
        for strategy in strategies:
            try:
                results = strategy(content, expected_count)
                if results and len(results) == expected_count:
                    return results
            except Exception as e:
                continue
        
        # 所有策略都失败，输出部分原始内容帮助调试
        print(f"[BatchLLM] 所有解析策略都失败")
        print(f"[BatchLLM] 原始内容前 500 字符:\n{content[:500]}")
        return []
    
    def _parse_strict_json(self, content: str, expected_count: int) -> List[Tuple[str, List[str]]]:
        """严格 JSON 解析"""
        data = json.loads(content)
        return self._extract_results(data, expected_count)
    
    def _parse_with_regex(self, content: str, expected_count: int) -> List[Tuple[str, List[str]]]:
        """使用正则提取 JSON 数组"""
        # 匹配最外层的中括号
        match = re.search(r'\[[\s\S]*\]', content)
        if not match:
            raise ValueError("未找到 JSON 数组")
        
        json_str = match.group()
        data = json.loads(json_str)
        return self._extract_results(data, expected_count)
    
    def _parse_truncated_json(self, content: str, expected_count: int) -> List[Tuple[str, List[str]]]:
        """处理被截断的 JSON（尝试修复并解析）"""
        # 尝试找到最后一个完整的条目
        # 模式：查找最后一个完整的 {...}
        pattern = r'\{\s*"summary"\s*:\s*"[^"]*"\s*,\s*"key_points"\s*:\s*\[[^\]]*\]\s*\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            # 构建一个有效的 JSON 数组
            fixed_json = "[" + ", ".join(matches) + "]"
            try:
                data = json.loads(fixed_json)
                return self._extract_results(data, expected_count)
            except:
                pass
        
        # 如果上面的方法失败，尝试更宽松的匹配
        # 匹配包含 summary 的对象
        pattern2 = r'\{[^{}]*"summary"[^{}]*\}'
        matches2 = re.findall(pattern2, content, re.DOTALL)
        
        if matches2:
            results = []
            for match in matches2:
                # 提取 summary
                summary_match = re.search(r'"summary"\s*:\s*"([^"]*)"', match)
                summary = summary_match.group(1) if summary_match else ""
                
                # 尝试提取 key_points
                kp_match = re.search(r'"key_points"\s*:\s*(\[[^\]]*\])', match)
                key_points = []
                if kp_match:
                    try:
                        key_points = json.loads(kp_match.group(1))
                    except:
                        pass
                
                results.append((summary, key_points if isinstance(key_points, list) else []))
            
            return results
        
        raise ValueError("无法解析被截断的 JSON")
    
    def _parse_line_by_line(self, content: str, expected_count: int) -> List[Tuple[str, List[str]]]:
        """逐行解析（处理每个条目的 JSON）"""
        results = []
        
        # 查找所有类似 {"summary": ..., "key_points": ...} 的对象
        pattern = r'\{\s*"summary"\s*:\s*"([^"]*)"\s*,\s*"key_points"\s*:\s*(\[[^\]]*\])\s*\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for summary, key_points_str in matches:
            try:
                key_points = json.loads(key_points_str)
            except:
                # 如果解析失败，尝试手动提取
                key_points = [p.strip().strip('"').strip("'") for p in key_points_str.split(",") if p.strip()]
            
            results.append((summary, key_points if isinstance(key_points, list) else []))
        
        return results
    
    def _parse_flexible(self, content: str, expected_count: int) -> List[Tuple[str, List[str]]]:
        """灵活解析（处理各种格式问题）"""
        results = []
        
        # 尝试查找 summary 和 key_points 的模式
        # 模式 1: "summary": "..." 后面跟着 "key_points": [...]
        entries = re.split(r'\}\s*,\s*\{', content)
        
        for entry in entries:
            entry = "{" + entry.strip("{} ") + "}"
            
            # 提取 summary
            summary_match = re.search(r'"summary"\s*:\s*"([^"]*)"', entry)
            summary = summary_match.group(1) if summary_match else ""
            
            # 提取 key_points
            kp_match = re.search(r'"key_points"\s*:\s*(\[[^\]]*\])', entry)
            key_points = []
            if kp_match:
                kp_str = kp_match.group(1)
                try:
                    key_points = json.loads(kp_str)
                except:
                    # 手动提取字符串
                    key_points = re.findall(r'"([^"]*)"', kp_str)
            
            results.append((summary, key_points if isinstance(key_points, list) else []))
        
        return results
    
    def _extract_results(self, data, expected_count: int) -> List[Tuple[str, List[str]]]:
        """从解析的数据中提取结果"""
        if not isinstance(data, list):
            raise ValueError("数据不是数组格式")
        
        results = []
        for item in data:
            if isinstance(item, dict):
                summary = item.get("summary", "")
                key_points = item.get("key_points", [])
                
                if isinstance(key_points, str):
                    key_points = [p.strip() for p in key_points.split("\n") if p.strip()]
                elif not isinstance(key_points, list):
                    key_points = []
                
                results.append((summary, key_points))
            else:
                results.append(("", []))
        
        # 补充缺失的结果
        while len(results) < expected_count:
            results.append(("", []))
        
        return results[:expected_count]
    
    async def _fallback_process(
        self, 
        items: List[ContentItem],
        style: str
    ) -> List[Tuple[str, List[str]]]:
        """
        降级处理方案
        1. 尝试使用 LLM 逐条处理（如果只有少量条目）
        2. 使用抽取式摘要
        """
        from src.processor.summarizer import ExtractiveSummarizer, LLMSummarizer
        
        # 如果条目较少，尝试用 LLM 逐条处理
        if len(items) <= 5 and self.client:
            print(f"[BatchLLM] 尝试用 LLM 逐条处理 {len(items)} 条内容")
            results = []
            summarizer = LLMSummarizer(max_concurrency=3)
            
            for item in items:
                try:
                    summary = await summarizer.summarize(item, style)
                    points = [p.strip().lstrip("•-・").strip() for p in summary.split("\n")]
                    key_points = [p for p in points if p and len(p) > 10]
                    results.append((summary, key_points))
                except Exception as e:
                    print(f"逐条 LLM 处理失败: {e}")
                    # 降级到抽取式
                    fallback = ExtractiveSummarizer()
                    summary = await fallback.summarize(item, style)
                    points = [p.strip().lstrip("•-・").strip() for p in summary.split("\n")]
                    key_points = [p for p in points if p and len(p) > 10]
                    results.append((summary, key_points))
            
            return results
        
        # 使用抽取式摘要
        print(f"[BatchLLM] 使用抽取式摘要作为降级方案")
        results = []
        fallback = ExtractiveSummarizer()
        
        for item in items:
            try:
                summary = await fallback.summarize(item, style)
                points = [p.strip().lstrip("•-・").strip() for p in summary.split("\n")]
                key_points = [p for p in points if p and len(p) > 10]
                results.append((summary, key_points))
            except Exception as e:
                print(f"抽取式处理失败: {item.title[:50]}... - {e}")
                results.append((item.title, []))
        
        return results
    
    async def smart_batch_process(
        self,
        items: List[ContentItem],
        style: str = "3_points",
        use_single_call: bool = True
    ) -> List[Tuple[str, List[str]]]:
        """
        智能批量处理
        
        根据内容长度和数量决定使用单次调用还是分批调用
        """
        if not items:
            return []
        
        total_length = sum(len(item.content or "") for item in items)
        
        # 如果内容较少，尝试一次性处理
        if use_single_call and len(items) <= self.MAX_BATCH_SIZE and total_length < self.MAX_CONTENT_LENGTH:
            print(f"[BatchLLM] 尝试单次处理 {len(items)} 条内容，总长度 {total_length}")
            results = await self._process_single_batch(items, style)
            
            if results and len(results) == len(items) and all(r[0] for r in results):
                return results
            
            print(f"[BatchLLM] 单次处理未返回完整结果，切换到分批处理")
        
        # 分批处理
        return await self.batch_process(items, style)
