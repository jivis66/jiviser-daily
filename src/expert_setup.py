"""
LLM 辅助专家配置模式
先配置 LLM，然后让 LLM 通过对话帮助用户完成所有配置
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.tree import Tree

console = Console()


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None


class LLMAssistedSetup:
    """LLM 辅助配置向导"""

    def __init__(self):
        self.llm_config: Optional[LLMConfig] = None
        self.config_dir = Path(__file__).parent.parent / "config"
        self.data_dir = Path(__file__).parent.parent / "data"
        self.conversation_history: List[Dict] = []

    async def run(self):
        """运行专家配置模式"""
        console.print(Panel.fit(
            "[bold blue]🎯 LLM 辅助专家配置模式[/bold blue]\n\n"
            "此模式将:\n"
            "1. 先配置 LLM（用于智能辅助）\n"
            "2. 然后与 AI 对话完成所有配置\n\n"
            "AI 会帮你:\n"
            "• 分析你的需求\n"
            "• 推荐合适的数据源\n"
            "• 解释配置选项\n"
            "• 自动生成配置",
            border_style="blue"
        ))

        # 步骤1：配置 LLM
        if not await self._setup_llm():
            console.print("[red]✗ LLM 配置失败，无法进入专家模式[/red]")
            return False

        # 步骤2：LLM 辅助配置
        await self._llm_assisted_configuration()

        return True

    async def _setup_llm(self) -> bool:
        """配置 LLM"""
        console.print("\n[bold cyan]步骤 1/2: 配置 LLM[/bold cyan]")
        console.print("首先需要配置一个 LLM 来辅助后续配置\n")

        # 选择提供商
        providers = [
            ("1", "openai", "🌐 OpenAI", "稳定高质量"),
            ("2", "moonshot", "🌙 Kimi", "中文长文本"),
            ("3", "qwen", "🤖 通义千问", "中文优化"),
            ("4", "openrouter", "🔗 OpenRouter", "多模型接入"),
            ("5", "ollama", "🏠 Ollama", "本地部署"),
        ]

        console.print("[bold]选择 LLM 提供商:[/bold]")
        for num, key, name, desc in providers:
            console.print(f"  [{num}] {name} - {desc}")

        choice = Prompt.ask("请选择", choices=[p[0] for p in providers], default="1")
        provider = providers[int(choice) - 1][1]

        # 输入 API Key
        api_key = Prompt.ask(f"请输入 {provider} API Key", password=True)

        if not api_key:
            console.print("[red]API Key 不能为空[/red]")
            return False

        # 选择模型
        model = await self._select_model(provider)

        # 可选：自定义 base_url
        base_url = None
        if Confirm.ask("是否需要自定义 API 地址?", default=False):
            base_url = Prompt.ask("请输入 API 基础 URL")

        # 测试连接
        self.llm_config = LLMConfig(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url
        )

        with console.status("[bold green]正在测试 LLM 连接..."):
            if await self._test_llm():
                console.print(f"[green]✓ LLM 配置成功: {model}[/green]\n")
                return True
            else:
                console.print("[red]✗ LLM 连接测试失败，请检查 API Key[/red]")
                return False

    async def _select_model(self, provider: str) -> str:
        """选择模型"""
        models_map = {
            "openai": [
                ("gpt-4o-mini", "GPT-4o-mini (推荐，性价比高)"),
                ("gpt-4o", "GPT-4o (最强性能)"),
                ("gpt-4-turbo", "GPT-4 Turbo"),
            ],
            "moonshot": [
                ("moonshot-v1-128k", "Kimi K1 128K (推荐)"),
                ("moonshot-v1-32k", "Kimi K1 32K"),
            ],
            "qwen": [
                ("qwen-max", "Qwen Max (推荐)"),
                ("qwen-plus", "Qwen Plus"),
                ("qwen-turbo", "Qwen Turbo"),
            ],
            "openrouter": [
                ("openai/gpt-4o-mini", "GPT-4o-mini (推荐)"),
                ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
            ],
            "ollama": [
                ("qwen2.5:14b", "Qwen2.5 14B (推荐)"),
                ("llama3.2", "Llama 3.2"),
            ],
        }

        models = models_map.get(provider, [("gpt-4o-mini", "Default")])

        console.print(f"\n[bold]选择模型:[/bold]")
        for i, (model_id, desc) in enumerate(models, 1):
            console.print(f"  [{i}] {desc}")

        choice = Prompt.ask("请选择", choices=[str(i) for i in range(1, len(models) + 1)], default="1")
        return models[int(choice) - 1][0]

    async def _test_llm(self) -> bool:
        """测试 LLM 连接"""
        try:
            headers = {
                "Authorization": f"Bearer {self.llm_config.api_key}",
                "Content-Type": "application/json"
            }

            base_url = self.llm_config.base_url or self._get_default_base_url(self.llm_config.provider)

            payload = {
                "model": self.llm_config.model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                return response.status_code == 200

        except Exception as e:
            console.print(f"[red]连接错误: {e}[/red]")
            return False

    def _get_default_base_url(self, provider: str) -> str:
        """获取默认 base URL"""
        urls = {
            "openai": "https://api.openai.com/v1",
            "moonshot": "https://api.moonshot.cn/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "ollama": "http://localhost:11434/v1",
        }
        return urls.get(provider, "https://api.openai.com/v1")

    async def _llm_assisted_configuration(self):
        """LLM 辅助配置主流程"""
        console.print("\n[bold cyan]步骤 2/2: LLM 辅助配置[/bold cyan]")
        console.print("现在你可以和 AI 对话来完成配置。告诉我:\n")
        console.print("• 你的职业或角色")
        console.print("• 你关注的话题")
        console.print("• 你希望日报包含什么内容\n")

        # 系统提示词
        system_prompt = """你是 Daily Agent 配置专家。你的任务是帮助用户配置个性化日报系统。

通过对话了解用户需求，然后生成 YAML 配置文件。

你需要收集的信息：
1. 用户画像：职业、行业、专业领域
2. 兴趣偏好：关注的话题、内容类型偏好
3. 日报设置：分栏、数据源、推送渠道

生成配置时要：
1. 解释你的推荐逻辑
2. 询问用户确认
3. 生成有效的 columns.yaml 配置

输出格式要求：
- 使用中文交流
- 解释技术概念
- 给出具体可操作的选项"""

        self.conversation_history.append({"role": "system", "content": system_prompt})

        # 初始问候
        welcome_msg = await self._chat_with_llm(
            "请向用户问好并询问他们的职业和兴趣，以便为他们配置日报。"
        )
        console.print(f"\n[bold green]🤖 AI:[/bold green] {welcome_msg}\n")

        # 对话循环
        collected_info = {
            "profession": None,
            "interests": [],
            "content_preference": None,
            "time_available": None,
        }

        while True:
            user_input = Prompt.ask("[bold blue]你[/bold blue]")

            if user_input.lower() in ["exit", "quit", "退出", "结束"]:
                console.print("\n[yellow]已退出配置[/yellow]")
                break

            if user_input.lower() in ["done", "完成", "ok", "确认"]:
                if await self._generate_configuration():
                    break
                continue

            # 分析用户输入，提取关键信息
            analysis_prompt = f"""用户输入: {user_input}

当前已收集信息: {json.dumps(collected_info, ensure_ascii=False)}

请:
1. 分析用户输入，更新已收集信息
2. 如果发现新的信息，确认并记录
3. 如果信息还不够生成配置，继续友好地询问
4. 如果信息足够，可以说"现在可以生成配置了，输入 '完成' 确认"

直接回复用户，保持对话自然。"""

            response = await self._chat_with_llm(analysis_prompt)
            console.print(f"\n[bold green]🤖 AI:[/bold green] {response}\n")

            # 尝试提取信息（简单规则）
            if any(word in user_input for word in ["开发", "程序员", "工程师", "技术"]):
                collected_info["profession"] = "tech_developer"
            elif any(word in user_input for word in ["产品", "PM", "经理"]):
                collected_info["profession"] = "product_manager"
            elif any(word in user_input for word in ["投资", "分析师", "金融"]):
                collected_info["profession"] = "investor"

            # 检查是否可以生成配置
            if collected_info["profession"] and len(self.conversation_history) > 5:
                console.print("[dim]💡 提示: 输入 '完成' 让 AI 生成配置[/dim]\n")

    async def _chat_with_llm(self, message: str) -> str:
        """与 LLM 对话"""
        self.conversation_history.append({"role": "user", "content": message})

        try:
            headers = {
                "Authorization": f"Bearer {self.llm_config.api_key}",
                "Content-Type": "application/json"
            }

            base_url = self.llm_config.base_url or self._get_default_base_url(self.llm_config.provider)

            payload = {
                "model": self.llm_config.model,
                "messages": self.conversation_history[-10:],  # 保持上下文
                "temperature": 0.7,
                "max_tokens": 2000
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )

                result = response.json()
                assistant_msg = result["choices"][0]["message"]["content"]
                self.conversation_history.append({"role": "assistant", "content": assistant_msg})

                return assistant_msg

        except Exception as e:
            return f"抱歉，与 AI 通信出错: {e}"

    async def _generate_configuration(self) -> bool:
        """生成最终配置"""
        console.print("\n[bold cyan]正在生成配置...[/bold cyan]\n")

        generate_prompt = """基于以上对话，请生成完整的 columns.yaml 配置。

要求:
1. 先总结用户的需求
2. 解释你的配置逻辑
3. 生成有效的 YAML 配置代码

配置结构:
```yaml
columns:
  - id: "headlines"
    name: "🔥 今日头条"
    description: "..."
    enabled: true
    max_items: 5
    order: 1
    sources:
      - type: "rss" | "api" | "bilibili" | etc.
        name: "显示名称"
        url: "RSS URL"
        weight: 1.0
        filter:
          keywords: ["关键词"]
    organization:
      sort_by: "relevance" | "time" | "mixed"
      dedup_strategy: "semantic" | "exact" | "none"
      summarize: "3_points" | "1_sentence" | "paragraph" | "none"
```

请生成配置:"""

        config_response = await self._chat_with_llm(generate_prompt)

        # 提取 YAML 代码块
        yaml_content = self._extract_yaml(config_response)

        if not yaml_content:
            console.print("[red]✗ 未能从 AI 响应中提取有效配置[/red]")
            console.print("AI 响应:")
            console.print(config_response)
            return False

        # 显示配置
        console.print("\n[bold]生成的配置预览:[/bold]\n")
        console.print(Syntax(yaml_content, "yaml", theme="monokai"))

        # 保存配置
        if Confirm.ask("\n是否保存此配置?", default=True):
            config_path = self.config_dir / "columns.yaml"

            # 备份旧配置
            if config_path.exists():
                backup_path = self.config_dir / "columns.yaml.backup"
                backup_path.write_text(config_path.read_text(), encoding="utf-8")
                console.print(f"[dim]已备份原配置到 {backup_path}[/dim]")

            # 保存新配置
            config_path.write_text(yaml_content, encoding="utf-8")
            console.print(f"[green]✓ 配置已保存到 {config_path}[/green]")

            # 同时保存 .env
            await self._save_env()

            return True

        return False

    def _extract_yaml(self, text: str) -> Optional[str]:
        """从文本中提取 YAML 代码块"""
        import re

        # 匹配 ```yaml ... ``` 或 ``` ... ```
        patterns = [
            r"```yaml\n(.*?)```",
            r"```yml\n(.*?)```",
            r"```\n(.*?)```",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # 如果没有代码块，尝试提取看起来像是 YAML 的部分
        if "columns:" in text:
            start = text.find("columns:")
            return text[start:].strip()

        return None

    async def _save_env(self):
        """保存 LLM 配置到 .env"""
        env_path = Path(__file__).parent.parent / ".env"

        env_content = f"""
# LLM 配置（由专家模式生成）
LLM_PROVIDER={self.llm_config.provider}
LLM_API_KEY={self.llm_config.api_key}
LLM_MODEL={self.llm_config.model}
"""

        if self.llm_config.base_url:
            env_content += f'LLM_BASE_URL={self.llm_config.base_url}\n'

        # 兼容旧配置
        if self.llm_config.provider == "openai":
            env_content += f"""
OPENAI_API_KEY={self.llm_config.api_key}
OPENAI_MODEL={self.llm_config.model}
"""
            if self.llm_config.base_url:
                env_content += f'OPENAI_BASE_URL={self.llm_config.base_url}\n'

        if env_path.exists():
            # 追加到现有文件
            with open(env_path, "a", encoding="utf-8") as f:
                f.write(env_content)
        else:
            env_path.write_text(env_content.strip(), encoding="utf-8")

        console.print(f"[green]✓ LLM 配置已保存到 {env_path}[/green]")


# CLI 入口
async def run_expert_setup():
    """运行专家配置模式"""
    setup = LLMAssistedSetup()
    return await setup.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_expert_setup())
