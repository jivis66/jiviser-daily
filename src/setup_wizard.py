"""
启动设置向导模块
提供交互式用户画像、兴趣偏好、日报内容配置
"""
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

console = Console()


# ============ 预设模板 ============

@dataclass
class UserProfileTemplate:
    """用户画像模板"""
    name: str
    description: str
    industry: str
    position: str
    expertise: List[str]
    experience_level: str = "mid"
    company_size: str = "mid"
    daily_time_minutes: int = 20


@dataclass
class InterestTemplate:
    """兴趣偏好模板"""
    name: str
    description: str
    core_topics: List[Dict[str, float]]
    content_types: List[str]
    source_preferences: Dict[str, float]
    language_preference: str = "zh_first"
    content_depth: str = "medium"
    novelty_preference: str = "balanced"


@dataclass
class DailyReportTemplate:
    """日报模板"""
    name: str
    description: str
    style: str
    columns: List[Dict]
    min_quality_score: int = 60
    time_window_hours: int = 24
    dedup_level: str = "medium"
    summary_method: str = "rule"


# 预设模板库
PROFILE_TEMPLATES = {
    "tech_developer": UserProfileTemplate(
        name="👨‍💻 技术开发者",
        description="专注技术趋势、开源项目、编程实践",
        industry="互联网/科技",
        position="技术开发者",
        expertise=["软件开发", "开源技术", "系统架构"],
        experience_level="senior",
        daily_time_minutes=20
    ),
    "product_manager": UserProfileTemplate(
        name="💼 产品经理",
        description="关注产品设计、用户增长、行业动态",
        industry="互联网/科技",
        position="产品经理",
        expertise=["产品设计", "用户研究", "数据分析"],
        experience_level="senior",
        daily_time_minutes=20
    ),
    "investor": UserProfileTemplate(
        name="💰 投资人",
        description="关注市场趋势、创业公司、财报数据",
        industry="金融/投资",
        position="投资人/分析师",
        expertise=["投资分析", "市场研究", "财务分析"],
        experience_level="expert",
        daily_time_minutes=30
    ),
    "business_analyst": UserProfileTemplate(
        name="📊 商业分析师",
        description="关注行业研究、市场数据、竞争分析",
        industry="咨询/商业分析",
        position="商业分析师",
        expertise=["行业研究", "数据分析", "战略规划"],
        experience_level="senior",
        daily_time_minutes=25
    ),
    "designer": UserProfileTemplate(
        name="🎨 设计师",
        description="关注设计趋势、创意灵感、设计工具",
        industry="互联网/科技",
        position="设计师",
        expertise=["UI/UX设计", "创意设计", "设计工具"],
        experience_level="mid",
        daily_time_minutes=15
    ),
    "general": UserProfileTemplate(
        name="📰 综合资讯",
        description="平衡的科技、商业、社会资讯",
        industry="其他",
        position="其他",
        expertise=[],
        experience_level="mid",
        daily_time_minutes=15
    )
}

INTEREST_TEMPLATES = {
    "tech_developer": InterestTemplate(
        name="👨‍💻 技术开发者",
        description="专注技术趋势、开源项目、编程实践",
        core_topics=[
            {"name": "人工智能", "weight": 1.0},
            {"name": "大语言模型", "weight": 0.95},
            {"name": "开源项目", "weight": 0.9},
            {"name": "编程语言", "weight": 0.85},
            {"name": "云原生", "weight": 0.8},
        ],
        content_types=["tutorial", "news", "analysis"],
        source_preferences={"media": 0.7, "community": 0.95, "social": 0.8, "academic": 0.6},
        language_preference="zh_first",
        content_depth="deep",
        novelty_preference="balanced"
    ),
    "product_manager": InterestTemplate(
        name="💼 产品经理",
        description="关注产品设计、用户增长、行业动态",
        core_topics=[
            {"name": "产品设计", "weight": 1.0},
            {"name": "用户增长", "weight": 0.9},
            {"name": "用户体验", "weight": 0.9},
            {"name": "商业模式", "weight": 0.8},
            {"name": "AI应用", "weight": 0.85},
        ],
        content_types=["analysis", "product_review", "news"],
        source_preferences={"media": 0.9, "community": 0.7, "social": 0.8, "academic": 0.4},
        language_preference="zh_first",
        content_depth="medium",
        novelty_preference="trending"
    ),
    "investor": InterestTemplate(
        name="💰 投资人",
        description="关注市场趋势、创业公司、财报数据",
        core_topics=[
            {"name": "创业公司", "weight": 1.0},
            {"name": "投融资", "weight": 0.95},
            {"name": "市场趋势", "weight": 0.9},
            {"name": "财报分析", "weight": 0.85},
            {"name": "宏观经济", "weight": 0.7},
        ],
        content_types=["news", "analysis"],
        source_preferences={"media": 0.95, "community": 0.6, "social": 0.7, "academic": 0.5},
        language_preference="zh_first",
        content_depth="medium",
        novelty_preference="trending"
    ),
    "general": InterestTemplate(
        name="📰 综合资讯",
        description="平衡的科技、商业、社会资讯",
        core_topics=[
            {"name": "科技", "weight": 0.8},
            {"name": "商业", "weight": 0.8},
            {"name": "社会", "weight": 0.6},
            {"name": "文化", "weight": 0.5},
        ],
        content_types=["news", "analysis"],
        source_preferences={"media": 0.8, "community": 0.5, "social": 0.6, "academic": 0.3},
        language_preference="zh_first",
        content_depth="medium",
        novelty_preference="balanced"
    )
}

DAILY_REPORT_TEMPLATES = {
    "tech_developer": DailyReportTemplate(
        name="👨‍💻 技术开发者",
        description="GitHub趋势、技术新闻、开发工具",
        style="detailed",
        columns=[
            {"id": "github", "name": "🔥 GitHub 趋势", "enabled": True, "max_items": 5, "order": 1},
            {"id": "ai_tech", "name": "🤖 AI/技术", "enabled": True, "max_items": 5, "order": 2},
            {"id": "dev_tools", "name": "🛠️ 开发工具", "enabled": True, "max_items": 3, "order": 3},
            {"id": "tech_news", "name": "📰 科技新闻", "enabled": True, "max_items": 3, "order": 4},
        ],
        min_quality_score=65,
        time_window_hours=24,
        dedup_level="medium",
        summary_method="llm"
    ),
    "product_manager": DailyReportTemplate(
        name="💼 产品经理",
        description="产品动态、用户增长、行业分析",
        style="brief",
        columns=[
            {"id": "headlines", "name": "🔥 今日头条", "enabled": True, "max_items": 3, "order": 1},
            {"id": "product_hunt", "name": "🚀 Product Hunt", "enabled": True, "max_items": 5, "order": 2},
            {"id": "ai_apps", "name": "🤖 AI应用", "enabled": True, "max_items": 4, "order": 3},
            {"id": "business", "name": "💰 商业动态", "enabled": True, "max_items": 3, "order": 4},
        ],
        min_quality_score=60,
        time_window_hours=24,
        dedup_level="medium",
        summary_method="rule"
    ),
    "investor": DailyReportTemplate(
        name="💰 投资人",
        description="市场动态、融资信息、财报速递",
        style="data",
        columns=[
            {"id": "market", "name": "📈 市场动态", "enabled": True, "max_items": 5, "order": 1},
            {"id": "funding", "name": "💰 融资信息", "enabled": True, "max_items": 5, "order": 2},
            {"id": "earnings", "name": "📊 财报速递", "enabled": True, "max_items": 3, "order": 3},
            {"id": "analysis", "name": "🔍 深度分析", "enabled": True, "max_items": 3, "order": 4},
        ],
        min_quality_score=70,
        time_window_hours=24,
        dedup_level="high",
        summary_method="llm"
    ),
    "general": DailyReportTemplate(
        name="📰 综合资讯",
        description="平衡的科技、商业、社会资讯",
        style="brief",
        columns=[
            {"id": "headlines", "name": "🔥 今日头条", "enabled": True, "max_items": 5, "order": 1},
            {"id": "tech", "name": "💻 科技", "enabled": True, "max_items": 4, "order": 2},
            {"id": "business", "name": "💼 商业", "enabled": True, "max_items": 3, "order": 3},
            {"id": "lifestyle", "name": "🌟 生活方式", "enabled": True, "max_items": 3, "order": 4},
        ],
        min_quality_score=55,
        time_window_hours=24,
        dedup_level="low",
        summary_method="rule"
    )
}


# ============ 设置向导 ============

class SetupWizard:
    """启动设置向导"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.profile_config = {}
        self.interest_config = {}
        self.daily_config = {}
    
    async def run_full_setup(self):
        """运行完整设置向导"""
        self._print_welcome()
        
        # 步骤 1: 用户画像
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]👤 步骤 1/4: 用户画像设置[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        self.profile_config = await self._setup_profile()
        
        # 步骤 2: 兴趣偏好
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]🎯 步骤 2/4: 兴趣偏好配置[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        self.interest_config = await self._setup_interests()
        
        # 步骤 3: LLM 配置
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]🤖 步骤 3/4: LLM 配置（可选）[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        await self._setup_llm()
        
        # 步骤 4: 日报内容
        console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print("[bold blue]📰 步骤 4/4: 日报内容定制[/bold blue]")
        console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
        self.daily_config = await self._setup_daily_report()
        
        # 保存配置
        await self._save_config()
        
        # 完成
        self._print_completion()
    
    def _print_welcome(self):
        """打印欢迎信息"""
        console.print(Panel(
            "[bold green]🎉 欢迎使用 Daily Agent 个性化日报系统[/bold green]\n\n"
            "这是一个交互式设置向导，将帮助您完成初始配置。\n"
            "整个过程大约需要 [cyan]3-5 分钟[/cyan]。\n\n"
            "[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
            "[bold]📋 设置步骤概览[/bold]\n"
            "[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
            "  1. 👤 用户画像设置 (约 1 分钟)\n"
            "  2. 🎯 兴趣偏好配置 (约 2 分钟)\n"
            "  3. 🤖 LLM 配置 (约 1 分钟)\n"
            "  4. 📰 日报内容定制 (约 1 分钟)\n\n",
            title="启动设置向导",
            border_style="green"
        ))
        
        Prompt.ask("按 Enter 开始设置", default="")
    
    async def _setup_profile(self) -> dict:
        """设置用户画像"""
        console.print("这些基础信息将帮助我为您筛选更相关的内容。\n")
        
        # 选择配置方式
        use_template = Confirm.ask(
            "📝 是否使用预设模板快速配置？",
            default=True
        )
        
        if use_template:
            return await self._setup_profile_from_template()
        else:
            return await self._setup_profile_custom()
    
    async def _setup_profile_from_template(self) -> dict:
        """从模板设置用户画像"""
        console.print("\n[bold]📝 选择预设模板：[/bold]\n")
        
        templates = list(PROFILE_TEMPLATES.items())
        for i, (key, template) in enumerate(templates, 1):
            console.print(f"   [{i}] {template.name}")
            console.print(f"       [dim]{template.description}[/dim]\n")
        
        choice = IntPrompt.ask(
            "请选择",
            choices=[str(i) for i in range(1, len(templates) + 1)],
            default=1
        )
        
        selected_key = templates[choice - 1][0]
        template = templates[choice - 1][1]
        
        console.print(f"\n✅ 已选择模板: [green]{template.name}[/green]")
        
        # 允许微调
        customize = Confirm.ask(
            "\n📝 是否对模板进行微调？",
            default=False
        )
        
        if customize:
            return await self._customize_profile_template(template)
        
        return {
            "industry": template.industry,
            "position": template.position,
            "expertise": template.expertise,
            "experience_level": template.experience_level,
            "daily_time_minutes": template.daily_time_minutes
        }
    
    async def _setup_profile_custom(self) -> dict:
        """自定义设置用户画像"""
        config = {}
        
        # 行业
        industries = [
            "互联网/科技", "金融/投资", "咨询/商业分析", "媒体/内容创作",
            "学术研究", "医疗健康", "制造业", "教育/培训", "其他"
        ]
        console.print("\n[bold]📝 您当前从事的行业是？[/bold]")
        for i, ind in enumerate(industries, 1):
            console.print(f"   [{i}] {ind}")
        
        ind_choice = IntPrompt.ask("请选择", choices=[str(i) for i in range(1, 10)])
        config["industry"] = industries[ind_choice - 1]
        
        # 职位
        positions = [
            "技术开发者/工程师", "产品经理", "创业者/高管", "投资人/分析师",
            "设计师", "市场/运营", "学生", "自由职业者", "其他"
        ]
        console.print("\n[bold]📝 您的职位或角色是？[/bold]")
        for i, pos in enumerate(positions, 1):
            console.print(f"   [{i}] {pos}")
        
        pos_choice = IntPrompt.ask("请选择", choices=[str(i) for i in range(1, 10)])
        config["position"] = positions[pos_choice - 1]
        
        # 专业领域
        expertise_input = Prompt.ask(
            "\n[bold]📝 您的专业领域或技术栈是？[/bold]（空格分隔，例如: AI Python 产品设计）",
            default=""
        )
        config["expertise"] = [e.strip() for e in expertise_input.split() if e.strip()]
        
        # 阅读时间
        console.print("\n[bold]📝 您每天大约有多少时间阅读日报？[/bold]")
        console.print("   [1] 5-10 分钟（精简版）")
        console.print("   [2] 15-20 分钟（标准版）")
        console.print("   [3] 30 分钟以上（深度版）")
        
        time_choice = IntPrompt.ask("请选择", choices=["1", "2", "3"])
        config["daily_time_minutes"] = {1: 10, 2: 20, 3: 30}[time_choice]
        
        console.print(f"\n✅ 已记录专业领域: [green]{', '.join(config['expertise'])}[/green]")
        
        return config
    
    async def _customize_profile_template(self, template: UserProfileTemplate) -> dict:
        """微调模板"""
        config = {
            "industry": template.industry,
            "position": template.position,
            "expertise": template.expertise.copy(),
            "daily_time_minutes": template.daily_time_minutes
        }
        
        # 修改专业领域
        add_expertise = Prompt.ask(
            f"\n当前专业领域: {', '.join(config['expertise'])}\n"
            "是否添加其他领域？（空格分隔，直接回车跳过）",
            default=""
        )
        if add_expertise:
            config["expertise"].extend([e.strip() for e in add_expertise.split() if e.strip()])
        
        # 修改阅读时间
        change_time = Confirm.ask("是否修改阅读时间？", default=False)
        if change_time:
            console.print("   [1] 5-10 分钟（精简版）")
            console.print("   [2] 15-20 分钟（标准版）")
            console.print("   [3] 30 分钟以上（深度版）")
            time_choice = IntPrompt.ask("请选择", choices=["1", "2", "3"])
            config["daily_time_minutes"] = {1: 10, 2: 20, 3: 30}[time_choice]
        
        return config
    
    async def _setup_interests(self) -> dict:
        """设置兴趣偏好"""
        # 使用与用户画像相同的模板
        profile_template_name = None
        for key, template in PROFILE_TEMPLATES.items():
            if (template.industry == self.profile_config.get("industry") and
                template.position == self.profile_config.get("position")):
                profile_template_name = key
                break
        
        if not profile_template_name:
            profile_template_name = "general"
        
        interest_template = INTEREST_TEMPLATES.get(profile_template_name, INTEREST_TEMPLATES["general"])
        
        console.print(f"基于您的用户画像，已为您推荐 [green]{interest_template.name}[/green] 兴趣配置\n")
        
        # 显示推荐内容
        console.print("📋 推荐兴趣标签：")
        for topic in interest_template.core_topics:
            console.print(f"   • {topic['name']} (权重: {topic['weight']})")
        
        # 允许自定义
        customize = Confirm.ask(
            "\n📝 是否添加自定义兴趣标签？",
            default=False
        )
        
        core_topics = interest_template.core_topics.copy()
        
        if customize:
            custom_tags = Prompt.ask(
                "输入标签（空格分隔）",
                default=""
            )
            if custom_tags:
                for tag in custom_tags.split():
                    core_topics.append({"name": tag.strip(), "weight": 0.7})
        
        # 内容深度偏好
        console.print("\n[bold]📝 内容深度偏好：[/bold]")
        console.print("   [1] 轻松阅读 - 标题+简短摘要")
        console.print("   [2] 标准深度 - 详细摘要+关键要点")
        console.print("   [3] 深度阅读 - 完整分析+背景信息")
        
        depth_choice = IntPrompt.ask("请选择", choices=["1", "2", "3"], default=2)
        content_depth = {1: "light", 2: "medium", 3: "deep"}[depth_choice]
        
        return {
            "core_topics": core_topics,
            "content_types": interest_template.content_types,
            "source_preferences": interest_template.source_preferences,
            "language_preference": interest_template.language_preference,
            "content_depth": content_depth,
            "novelty_preference": interest_template.novelty_preference
        }
    
    async def _setup_llm(self):
        """设置 LLM 配置"""
        from src.llm_config import LLMSetupWizard as LLMWizard
        
        console.print("配置 LLM 可以让日报生成更智能的摘要和质量评估。\n")
        
        # 检查是否已有配置
        from src.llm_config import get_llm_manager
        manager = get_llm_manager()
        current_config = manager.get_current_config()
        
        if current_config.is_configured() and current_config.provider != "skip":
            console.print(f"[green]✓ 已配置 LLM: {current_config.provider} / {current_config.model}[/green]\n")
            reconfigure = Confirm.ask("是否重新配置 LLM？", default=False)
            if not reconfigure:
                console.print("[dim]保留现有配置，跳过此步骤[/dim]\n")
                return
        
        # 询问是否配置
        setup_llm = Confirm.ask("是否现在配置 LLM？", default=True)
        
        if setup_llm:
            wizard = LLMWizard()
            await wizard.run_setup()
        else:
            console.print("\n[yellow]⚠️ 已跳过 LLM 配置[/yellow]")
            console.print("[dim]系统将使用规则摘要（功能受限）[/dim]")
            console.print("[dim]稍后可通过 python -m src.cli llm setup 重新配置[/dim]\n")
    
    async def _setup_daily_report(self) -> dict:
        """设置日报内容"""
        # 使用相同的模板
        profile_template_name = None
        for key, template in PROFILE_TEMPLATES.items():
            if (template.industry == self.profile_config.get("industry") and
                template.position == self.profile_config.get("position")):
                profile_template_name = key
                break
        
        if not profile_template_name:
            profile_template_name = "general"
        
        daily_template = DAILY_REPORT_TEMPLATES.get(profile_template_name, DAILY_REPORT_TEMPLATES["general"])
        
        console.print(f"基于您的偏好，已为您配置 [green]{daily_template.name}[/green] 日报\n")
        
        # 日报风格
        console.print("[bold]📝 日报风格：[/bold]")
        styles = [
            ("brief", "📰 新闻简报型", "标题+摘要，快速浏览"),
            ("detailed", "📖 深度阅读型", "详细摘要+关键要点"),
            ("chat", "💬 对话简报型", "聊天式摘要，适合移动端"),
            ("data", "📊 数据驱动型", "图表+数据，适合分析师")
        ]
        
        for i, (key, name, desc) in enumerate(styles, 1):
            marker = "✓" if key == daily_template.style else " "
            console.print(f"   [{marker}] [{i}] {name} - {desc}")
        
        style_choice = IntPrompt.ask(
            "请选择",
            choices=[str(i) for i in range(1, 5)],
            default={"brief": 1, "detailed": 2, "chat": 3, "data": 4}.get(daily_template.style, 2)
        )
        selected_style = styles[style_choice - 1][0]
        
        # 分栏设置
        console.print("\n[bold]📝 日报分栏设置：[/bold]\n")
        
        columns = []
        for col in daily_template.columns:
            enabled = Confirm.ask(f"   [x] {col['name']}", default=col['enabled'])
            if enabled:
                max_items = IntPrompt.ask(
                    f"       条数",
                    default=col['max_items']
                )
                columns.append({
                    "id": col['id'],
                    "name": col['name'],
                    "enabled": True,
                    "max_items": max_items,
                    "order": col['order']
                })
        
        # 质量筛选
        console.print("\n[bold]📝 内容筛选规则：[/bold]")
        min_quality = IntPrompt.ask(
            "   最低质量分数 (0-100, 越高越精选)",
            default=daily_template.min_quality_score
        )
        
        # 摘要方式
        from src.config import get_settings
        settings = get_settings()
        has_llm = bool(settings.openai_api_key)
        
        if has_llm:
            console.print("\n[bold]📝 摘要生成：[/bold]")
            console.print("   [1] 规则摘要 - 快速、稳定")
            console.print("   [2] LLM摘要 - 高质量、需要API Key")
            summary_choice = IntPrompt.ask("请选择", choices=["1", "2"], default=2)
            summary_method = "rule" if summary_choice == 1 else "llm"
        else:
            console.print("\n[yellow]⚠️ 未检测到 OPENAI_API_KEY，将使用规则摘要[/yellow]")
            summary_method = "rule"
        
        return {
            "style": selected_style,
            "columns": columns,
            "filter_rules": {
                "min_quality_score": min_quality,
                "time_window_hours": daily_template.time_window_hours,
                "dedup_level": daily_template.dedup_level
            },
            "summary": {
                "method": summary_method,
                "length": "medium",
                "include_key_points": True
            }
        }
    
    async def _save_config(self):
        """保存配置到数据库"""
        from src.database import UserProfileDB, get_session
        
        async with get_session() as session:
            # 查询或创建用户画像
            from sqlalchemy import select
            from src.database import Base
            
            result = await session.execute(
                select(UserProfileDB).where(UserProfileDB.user_id == self.user_id)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                profile = UserProfileDB(user_id=self.user_id)
                session.add(profile)
            
            # 更新用户画像
            profile.industry = self.profile_config.get("industry")
            profile.position = self.profile_config.get("position")
            profile.expertise = json.dumps(self.profile_config.get("expertise", []), ensure_ascii=False)
            
            # 更新兴趣偏好
            profile.interests = json.dumps(self.interest_config.get("core_topics", []), ensure_ascii=False)
            
            # 更新阅读偏好
            profile.reading_time = f"{self.profile_config.get('daily_time_minutes', 20)}min"
            profile.summary_style = self.daily_config.get("summary", {}).get("method", "rule")
            profile.content_depth = self.interest_config.get("content_depth", "medium")
            
            await session.flush()
        
        # 保存日报配置到文件
        await self._save_daily_config()
        
        console.print("\n[green]✅ 配置已保存[/green]")
    
    async def _save_daily_config(self):
        """保存日报配置到 YAML 文件"""
        import os
        
        from ruamel.yaml import YAML
        
        config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        config_path = os.path.join(config_dir, "daily_report.yaml")
        
        config = {
            "user_id": self.user_id,
            "style": self.daily_config.get("style", "brief"),
            "columns": self.daily_config.get("columns", []),
            "filter_rules": self.daily_config.get("filter_rules", {}),
            "summary": self.daily_config.get("summary", {})
        }
        
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.allow_unicode = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
    
    def _print_completion(self):
        """打印完成信息"""
        console.print(Panel(
            "[bold green]🎉 设置完成！[/bold green]\n\n"
            "您的个性化日报配置已保存。\n\n"
            "[bold]接下来您可以：[/bold]\n"
            "  • 运行 [cyan]python -m src.cli collect[/cyan] 手动触发采集\n"
            "  • 运行 [cyan]python -m src.cli generate[/cyan] 生成日报\n"
            "  • 访问 [cyan]http://localhost:8080/docs[/cyan] 查看 API 文档\n\n"
            "[dim]其他命令：[/dim]\n"
            "  • [cyan]python -m src.cli llm setup[/cyan] - 配置 LLM\n"
            "  • [cyan]python -m src.cli auth list[/cyan] - 管理认证渠道\n\n"
            "[dim]如需重新配置，运行: python -m src.cli quickstart[/dim]",
            title="设置向导",
            border_style="green"
        ))


# ============ 配置导入导出 ============

async def export_config(user_id: str = "default", format: str = "yaml", output: str = None) -> str:
    """
    导出用户配置
    
    Args:
        user_id: 用户ID
        format: 格式 (yaml/json)
        output: 输出文件路径
        
    Returns:
        输出文件路径
    """
    from src.database import UserProfileDB, get_session
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(UserProfileDB).where(UserProfileDB.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError(f"未找到用户 {user_id} 的配置")
        
        config = {
            "user_id": user_id,
            "profile": {
                "industry": profile.industry,
                "position": profile.position,
                "expertise": json.loads(profile.expertise or "[]"),
                "interests": json.loads(profile.interests or "[]"),
            },
            "preferences": {
                "reading_time": profile.reading_time,
                "summary_style": profile.summary_style,
                "content_depth": profile.content_depth,
                "push_time": profile.push_time,
                "timezone": profile.timezone,
            }
        }
    
    # 确定输出路径
    if not output:
        output = f"daily-agent-config-{user_id}.{format}"
    
    # 写入文件
    if format == "json":
        with open(output, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    else:  # yaml
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.allow_unicode = True
        with open(output, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
    
    return output


async def import_config(filepath: str, user_id: str = "default", overwrite: bool = False) -> bool:
    """
    导入用户配置
    
    Args:
        filepath: 配置文件路径
        user_id: 用户ID
        overwrite: 是否覆盖现有配置
        
    Returns:
        是否成功
    """
    import os
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"配置文件不存在: {filepath}")
    
    # 读取配置
    if filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:  # yaml
        from ruamel.yaml import YAML
        yaml = YAML()
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.load(f)
    
    # 导入到数据库
    from src.database import UserProfileDB, get_session
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(UserProfileDB).where(UserProfileDB.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile and not overwrite:
            return False
        
        if not profile:
            profile = UserProfileDB(user_id=user_id)
            session.add(profile)
        
        profile_data = config.get("profile", {})
        profile.industry = profile_data.get("industry")
        profile.position = profile_data.get("position")
        profile.expertise = json.dumps(profile_data.get("expertise", []), ensure_ascii=False)
        profile.interests = json.dumps(profile_data.get("interests", []), ensure_ascii=False)
        
        pref_data = config.get("preferences", {})
        profile.reading_time = pref_data.get("reading_time", "20min")
        profile.summary_style = pref_data.get("summary_style", "rule")
        profile.content_depth = pref_data.get("content_depth", "medium")
        profile.push_time = pref_data.get("push_time", "09:00")
        profile.timezone = pref_data.get("timezone", "Asia/Shanghai")
        
        await session.flush()
    
    return True


async def get_user_config(user_id: str = "default") -> dict:
    """
    获取用户配置
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户配置字典
    """
    from src.database import UserProfileDB, get_session
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(UserProfileDB).where(UserProfileDB.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError(f"未找到用户 {user_id} 的配置")
        
        return {
            "user_id": user_id,
            "profile": {
                "industry": profile.industry,
                "position": profile.position,
                "expertise": json.loads(profile.expertise or "[]"),
                "interests": json.loads(profile.interests or "[]"),
            },
            "preferences": {
                "reading_time": profile.reading_time,
                "summary_style": profile.summary_style,
                "content_depth": profile.content_depth,
                "push_time": profile.push_time,
                "timezone": profile.timezone,
                "push_channels": profile.push_channels.split(",") if profile.push_channels else [],
            }
        }


async def apply_template(template_key: str, user_id: str = "default") -> bool:
    """
    应用预设模板到用户配置
    
    Args:
        template_key: 模板ID
        user_id: 用户ID
        
    Returns:
        是否成功
    """
    if template_key not in PROFILE_TEMPLATES:
        return False
    
    profile_template = PROFILE_TEMPLATES[template_key]
    interest_template = INTEREST_TEMPLATES.get(template_key, INTEREST_TEMPLATES["general"])
    daily_template = DAILY_REPORT_TEMPLATES.get(template_key, DAILY_REPORT_TEMPLATES["general"])
    
    # 保存到数据库
    from src.database import UserProfileDB, get_session
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(UserProfileDB).where(UserProfileDB.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = UserProfileDB(user_id=user_id)
            session.add(profile)
        
        # 应用模板配置
        profile.industry = profile_template.industry
        profile.position = profile_template.position
        profile.expertise = json.dumps(profile_template.expertise, ensure_ascii=False)
        profile.interests = json.dumps([t["name"] for t in interest_template.core_topics], ensure_ascii=False)
        profile.reading_time = f"{profile_template.daily_time_minutes}min"
        profile.summary_style = daily_template.summary_method
        profile.content_depth = interest_template.content_depth
        
        await session.flush()
    
    return True
