"""
内容清洗模块
"""
import re
from html import unescape
from typing import Optional

from bs4 import BeautifulSoup


class ContentCleaner:
    """内容清洗器"""
    
    # 常见的广告/导航关键词
    NOISE_PATTERNS = [
        r"订阅.*公众号",
        r"关注.*微信",
        r"扫码.*关注",
        r"阅读原文",
        r"点击.*阅读",
        r"本文.*来源",
        r"作者.*简介",
        r"关于.*作者",
        r"版权声明",
        r"未经授权.*不得转载",
        r"投稿.*邮箱",
        r"合作.*联系",
        r"广告合作",
        r"商务合作",
        r"招聘.*信息",
        r"加入我们",
        r"相关阅读",
        r"推荐阅读",
        r"热门文章",
        r"延伸阅读",
        r"猜你喜欢",
        r"可能感兴趣",
        r"分享.*到",
        r"分享到.*",
        r"点赞.*收藏",
    ]
    
    def __init__(self):
        self.noise_regex = re.compile("|".join(self.NOISE_PATTERNS), re.IGNORECASE)
    
    def clean(self, html_content: str) -> str:
        """
        清洗 HTML 内容
        
        Args:
            html_content: 原始 HTML
            
        Returns:
            str: 清洗后的纯文本
        """
        if not html_content:
            return ""
        
        # 使用 BeautifulSoup 解析
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 移除脚本和样式
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        # 移除广告/导航元素
        self._remove_noise_elements(soup)
        
        # 获取文本
        text = soup.get_text(separator="\n")
        
        # 后处理
        text = self._post_process(text)
        
        return text
    
    def clean_markdown(self, text: str) -> str:
        """
        清洗 Markdown 文本
        
        Args:
            text: Markdown 文本
            
        Returns:
            str: 清洗后的文本
        """
        if not text:
            return ""
        
        # 移除 HTML 标签
        text = re.sub(r"<[^>]+>", "", text)
        
        # 移除 Markdown 链接，保留文本
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        
        # 移除图片
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
        
        # 移除格式标记
        text = re.sub(r"[*_`~#>]", "", text)
        
        # 移除噪声文本
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line and not self.noise_regex.search(line):
                lines.append(line)
        
        return "\n".join(lines)
    
    def _remove_noise_elements(self, soup: BeautifulSoup):
        """移除噪声元素"""
        # 根据 class/id 移除广告等元素
        noise_classes = [
            "ad", "ads", "advertisement", "sponsor",
            "share", "sharing", "social",
            "comment", "comments",
            "sidebar", "widget",
            "related", "recommendation",
            "newsletter", "subscribe"
        ]
        
        for elem in soup.find_all(class_=lambda x: x and any(nc in str(x).lower() for nc in noise_classes)):
            elem.decompose()
        
        for elem in soup.find_all(id=lambda x: x and any(nc in str(x).lower() for nc in noise_classes)):
            elem.decompose()
    
    def _post_process(self, text: str) -> str:
        """后处理文本"""
        # HTML 实体解码
        text = unescape(text)
        
        # 移除噪声行
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            # 跳过空行和噪声
            if not line:
                continue
            if self.noise_regex.search(line):
                continue
            # 跳过过短的行（可能是导航）
            if len(line) < 5 and not line.endswith("。"):
                continue
            lines.append(line)
        
        text = "\n\n".join(lines)
        
        # 规范化空白
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        
        # 移除特殊字符
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", text)
        
        return text.strip()
    
    def extract_main_content(self, html: str) -> str:
        """
        提取主要内容（使用启发式算法）
        
        Args:
            html: HTML 内容
            
        Returns:
            str: 主要内容
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 常见的内容容器
        content_selectors = [
            "article",
            "[role='main']",
            ".post-content",
            ".article-content",
            ".entry-content",
            ".content",
            "main",
            "#content",
            ".post",
            ".article"
        ]
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                return self.clean(str(elem))
        
        # 如果没有找到，返回全部内容
        return self.clean(html)
    
    def truncate(self, text: str, max_length: int = 1000, suffix: str = "...") -> str:
        """
        截断文本
        
        Args:
            text: 原文本
            max_length: 最大长度
            suffix: 后缀
            
        Returns:
            str: 截断后的文本
        """
        if len(text) <= max_length:
            return text
        
        # 在句子边界截断
        truncated = text[:max_length - len(suffix)]
        last_period = max(
            truncated.rfind("。"),
            truncated.rfind(". "),
            truncated.rfind("\n")
        )
        
        if last_period > max_length * 0.5:
            truncated = truncated[:last_period + 1]
        
        return truncated.strip() + suffix
