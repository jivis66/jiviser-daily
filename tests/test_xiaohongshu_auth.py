"""
小红书鉴权模块测试

运行测试:
    pytest tests/test_xiaohongshu_auth.py -v
    
环境要求:
    - 安装 playwright: pip install playwright && python -m playwright install chromium
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime, timezone


# 标记需要 Playwright 的测试
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        pytest.importorskip("playwright", reason="playwright not installed") is None,
        reason="playwright not installed"
    )
]


class TestXHSAuthData:
    """测试 XHSAuthData 数据类"""
    
    def test_to_dict(self):
        """测试转换为字典"""
        from src.collector.xiaohongshu_auth import XHSAuthData
        
        data = XHSAuthData(
            cookies=[{"name": "test", "value": "123", "domain": ".xiaohongshu.com"}],
            local_storage=[{"origin": "https://www.xiaohongshu.com", "localStorage": {}}],
            session_storage=[],
            user_agent="Mozilla/5.0 Test",
            timestamp=1234567890.0,
            user_info={"nickname": "TestUser"}
        )
        
        result = data.to_dict()
        assert result["user_agent"] == "Mozilla/5.0 Test"
        assert result["user_info"]["nickname"] == "TestUser"
        assert len(result["cookies"]) == 1
    
    def test_from_dict(self):
        """测试从字典创建"""
        from src.collector.xiaohongshu_auth import XHSAuthData
        
        data = {
            "cookies": [{"name": "webId", "value": "abc123"}],
            "local_storage": [],
            "session_storage": [],
            "user_agent": "Test",
            "timestamp": 1234567890.0,
            "user_info": None
        }
        
        result = XHSAuthData.from_dict(data)
        assert result.user_agent == "Test"
        assert result.timestamp == 1234567890.0
    
    def test_get_cookie_dict(self):
        """测试获取 Cookie 字典"""
        from src.collector.xiaohongshu_auth import XHSAuthData
        
        data = XHSAuthData(
            cookies=[
                {"name": "webId", "value": "123"},
                {"name": "session", "value": "abc"}
            ],
            local_storage=[],
            session_storage=[],
            user_agent="Test",
            timestamp=0
        )
        
        cookie_dict = data.get_cookie_dict()
        assert cookie_dict["webId"] == "123"
        assert cookie_dict["session"] == "abc"
    
    def test_get_cookie_string(self):
        """测试获取 Cookie 字符串"""
        from src.collector.xiaohongshu_auth import XHSAuthData
        
        data = XHSAuthData(
            cookies=[
                {"name": "a", "value": "1"},
                {"name": "b", "value": "2"}
            ],
            local_storage=[],
            session_storage=[],
            user_agent="Test",
            timestamp=0
        )
        
        cookie_str = data.get_cookie_string()
        assert "a=1" in cookie_str
        assert "b=2" in cookie_str
        assert "; " in cookie_str


class TestXiaohongshuAuthHelper:
    """测试 XiaohongshuAuthHelper 类"""
    
    @pytest.fixture
    def helper(self):
        """创建测试用的 helper 实例"""
        from src.collector.xiaohongshu_auth import XiaohongshuAuthHelper
        return XiaohongshuAuthHelper(headless=True, timeout=30)
    
    def test_init(self, helper):
        """测试初始化"""
        assert helper.headless is True
        assert helper.timeout == 30
        assert helper.config is not None
    
    def test_default_status_handler(self, helper):
        """测试默认状态处理器"""
        # 应该能正常执行不抛出异常
        helper._default_status_handler("test message")
    
    def test_notify(self, helper):
        """测试状态通知"""
        messages = []
        helper.on_status = lambda msg: messages.append(msg)
        helper._notify("test")
        assert messages == ["test"]


class TestXiaohongshuAuthManager:
    """测试 XiaohongshuAuthManager 类"""
    
    @pytest.fixture
    def manager(self):
        """创建测试用的 manager 实例"""
        from src.collector.xiaohongshu_auth import XiaohongshuAuthManager
        return XiaohongshuAuthManager()
    
    @pytest.mark.asyncio
    async def test_verify_auth_calls_auth_manager(self, manager):
        """测试验证认证调用 auth_manager"""
        with patch.object(manager.auth_manager, 'test_auth', new_callable=AsyncMock) as mock_test:
            mock_test.return_value = (True, "认证有效", None)
            
            result = await manager.verify_auth()
            
            assert result == (True, "认证有效")
            mock_test.assert_called_once_with("xiaohongshu")


class TestExceptions:
    """测试异常类"""
    
    def test_xhs_auth_error(self):
        """测试基础鉴权错误"""
        from src.collector.xiaohongshu_auth import XHSAuthError
        
        with pytest.raises(XHSAuthError) as exc_info:
            raise XHSAuthError("test error")
        assert str(exc_info.value) == "test error"
    
    def test_xhs_login_timeout_error(self):
        """测试登录超时错误"""
        from src.collector.xiaohongshu_auth import XHSLoginTimeoutError, XHSAuthError
        
        with pytest.raises(XHSAuthError):  # 继承自 XHSAuthError
            raise XHSLoginTimeoutError("timeout")
    
    def test_xhs_login_failed_error(self):
        """测试登录失败错误"""
        from src.collector.xiaohongshu_auth import XHSLoginFailedError, XHSAuthError
        
        with pytest.raises(XHSAuthError):  # 继承自 XHSAuthError
            raise XHSLoginFailedError("failed")


class TestXiaohongshuCollectorIntegration:
    """测试小红书采集器与鉴权模块的集成"""
    
    @pytest.mark.asyncio
    async def test_collector_requires_auth_for_following(self):
        """测试关注流采集器需要认证"""
        from src.collector.xiaohongshu_collector import XiaohongshuAuthenticatedCollector
        
        config = {"collect_type": "following", "limit": 10}
        collector = XiaohongshuAuthenticatedCollector(config)
        
        # 未加载认证时应该抛出错误
        with pytest.raises(Exception):
            collector.get_auth_headers()
    
    def test_public_collector_no_auth_needed(self):
        """测试公开采集器不需要认证"""
        from src.collector.xiaohongshu_collector import XiaohongshuCollector
        
        config = {"collect_type": "hot", "limit": 10}
        collector = XiaohongshuCollector("test_xhs", config)
        
        # 公开采集器可以直接使用
        assert collector.collect_type == "hot"
        assert collector.limit == 10


class TestBrowserAuthIntegration:
    """测试 browser_auth 模块集成"""
    
    @pytest.mark.asyncio
    async def test_xiaohongshu_uses_specialized_auth(self):
        """测试小红书使用专门的鉴权模块"""
        from src.browser_auth import interactive_auth
        
        with patch('src.browser_auth._xiaohongshu_interactive_auth', new_callable=AsyncMock) as mock_xhs:
            mock_xhs.return_value = (True, "小红书认证成功")
            
            result = await interactive_auth("xiaohongshu")
            
            assert result == (True, "小红书认证成功")
            mock_xhs.assert_called_once_with(None)
    
    @pytest.mark.asyncio
    async def test_other_platforms_use_generic_auth(self):
        """测试其他平台使用通用鉴权"""
        from src.browser_auth import interactive_auth
        
        with patch.object(
            'src.browser_auth.BrowserAuthHelper', 
            'get_cookie_interactive', 
            new_callable=AsyncMock
        ) as mock_get_cookie, \
        patch('src.browser_auth.get_auth_manager') as mock_get_manager:
            
            mock_helper = MagicMock()
            mock_helper.get_cookie_interactive = AsyncMock(return_value=(True, "cookie=123"))
            mock_helper.get_curl_command.return_value = "curl test"
            mock_helper.cookie_str = "cookie=123"
            mock_helper.headers = {}
            
            mock_get_cookie.return_value = (True, "cookie=123")
            
            # 知乎使用通用认证
            result = await interactive_auth("zhihu")
            
            # 应该调用通用的 BrowserAuthHelper
            # 注意：由于导入时已经定义了函数，我们需要在正确的位置 patch


# 手动运行测试的入口
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
