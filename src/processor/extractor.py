"""
信息提取模块
负责实体识别、关键词提取等
"""
import re
from collections import Counter
from typing import List, Set

import jieba
from sklearn.feature_extraction.text import TfidfVectorizer

from src.models import ContentItem


class KeywordExtractor:
    """关键词提取器"""
    
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
    
    def extract(self, item: ContentItem, top_k: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            item: 内容条目
            top_k: 返回关键词数量
            
        Returns:
            List[str]: 关键词列表
        """
        text = f"{item.title} {item.content or ''}"
        if not text:
            return []
        
        # 合并已有的关键词
        existing = set(item.keywords)
        
        # 使用 TF-IDF 提取
        tfidf_keywords = self._extract_tfidf(text, top_k)
        
        # 使用正则提取可能的术语（大写字母组合、技术术语等）
        pattern_keywords = self._extract_patterns(text)
        
        # 合并去重
        all_keywords = list(existing) + tfidf_keywords + pattern_keywords
        
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
    
    def _extract_tfidf(self, text: str, top_k: int) -> List[str]:
        """使用 TF-IDF 提取关键词"""
        try:
            # 简单分词
            words = self._tokenize(text)
            
            if len(words) < 5:
                return words[:top_k]
            
            # 使用简单的词频统计代替 TF-IDF（单文档场景）
            word_freq = Counter(w for w in words if w.lower() not in self.STOP_WORDS and len(w) > 1)
            return [word for word, _ in word_freq.most_common(top_k)]
            
        except Exception:
            return []
    
    def _extract_patterns(self, text: str) -> List[str]:
        """提取模式匹配的关键词"""
        keywords = []
        
        # 匹配技术术语（如 Python, JavaScript, AI, GPT-4 等）
        tech_patterns = [
            r"\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b",  # CamelCase
            r"\b[A-Z]{2,}\b",  # 大写缩写
            r"\bGPT-[0-9.]+\b",  # GPT-4, GPT-3.5
            r"\b[A-Za-z]+\.js\b",  # xxx.js
            r"\b[A-Za-z]+\.py\b",  # xxx.py
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        return keywords
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 检测语言
        if self._is_chinese(text):
            # 中文分词
            return list(jieba.cut(text))
        else:
            # 英文分词
            return re.findall(r"\b[a-zA-Z]+\b", text)
    
    def _is_chinese(self, text: str) -> bool:
        """检测是否包含中文"""
        return bool(re.search(r"[\u4e00-\u9fff]", text))


class EntityExtractor:
    """实体提取器"""
    
    # 简单的实体模式
    PATTERNS = {
        "company": [
            r"\b(Google|Microsoft|Apple|Amazon|Meta|OpenAI|Anthropic|NVIDIA|Intel|AMD)\b",
            r"\b(字节跳动|腾讯|阿里巴巴|百度|华为|小米|美团|京东|滴滴|拼多多)\b",
            r"\b(ByteDance|Tencent|Alibaba|Baidu|Huawei|Xiaomi)\b",
        ],
        "person": [
            r"\b(Elon Musk|Bill Gates|Mark Zuckerberg|Sundar Pichai|Satya Nadella|Tim Cook)\b",
            r"\b(马斯克|扎克伯格|贝索斯|马云|马化腾|李彦宏|雷军)\b",
        ],
        "technology": [
            r"\b(AI|人工智能|机器学习|深度学习|LLM|大模型|GPT|ChatGPT|Claude)\b",
            r"\b(区块链|Blockchain|Web3|云计算|Cloud|物联网|IoT|5G|6G)\b",
        ]
    }
    
    def extract(self, item: ContentItem) -> List[str]:
        """
        提取实体
        
        Args:
            item: 内容条目
            
        Returns:
            List[str]: 实体列表
        """
        text = f"{item.title} {item.content or ''}"
        entities = set()
        
        # 模式匹配提取
        for entity_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities.update(matches)
        
        # 合并已有的实体
        entities.update(item.entities)
        
        return list(entities)
    
    def extract_companies(self, text: str) -> List[str]:
        """提取公司名"""
        companies = []
        for pattern in self.PATTERNS["company"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            companies.extend(matches)
        return companies
    
    def extract_technologies(self, text: str) -> List[str]:
        """提取技术术语"""
        techs = []
        for pattern in self.PATTERNS["technology"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            techs.extend(matches)
        return techs


class TopicClassifier:
    """主题分类器（基于关键词）"""
    
    TOPICS = {
        "人工智能": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "GPT", "LLM", "大模型"],
        "编程开发": ["编程", "代码", "开发", "Python", "JavaScript", "Java", "GitHub", "开源"],
        "科技产品": ["产品", "发布", "新品", "iPhone", "手机", "电脑", "芯片", "硬件"],
        "互联网": ["互联网", "平台", "App", "应用", "网站", "用户", "流量"],
        "商业财经": ["融资", "上市", "投资", "财报", "营收", "利润", "市场", "股价"],
        "创业": ["创业", "初创", "startup", "创始人", "CEO", "VC", "天使轮"],
        "区块链": ["区块链", "Web3", "加密货币", "比特币", "以太坊", "NFT", "DeFi"],
        "云计算": ["云", "AWS", "Azure", "服务器", "容器", "Kubernetes", "Docker"],
        "安全": ["安全", "黑客", "漏洞", "攻击", "隐私", "加密", "数据泄露"],
    }
    
    def classify(self, item: ContentItem, top_k: int = 3) -> List[str]:
        """
        分类主题
        
        Args:
            item: 内容条目
            top_k: 返回主题数量
            
        Returns:
            List[str]: 主题列表
        """
        text = f"{item.title} {' '.join(item.keywords)} {item.content or ''}".lower()
        
        scores = {}
        for topic, keywords in self.TOPICS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > 0:
                scores[topic] = score
        
        # 排序返回
        sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics[:top_k]]
