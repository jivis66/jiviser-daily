# 小红书交互式鉴权模块

小红书由于其严格的反爬机制，推荐使用浏览器自动登录方式获取和维持登录态。

## 功能特性

- 🔐 **交互式登录**：自动打开浏览器，支持扫码/手机号/验证码登录
- 🤖 **自动检测**：智能检测登录成功状态，无需手动确认
- 🛡️ **反检测**：注入反检测脚本，隐藏自动化特征
- 💾 **安全存储**：使用 Fernet 加密存储到数据库
- 🔄 **兼容现有系统**：与 `AuthManager` 无缝集成

## 快速开始

### 1. 使用 CLI 工具（推荐）

```bash
# 添加小红书认证（浏览器自动登录）
python -m src.cli auth add xiaohongshu -b

# 或使用手动方式
python -m src.cli auth add xiaohongshu -m
```

### 2. 直接运行模块

```bash
python -m src.collector.xiaohongshu_auth
```

### 3. 代码中使用

```python
import asyncio
from src.collector.xiaohongshu_auth import xhs_login_interactive

async def main():
    # 执行交互式登录
    success = await xhs_login_interactive(
        headless=False,  # 显示浏览器窗口
        timeout=300,     # 超时时间（秒）
        save_to_db=True  # 自动保存到数据库
    )
    
    if success:
        print("✅ 登录成功！")
    else:
        print("❌ 登录失败")

asyncio.run(main())
```

## API 参考

### XiaohongshuAuthHelper

底层认证助手类，提供浏览器自动化功能。

```python
from src.collector.xiaohongshu_auth import XiaohongshuAuthHelper

helper = XiaohongshuAuthHelper(
    headless=False,           # 是否无头模式
    timeout=300,              # 超时时间（秒）
    on_status=print          # 状态回调函数
)

# 执行交互式登录
auth_data = await helper.interactive_login()

# 关闭浏览器
await helper.close()
```

### XiaohongshuAuthManager

高级管理类，整合数据库操作。

```python
from src.collector.xiaohongshu_auth import XiaohongshuAuthManager

manager = XiaohongshuAuthManager()

# 执行登录
auth_data = await manager.login_interactive()

# 保存到数据库
success = await manager.save_to_database(auth_data)

# 验证现有认证
is_valid, message = await manager.verify_auth()

# 加载已保存的认证
auth_data = await manager.get_auth_data()
```

### XHSAuthData

鉴权数据类。

```python
from src.collector.xiaohongshu_auth import XHSAuthData

# 属性
auth_data.cookies           # Cookie 列表
auth_data.local_storage     # LocalStorage 数据
auth_data.user_agent        # User-Agent
auth_data.timestamp         # 时间戳
auth_data.user_info         # 用户信息（昵称等）

# 方法
auth_data.to_dict()         # 转换为字典
auth_data.get_cookie_dict() # 获取 Cookie 字典
auth_data.get_cookie_string() # 获取 Cookie 字符串
```

## 采集器使用

认证后，使用 `XiaohongshuAuthenticatedCollector` 采集关注流：

```python
from src.collector.xiaohongshu_collector import XiaohongshuAuthenticatedCollector

config = {
    "collect_type": "following",  # following, recommend
    "limit": 20
}

collector = XiaohongshuAuthenticatedCollector(config)
result = await collector.collect()

for item in result.items:
    print(f"- {item.title}")
```

## 反检测机制

本模块采用多种技术避免被检测为自动化工具：

1. **隐藏 webdriver 标记**：`navigator.webdriver = undefined`
2. **伪装 plugins**：模拟真实浏览器插件列表
3. **伪装 languages**：设置 `navigator.languages = ['zh-CN', 'zh', 'en']`
4. **伪造 chrome 对象**：模拟 Chrome 的 `chrome.runtime` API
5. **权限查询伪装**：修改 `navigator.permissions.query` 行为
6. **浏览器启动参数**：禁用自动化检测相关特性

## 异常处理

```python
from src.collector.xiaohongshu_auth import (
    XHSAuthError,
    XHSLoginTimeoutError,
    XHSLoginFailedError
)

try:
    auth_data = await helper.interactive_login()
except XHSLoginTimeoutError:
    print("登录超时，请重试")
except XHSLoginFailedError as e:
    print(f"登录失败: {e}")
except XHSAuthError as e:
    print(f"鉴权错误: {e}")
```

## 注意事项

1. **依赖要求**：需要安装 Playwright
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

2. **登录超时**：默认 5 分钟超时，可通过 `timeout` 参数调整

3. **Cookie 有效期**：小红书 Cookie 通常 7 天有效，过期后需要重新登录

4. **并发限制**：避免同时运行多个浏览器实例

5. **隐私模式**：浏览器数据仅在内存中，不会保存到本地磁盘

## 故障排除

### 浏览器启动失败

```bash
# 安装 Playwright 浏览器
python -m playwright install chromium

# 或安装系统 Chrome
# macOS: 下载 https://www.google.com/chrome/
# Linux: sudo apt-get install google-chrome-stable
```

### 登录被拦截

- 检查网络连接是否正常
- 尝试使用手机号登录代替扫码登录
- 确保小红书账号未被封禁

### Cookie 快速失效

- 避免在多个设备同时登录同一账号
- 减少频繁的 API 调用
- 使用认证采集器时注意请求频率

## 相关文件

- `src/collector/xiaohongshu_auth.py` - 鉴权模块
- `src/collector/xiaohongshu_collector.py` - 采集器
- `src/browser_auth.py` - 通用浏览器认证
- `src/auth_manager.py` - 认证管理器
