"""
插件系统基础模块
支持自定义采集器、处理器、推送渠道
"""
import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: str  # collector, processor, publisher
    enabled: bool = True
    config: Dict = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class BasePlugin(ABC):
    """插件基类"""
    
    # 插件元数据（子类必须定义）
    NAME: str = ""
    VERSION: str = "1.0.0"
    DESCRIPTION: str = ""
    AUTHOR: str = ""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self):
        """初始化插件"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """关闭插件"""
        pass
    
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return PluginInfo(
            name=self.NAME,
            version=self.VERSION,
            description=self.DESCRIPTION,
            author=self.AUTHOR,
            plugin_type=self.get_plugin_type(),
            enabled=True,
            config=self.config
        )
    
    @abstractmethod
    def get_plugin_type(self) -> str:
        """获取插件类型"""
        pass


class CollectorPlugin(BasePlugin):
    """采集器插件基类"""
    
    def get_plugin_type(self) -> str:
        return "collector"
    
    @abstractmethod
    async def collect(self) -> List[Dict]:
        """
        执行采集
        
        Returns:
            内容列表
        """
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        pass


class ProcessorPlugin(BasePlugin):
    """处理器插件基类"""
    
    def get_plugin_type(self) -> str:
        return "processor"
    
    @abstractmethod
    async def process(self, content: Dict) -> Dict:
        """
        处理内容
        
        Args:
            content: 内容字典
            
        Returns:
            处理后的内容
        """
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        pass


class PublisherPlugin(BasePlugin):
    """推送渠道插件基类"""
    
    def get_plugin_type(self) -> str:
        return "publisher"
    
    @abstractmethod
    async def publish(self, report: Any) -> bool:
        """
        推送日报
        
        Args:
            report: 日报对象
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        pass


class PluginManager:
    """插件管理器"""
    
    PLUGIN_DIR = "plugins"
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_infos: Dict[str, PluginInfo] = {}
        self._loaders = {
            "collector": self._load_collector_plugin,
            "processor": self._load_processor_plugin,
            "publisher": self._load_publisher_plugin
        }
    
    def _ensure_plugin_dir(self):
        """确保插件目录存在"""
        plugin_path = Path(self.PLUGIN_DIR)
        if not plugin_path.exists():
            plugin_path.mkdir(parents=True)
            
            # 创建 __init__.py
            (plugin_path / "__init__.py").touch()
            
            # 创建示例插件
            self._create_example_plugin()
    
    def _create_example_plugin(self):
        """创建示例插件"""
        example_code = '''"""
示例采集器插件
展示如何创建自定义采集器
"""
from src.plugin_system import CollectorPlugin


class ExampleCollectorPlugin(CollectorPlugin):
    """示例采集器 - 演示如何创建自定义采集器"""
    
    NAME = "example_collector"
    VERSION = "1.0.0"
    DESCRIPTION = "示例采集器插件"
    AUTHOR = "Your Name"
    
    async def initialize(self):
        """初始化"""
        print(f"[{self.NAME}] 初始化")
        self._initialized = True
    
    async def shutdown(self):
        """关闭"""
        print(f"[{self.NAME}] 关闭")
    
    async def collect(self):
        """
        采集内容
        
        返回内容列表，每个内容是一个字典
        """
        # 这里实现你的采集逻辑
        # 可以调用 API、解析网页等
        
        return [
            {
                "title": "示例内容标题",
                "url": "https://example.com/article/1",
                "source": "Example Source",
                "content": "内容正文...",
                "summary": "内容摘要..."
            }
        ]
    
    def get_default_config(self):
        """默认配置"""
        return {
            "api_key": "",
            "base_url": "https://api.example.com",
            "limit": 10
        }
'''
        example_path = Path(self.PLUGIN_DIR) / "example_collector.py"
        with open(example_path, "w", encoding="utf-8") as f:
            f.write(example_code)
    
    def discover_plugins(self) -> List[PluginInfo]:
        """发现并列出所有可用插件"""
        self._ensure_plugin_dir()
        
        plugins = []
        plugin_path = Path(self.PLUGIN_DIR)
        
        # 扫描插件目录
        for file_path in plugin_path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            try:
                # 动态导入模块
                module_name = f"{self.PLUGIN_DIR}.{file_path.stem}"
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                else:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                
                # 查找插件类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BasePlugin) and 
                        obj is not BasePlugin and
                        obj is not CollectorPlugin and
                        obj is not ProcessorPlugin and
                        obj is not PublisherPlugin and
                        hasattr(obj, 'NAME') and obj.NAME):
                        
                        # 创建实例获取信息
                        instance = obj()
                        info = instance.get_info()
                        plugins.append(info)
            
            except Exception as e:
                print(f"加载插件失败 {file_path}: {e}")
        
        return plugins
    
    def load_plugin(self, plugin_name: str, config: Dict = None) -> Optional[BasePlugin]:
        """加载并初始化插件"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        
        plugin_path = Path(self.PLUGIN_DIR) / f"{plugin_name}.py"
        if not plugin_path.exists():
            print(f"插件不存在: {plugin_name}")
            return None
        
        try:
            # 动态导入
            module_name = f"{self.PLUGIN_DIR}.{plugin_name}"
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj is not BasePlugin and
                    hasattr(obj, 'NAME') and 
                    obj.NAME == plugin_name):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                print(f"在 {plugin_name} 中未找到插件类")
                return None
            
            # 创建实例
            plugin = plugin_class(config)
            
            # 存储
            self.plugins[plugin_name] = plugin
            self.plugin_infos[plugin_name] = plugin.get_info()
            
            return plugin
        
        except Exception as e:
            print(f"加载插件失败 {plugin_name}: {e}")
            return None
    
    async def initialize_plugin(self, plugin_name: str) -> bool:
        """初始化插件"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False
        
        try:
            await plugin.initialize()
            return True
        except Exception as e:
            print(f"初始化插件失败 {plugin_name}: {e}")
            return False
    
    async def shutdown_all(self):
        """关闭所有插件"""
        for name, plugin in self.plugins.items():
            try:
                await plugin.shutdown()
            except Exception as e:
                print(f"关闭插件失败 {name}: {e}")
        
        self.plugins.clear()
        self.plugin_infos.clear()
    
    def get_loaded_plugins(self) -> List[PluginInfo]:
        """获取已加载的插件列表"""
        return [info for info in self.plugin_infos.values()]
    
    def _load_collector_plugin(self, plugin: CollectorPlugin):
        """加载采集器插件"""
        # 这里应该将插件注册到采集器管理器
        from src.collector import CollectorManager
        # TODO: 实现注册逻辑
        print(f"注册采集器插件: {plugin.NAME}")
    
    def _load_processor_plugin(self, plugin: ProcessorPlugin):
        """加载处理器插件"""
        # 这里应该将插件注册到处理器链
        print(f"注册处理器插件: {plugin.NAME}")
    
    def _load_publisher_plugin(self, plugin: PublisherPlugin):
        """加载推送插件"""
        # 这里应该将插件注册到推送渠道
        print(f"注册推送插件: {plugin.NAME}")
    
    def get_plugin_template(self, plugin_type: str) -> str:
        """获取插件模板代码"""
        if plugin_type == "collector":
            return '''"""
自定义采集器插件
"""
from src.plugin_system import CollectorPlugin


class MyCollectorPlugin(CollectorPlugin):
    """我的采集器"""
    
    NAME = "my_collector"
    VERSION = "1.0.0"
    DESCRIPTION = "我的自定义采集器"
    AUTHOR = "Your Name"
    
    async def initialize(self):
        """初始化"""
        self.api_key = self.config.get("api_key")
        self.base_url = self.config.get("base_url")
    
    async def shutdown(self):
        """关闭"""
        pass
    
    async def collect(self):
        """采集内容"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # 调用 API 或爬取网页
            response = await client.get(f"{self.base_url}/api/data")
            data = response.json()
            
            # 转换为标准格式
            items = []
            for item in data:
                items.append({
                    "title": item["title"],
                    "url": item["url"],
                    "source": "My Source",
                    "content": item.get("content", ""),
                    "summary": item.get("summary", "")
                })
            
            return items
    
    def get_default_config(self):
        return {
            "api_key": "",
            "base_url": "https://api.example.com"
        }
'''
        elif plugin_type == "processor":
            return '''"""
自定义处理器插件
"""
from src.plugin_system import ProcessorPlugin


class MyProcessorPlugin(ProcessorPlugin):
    """我的内容处理器"""
    
    NAME = "my_processor"
    VERSION = "1.0.0"
    DESCRIPTION = "我的自定义内容处理器"
    AUTHOR = "Your Name"
    
    async def initialize(self):
        pass
    
    async def shutdown(self):
        pass
    
    async def process(self, content):
        """处理内容"""
        # 自定义处理逻辑
        # 例如：翻译、关键词提取、情感分析等
        
        content["processed"] = True
        content["keywords"] = self._extract_keywords(content.get("content", ""))
        
        return content
    
    def _extract_keywords(self, text: str) -> list:
        """提取关键词"""
        # 实现关键词提取
        return []
    
    def get_default_config(self):
        return {}
'''
        elif plugin_type == "publisher":
            return '''"""
自定义推送渠道插件
"""
from src.plugin_system import PublisherPlugin


class MyPublisherPlugin(PublisherPlugin):
    """我的推送渠道"""
    
    NAME = "my_publisher"
    VERSION = "1.0.0"
    DESCRIPTION = "我的自定义推送渠道"
    AUTHOR = "Your Name"
    
    async def initialize(self):
        self.webhook_url = self.config.get("webhook_url")
    
    async def shutdown(self):
        pass
    
    async def publish(self, report):
        """推送日报"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.webhook_url,
                json={
                    "title": report.title,
                    "content": report.content,
                    "date": report.date.isoformat()
                }
            )
            
            return response.status_code == 200
    
    def get_default_config(self):
        return {
            "webhook_url": ""
        }
'''
        else:
            return ""


# 全局插件管理器
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取插件管理器"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


# CLI 命令函数
def cli_list_plugins():
    """CLI: 列出插件"""
    manager = get_plugin_manager()
    plugins = manager.discover_plugins()
    
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    if not plugins:
        console.print("[yellow]未发现插件[/yellow]")
        console.print(f"\n插件目录: {manager.PLUGIN_DIR}/")
        console.print("使用 `python -m src.cli plugin create <name> --type collector` 创建新插件")
        return
    
    table = Table(title="已发现插件")
    table.add_column("名称", style="cyan")
    table.add_column("类型", style="green")
    table.add_column("版本")
    table.add_column("描述")
    table.add_column("作者")
    
    for plugin in plugins:
        table.add_row(
            plugin.name,
            plugin.plugin_type,
            plugin.version,
            plugin.description[:30],
            plugin.author
        )
    
    console.print(table)


def cli_create_plugin(name: str, plugin_type: str):
    """CLI: 创建插件模板"""
    manager = get_plugin_manager()
    manager._ensure_plugin_dir()
    
    template = manager.get_plugin_template(plugin_type)
    if not template:
        print(f"未知插件类型: {plugin_type}")
        return
    
    # 替换模板中的类名
    class_name = "".join(word.capitalize() for word in name.split("_"))
    template = template.replace("MyCollector", class_name)
    template = template.replace("MyProcessor", class_name)
    template = template.replace("MyPublisher", class_name)
    template = template.replace("my_collector", name)
    template = template.replace("my_processor", name)
    template = template.replace("my_publisher", name)
    
    # 写入文件
    file_path = Path(manager.PLUGIN_DIR) / f"{name}.py"
    
    if file_path.exists():
        print(f"插件已存在: {file_path}")
        return
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template)
    
    print(f"✅ 插件已创建: {file_path}")
    print(f"\n编辑文件实现你的逻辑，然后使用:")
    print(f"  python -m src.cli plugin load {name}")
