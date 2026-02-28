"""
信息提取模块
负责实体识别、关键词提取等
优化版本：避免阻塞操作
"""
import asyncio
import re
from collections import Counter
from typing import List, Set

import jieba

from src.models import ContentItem


class KeywordExtractor:
    """关键词提取器（优化版 - 异步非阻塞）"""
    
    # 停用词
    STOP_WORDS = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
        "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
        "自己", "这", "中", "为", "来", "个", "能", "以", "可", "而", "及", "与",
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "from",
        "as", "into", "through", "during", "before", "after", "above", "below",
        "between", "under", "and", "but", "or", "yet", "so", "if", "because",
        "although", "though", "while", "where", "when", "that", "which", "who",
        "whom", "whose", "what", "this", "these", "those", "i", "you", "he",
        "she", "it", "we", "they", "me", "him", "her", "us", "them"
    }
    
    async def extract(self, item: ContentItem, top_k: int = 10) -> List[str]:
        """
        提取关键词（异步非阻塞）
        """
        text = f"{item.title} {item.content or ''}"
        if not text:
            return []
        
        # 合并已有的关键词
        existing = set(item.keywords) if item.keywords else set()
        
        # 在后台线程执行分词（避免阻塞事件循环）
        freq_keywords = await asyncio.to_thread(
            self._extract_by_frequency_sync, text, top_k * 2
        )
        
        # 提取模式匹配的关键词（正则很快，不需要放到线程）
        pattern_keywords = self._extract_patterns(text)
        
        # 合并去重
        all_keywords = list(existing) + freq_keywords + pattern_keywords
        
        # 去重并保持顺序
        seen = set()
        result = []
        for kw in all_keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen and len(kw) > 1:
                seen.add(kw_lower)
                result.append(kw)
                if len(result) >= top_k:
                    break
        
        return result
    
    def _extract_by_frequency_sync(self, text: str, top_k: int) -> List[str]:
        """同步词频提取（在线程池中运行）"""
        try:
            words = self._tokenize_sync(text)
            
            if len(words) < 5:
                return words[:top_k]
            
            filtered_words = [
                w for w in words 
                if w.lower() not in self.STOP_WORDS 
                and len(w) > 1
                and not w.isdigit()
            ]
            
            word_freq = Counter(filtered_words)
            return [word for word, _ in word_freq.most_common(top_k)]
            
        except Exception:
            return []
    
    def _tokenize_sync(self, text: str) -> List[str]:
        """同步分词（在线程池中运行）"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)
        
        if chinese_chars > total_chars * 0.1:  # 中文内容
            words = list(jieba.cut(text))
            words = [w.strip() for w in words if w.strip() and len(w.strip()) > 1]
            return words
        else:  # 英文内容
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            return [w for w in words if len(w) > 2]
    
    def _extract_patterns(self, text: str) -> List[str]:
        """提取模式匹配的关键词"""
        keywords = []
        
        tech_patterns = [
            r"\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b",
            r"\b[A-Z]{2,}\b",
            r"\bGPT-[0-9.]+\b",
            r"\bClaude-[0-9.]+\b",
            r"\bLlama-[0-9.]+\b",
            r"\b[A-Za-z]+\.js\b",
            r"\b[A-Za-z]+\.py\b",
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        return keywords


class EntityExtractor:
    """实体提取器（简化版）"""
    
    ENTITY_PATTERNS = {
        "person": r"[\u4e00-\u9fff]{2,4}(?:先生|女士|博士|教授| CEO| CTO| 总裁| 创始人)",
        "company": r"[\u4e00-\u9fff]{2,}(?:公司|集团|科技|网络|实验室|研究院)|\b[A-Z][a-zA-Z]*(?: Inc| Corp| Ltd| Company)",
        "product": r"[\u4e00-\u9fff]{2,}(?:手机|电脑|应用|平台|系统)|iPhone|iPad|MacBook|Galaxy|Pixel",
        "technology": r"AI|人工智能|机器学习|深度学习|区块链|云计算|大数据|5G|物联网|AR|VR|NLP|CV"
    }
    
    def extract(self, item: ContentItem) -> List[str]:
        """提取实体"""
        text = f"{item.title} {item.content or ''}"
        if not text:
            return []
        
        entities = set()
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update(matches)
        
        return list(entities)[:10]


class TopicClassifier:
    """主题分类器"""
    
    TOPIC_KEYWORDS = {
        "人工智能": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "GPT", "LLM", "大模型"],
        "区块链": ["区块链", "Bitcoin", "以太坊", "加密货币", "Web3", "DeFi", "NFT"],
        "云计算": ["云计算", "AWS", "Azure", "云原生", "K8s", "Kubernetes", "Docker", "容器"],
        "前端开发": ["前端", "React", "Vue", "Angular", "JavaScript", "TypeScript", "CSS", "HTML"],
        "后端开发": ["后端", "Python", "Java", "Go", "Rust", "Node.js", "数据库", "API"],
        "移动开发": ["iOS", "Android", "Flutter", "React Native", "Swift", "Kotlin"],
        "数据科学": ["数据科学", "数据分析", "数据挖掘", "Pandas", "NumPy", "可视化"],
        "网络安全": ["安全", "黑客", "漏洞", "加密", "隐私", "防火墙", "渗透测试"],
        "产品运营": ["产品", "运营", "增长", "用户", "留存", "转化", "PMF", "MVP"],
        "创业投资": ["创业", "投资", "融资", "VC", "天使轮", "IPO", "独角兽", "估值"]
    }
    
    def classify(self, item: ContentItem) -> List[str]:
        """主题分类"""
        text = f"{item.title} {item.content or ''}".lower()
        if not text:
            return []
        
        topic_scores = {}
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text:
                    score += 1
            
            if score > 0:
                topic_scores[topic] = score
        
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics[:3]]
