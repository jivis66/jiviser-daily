#!/usr/bin/env python3
"""
小红书采集器测试脚本
测试已配置认证的小红书信息获取能力
"""
import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '.')


async def test_xiaohongshu_collection():
    """测试小红书采集"""
    from src.collector.xiaohongshu_collector import XiaohongshuCollector
    from src.auth_manager import get_auth_manager
    
    print("=" * 60)
    print("小红书采集器测试")
    print("=" * 60)
    
    # 1. 检查认证配置
    print("\n[1] 检查认证配置...")
    manager = get_auth_manager()
    credentials = await manager.list_auth()
    
    xhs_creds = [c for c in credentials if c['source_name'] == 'xiaohongshu']
    if not xhs_creds:
        print("   ✗ 未找到小红书认证配置")
        print("   请先运行: python -m src.cli auth add xiaohongshu --browser")
        return False
    
    cred = xhs_creds[0]
    print(f"   ✓ 找到认证配置")
    print(f"   - 过期时间: {cred['expires_at']}")
    print(f"   - 状态: {'有效' if cred['is_valid'] else '已失效'}")
    
    # 2. 测试热门采集
    print("\n[2] 测试热门笔记采集...")
    
    # 创建带认证的采集器配置
    config = {
        "collect_type": "hot",
        "limit": 5,
        "use_auth": True,  # 启用认证
    }
    
    collector = XiaohongshuCollector("xiaohongshu_test", config)
    
    # 如果有认证，添加到 headers
    if xhs_creds:
        from src.database import get_session, AuthCredentialRepository
        async with get_session() as session:
            repo = AuthCredentialRepository(session)
            auth_data = await repo.get_by_source('xiaohongshu')
            if auth_data:
                import json
                headers = json.loads(auth_data.headers or '{}')
                collector._headers.update(headers)
                print("   ✓ 已加载认证信息到请求头")
    
    result = await collector.collect()
    
    print(f"   - 采集结果: {'成功' if result.success else '失败'}")
    print(f"   - 消息: {result.message}")
    print(f"   - 找到: {result.total_found} 条")
    print(f"   - 有效: {len(result.items)} 条")
    
    if result.items:
        print("\n[3] 采集到的内容预览:")
        print("-" * 60)
        for i, item in enumerate(result.items[:3], 1):
            print(f"\n[{i}] {item.title}")
            print(f"    作者: {item.author}")
            print(f"    链接: {item.url}")
            print(f"    关键词: {', '.join(item.keywords[:5])}")
            if item.extra:
                print(f"    互动: 👍{item.extra.get('likes', 0)} ⭐{item.extra.get('collects', 0)} 💬{item.extra.get('comments', 0)}")
    
    # 3. 测试搜索采集（如果有配置关键词）
    print("\n[4] 测试搜索采集 (关键词: AI)...")
    search_config = {
        "collect_type": "search",
        "keyword": "AI",
        "limit": 3,
    }
    
    search_collector = XiaohongshuCollector("xiaohongshu_search", search_config)
    # 同样添加认证
    if xhs_creds and auth_data:
        search_collector._headers.update(headers)
    
    search_result = await search_collector.collect()
    
    print(f"   - 采集结果: {'成功' if search_result.success else '失败'}")
    print(f"   - 消息: {search_result.message}")
    print(f"   - 找到: {search_result.total_found} 条")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return result.success


async def test_with_browser():
    """使用浏览器直接测试（更可靠）"""
    print("\n" + "=" * 60)
    print("使用浏览器测试小红书 API 访问")
    print("=" * 60)
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("请先安装 Playwright: pip install playwright")
        return False
    
    async with async_playwright() as p:
        # 尝试启动浏览器
        browser = None
        for channel in ['chrome', 'msedge', None]:
            try:
                if channel:
                    browser = await p.chromium.launch(channel=channel, headless=False)
                else:
                    browser = await p.chromium.launch(headless=False)
                break
            except:
                continue
        
        if not browser:
            print("无法启动浏览器")
            return False
        
        context = await browser.new_context()
        page = await context.new_page()
        
        print("\n1. 打开小红书...")
        await page.goto("https://www.xiaohongshu.com")
        
        # 等待登录或检查是否已登录
        print("2. 请确保已登录（如未登录请扫码登录）")
        print("3. 按 Enter 继续测试 API...")
        input()
        
        # 测试访问 API
        print("\n4. 测试访问小红书 API...")
        
        # 访问用户个人信息接口
        response = await page.goto("https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo")
        
        if response:
            status = response.status
            text = await response.text()
            print(f"   状态码: {status}")
            print(f"   响应长度: {len(text)}")
            
            if status == 200:
                try:
                    data = json.loads(text)
                    if data.get('success') or data.get('code') == 0:
                        user = data.get('data', {})
                        print(f"   ✓ API 访问成功")
                        print(f"   - 用户ID: {user.get('user_id')}")
                        print(f"   - 昵称: {user.get('nickname')}")
                    else:
                        print(f"   ✗ API 返回错误: {data.get('msg')}")
                except:
                    print(f"   响应内容: {text[:200]}")
            else:
                print(f"   ✗ 请求失败: HTTP {status}")
        
        await browser.close()
        return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='小红书采集器测试')
    parser.add_argument('--mode', choices=['collector', 'browser', 'both'], 
                       default='both', help='测试模式')
    
    args = parser.parse_args()
    
    if args.mode in ['collector', 'both']:
        print("\n" + "=" * 60)
        print("模式 1: 测试采集器")
        print("=" * 60)
        asyncio.run(test_xiaohongshu_collection())
    
    if args.mode in ['browser', 'both']:
        asyncio.run(test_with_browser())
