"""
模板推荐器模块
根据用户输入智能推荐配置模板
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass
class TemplateScore:
    """模板评分"""
    template_id: str
    name: str
    score: float  # 0-1
    matched_keywords: List[str]
    description: str


class TemplateRecommender:
    """模板推荐器"""
    
    # 模板关键词映射
    TEMPLATE_KEYWORDS = {
        "tech_developer": {
            "name": "👨‍💻 技术开发者",
            "keywords": [
                "技术", "编程", "代码", "开发", "developer", "programming",
                "开源", "github", "ai", "人工智能", "大模型", "llm",
                "python", "javascript", "java", "golang", "rust",
                "架构", "系统", "后端", "前端", "全栈", "算法",
                "云计算", "云原生", "devops", "容器", "k8s", "kubernetes"
            ],
            "description": "专注技术趋势、开源项目、编程实践",
        },
        "product_manager": {
            "name": "💼 产品经理",
            "keywords": [
                "产品", "产品经理", "pm", "product", "设计",
                "用户", "用户体验", "ux", "ui", "交互设计",
                "增长", "运营", "数据分析", "数据驱动",
                "需求", "敏捷", "scrum", "项目管理",
                "商业模式", "竞品分析", "市场调研"
            ],
            "description": "关注产品设计、用户增长、行业动态",
        },
        "investor": {
            "name": "💰 投资人",
            "keywords": [
                "投资", "vc", "pe", "创投", "融资", "startup",
                "创业", "估值", "股权", "并购", "ipo",
                "市场", "行业研究", "财报", "财务", "经济",
                "趋势", "宏观", "策略", "基金", "资产配置"
            ],
            "description": "关注市场趋势、创业公司、财报数据",
        },
        "business_analyst": {
            "name": "📊 商业分析师",
            "keywords": [
                "商业", "咨询", "分析", "战略", "规划",
                "行业研究", "市场分析", "竞争分析", "benchmark",
                "数据", "商业智能", "bi", "报告", "洞察",
                "咨询", "麦肯锡", "bcg", "贝恩", "四大"
            ],
            "description": "关注行业研究、市场数据、竞争分析",
        },
        "designer": {
            "name": "🎨 设计师",
            "keywords": [
                "设计", "design", "ui", "ux", "界面", "视觉",
                "创意", "灵感", "艺术", "美学", "配色",
                "figma", "sketch", "adobe", "ps", "ai",
                "品牌", "营销", "广告", "插画", "动画"
            ],
            "description": "关注设计趋势、创意灵感、设计工具",
        },
        "ai_researcher": {
            "name": "🧠 AI 研究员",
            "keywords": [
                "ai", "人工智能", "机器学习", "深度学习", "神经网络",
                "论文", "研究", "学术", "顶会", "neurips", "icml", "cvpr",
                "大模型", "llm", "nlp", "cv", "计算机视觉", "自然语言处理",
                "强化学习", "rl", "多模态", "生成式ai", "gpt", "transformer"
            ],
            "description": "专注 AI 研究、学术论文、前沿技术",
        },
        "frontend_dev": {
            "name": "🌐 前端开发者",
            "keywords": [
                "前端", "frontend", "web", "react", "vue", "angular",
                "javascript", "typescript", "html", "css", "nodejs",
                "ui组件", "响应式", "性能优化", "webpack", "vite",
                "小程序", "移动端", "h5", "pwa", "ssr"
            ],
            "description": "专注前端技术、框架动态、UI组件",
        },
        "backend_dev": {
            "name": "⚙️ 后端开发者",
            "keywords": [
                "后端", "backend", "服务器", "api", "数据库",
                "微服务", "分布式", "高并发", "性能", "架构",
                "redis", "mysql", "postgresql", "mongodb", "elasticsearch",
                "消息队列", "kafka", "rabbitmq", "grpc", "rest"
            ],
            "description": "专注后端架构、数据库、分布式系统",
        },
        "data_engineer": {
            "name": "📈 数据工程师",
            "keywords": [
                "数据", "data", "etl", "数据仓库", "数据湖", "大数据",
                "hadoop", "spark", "flink", "kafka", "实时计算",
                "sql", "python", "pandas", "数据管道", "数据治理",
                "bi", "报表", "可视化", "tableau", "powerbi"
            ],
            "description": "专注数据处理、数据管道、数据架构",
        },
        "security_engineer": {
            "name": "🔒 安全工程师",
            "keywords": [
                "安全", "security", "网络安全", "信息安全", "攻防",
                "渗透测试", "漏洞", "ctf", "加密", "密码学",
                "防火墙", "ids", "ips", "soc", "siem",
                "合规", "等保", "gdpr", "隐私保护", "零信任"
            ],
            "description": "关注网络安全、攻防技术、安全合规",
        },
        "entrepreneur": {
            "name": "🚀 创业者",
            "keywords": [
                "创业", "startup", "创始人", "ceo", "cto",
                "融资", "vc", "天使投资", "路演", "bp",
                "商业模式", "mvp", "增长黑客", "产品市场匹配", "pmf",
                "管理", "团队", "企业文化", "领导力", "决策"
            ],
            "description": "关注创业动态、融资信息、管理实践",
        },
        "general": {
            "name": "📰 综合资讯",
            "keywords": [
                "新闻", "资讯", "时事", "社会", "文化",
                "综合", "杂项", "兴趣广泛", "多方面"
            ],
            "description": "平衡的科技、商业、社会资讯",
        }
    }
    
    def __init__(self):
        self.templates = self.TEMPLATE_KEYWORDS
    
    def recommend(self, user_input: str, top_k: int = 3) -> List[TemplateScore]:
        """
        根据用户输入推荐模板
        
        Args:
            user_input: 用户输入的关键词（空格分隔）
            top_k: 返回前 k 个推荐
            
        Returns:
            模板评分列表
        """
        user_keywords = [kw.strip().lower() for kw in user_input.split()]
        
        scores = []
        for template_id, info in self.templates.items():
            template_keywords = [k.lower() for k in info["keywords"]]
            
            # 计算匹配
            matched = []
            score = 0.0
            
            for user_kw in user_keywords:
                # 完全匹配
                if user_kw in template_keywords:
                    matched.append(user_kw)
                    score += 1.0
                else:
                    # 部分匹配
                    for template_kw in template_keywords:
                        if user_kw in template_kw or template_kw in user_kw:
                            matched.append(user_kw)
                            score += 0.5
                            break
            
            # 归一化分数
            if user_keywords:
                score = score / len(user_keywords)
            
            if score > 0:
                scores.append(TemplateScore(
                    template_id=template_id,
                    name=info["name"],
                    score=score,
                    matched_keywords=list(set(matched)),
                    description=info["description"]
                ))
        
        # 按分数排序
        scores.sort(key=lambda x: x.score, reverse=True)
        
        return scores[:top_k]
    
    def get_template_by_id(self, template_id: str) -> Dict:
        """获取模板信息"""
        return self.templates.get(template_id, self.templates["general"])
    
    def interactive_recommend(self) -> str:
        """
        交互式推荐
        
        Returns:
            用户选择的模板 ID
        """
        from rich.prompt import Prompt
        
        console.print("\n[bold cyan]🎯 智能模板推荐[/bold cyan]")
        console.print("告诉我们你关注哪些话题，我们会为你推荐最合适的配置\n")
        
        # 获取用户输入
        user_input = Prompt.ask(
            "📝 输入你关注的关键词（空格分隔）",
            default="科技 编程"
        )
        
        if not user_input or user_input.strip() == "":
            user_input = "科技 编程"
        
        # 获取推荐
        recommendations = self.recommend(user_input)
        
        if not recommendations:
            console.print("\n[yellow]未找到匹配模板，使用默认模板[/yellow]")
            return "general"
        
        # 显示推荐
        console.print("\n[bold]✨ 根据你的兴趣，推荐以下模板：[/bold]\n")
        
        for i, rec in enumerate(recommendations, 1):
            match_pct = int(rec.score * 100)
            match_color = "green" if match_pct >= 80 else "yellow" if match_pct >= 50 else "white"
            
            panel_content = (
                f"{rec.description}\n"
                f"\n[dim]匹配度: [{match_color}]{match_pct}%[/{match_color}]"
            )
            if rec.matched_keywords:
                panel_content += f" | 匹配: {', '.join(rec.matched_keywords[:3])}"
            panel_content += "[/dim]"
            
            console.print(Panel(
                panel_content,
                title=f"[{i}] {rec.name}",
                border_style="green" if i == 1 else "yellow" if i == 2 else "white"
            ))
        
        # 其他选项
        console.print(f"[{len(recommendations) + 1}] 浏览所有模板")
        console.print(f"[{len(recommendations) + 2}] 自定义配置\n")
        
        # 获取选择
        choices = [str(i) for i in range(1, len(recommendations) + 3)]
        choice = Prompt.ask("请选择", choices=choices, default="1")
        
        choice_idx = int(choice) - 1
        
        if choice_idx < len(recommendations):
            selected = recommendations[choice_idx]
            console.print(f"\n[green]✅ 已选择: {selected.name}[/green]")
            return selected.template_id
        elif choice_idx == len(recommendations):
            # 浏览所有
            return self._show_all_templates()
        else:
            # 自定义
            return "custom"
    
    def _show_all_templates(self) -> str:
        """显示所有模板供选择"""
        from rich.prompt import IntPrompt
        
        console.print("\n[bold]所有可用模板：[/bold]\n")
        
        templates_list = list(self.templates.items())
        
        for i, (template_id, info) in enumerate(templates_list, 1):
            console.print(f"  [{i}] {info['name']}")
            console.print(f"      [dim]{info['description']}[/dim]\n")
        
        choice = IntPrompt.ask(
            "请选择",
            choices=[str(i) for i in range(1, len(templates_list) + 1)],
            default=1
        )
        
        selected_id = templates_list[choice - 1][0]
        console.print(f"\n[green]✅ 已选择: {self.templates[selected_id]['name']}[/green]")
        
        return selected_id


# 便捷函数
def recommend_template(user_input: str = "") -> str:
    """
    根据输入推荐模板
    
    Args:
        user_input: 用户输入的关键词
        
    Returns:
        推荐的模板 ID
    """
    recommender = TemplateRecommender()
    
    if not user_input:
        return recommender.interactive_recommend()
    
    recommendations = recommender.recommend(user_input)
    
    if recommendations:
        return recommendations[0].template_id
    
    return "general"


if __name__ == "__main__":
    # 测试
    recommender = TemplateRecommender()
    template_id = recommender.interactive_recommend()
    print(f"\n最终选择: {template_id}")
