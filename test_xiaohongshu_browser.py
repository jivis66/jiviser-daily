#!/usr/bin/env python3
"""
使用浏览器测试小红书内容获取
更可靠的方式，通过真实浏览器访问
"""
import asyncio
import json
import sys

sys.path.insert(0, '.')


async def test_xiaohongshu_with_browser():
    """使用浏览器测试小红书内容获取"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("请先安装 Playwright: pip install playwright")
        print("然后安装浏览器: python -m playwright install chromium")
        return
    
    print("=" * 60)
    print("小红书浏览器采集测试")
    print("=" * 60)
    
    async with async_playwright() as p:
        # 启动浏览器
        print("\n[1] 启动浏览器...")
        browser = None
        
        # 尝试使用系统 Chrome
        import os
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chrome.app/Contents/MacOS/Chrome",
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    browser = await p.chromium.launch(
                        headless=False,
                        executable_path=chrome_path
                    )
                    print("   ✓ 使用系统 Chrome")
                    break
                except:
                    pass
        
        if not browser:
            try:
                browser = await p.chromium.launch(headless=False)
                print("   ✓ 使用 Playwright Chromium")
            except Exception as e:
                print(f"   ✗ 启动失败: {e}")
                return
        
        # 创建上下文
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        # 访问小红书
        print("\n[2] 打开小红书...")
        await page.goto("https://www.xiaohongshu.com")
        
        print("\n[3] 请登录小红书（如未登录）")
        print("   - 扫码登录或密码登录")
        print("   - 登录成功后返回终端按 Enter")
        input("\n登录完成请按 Enter...")
        
        # 测试 1: 获取推荐内容
        print("\n[4] 测试获取推荐内容...")
        await page.goto("https://www.xiaohongshu.com/explore")
        await asyncio.sleep(3)  # 等待加载
        
        # 提取页面中的笔记数据
        notes = await page.evaluate("""() => {
            // 尝试从 window.__INITIAL_STATE__ 获取数据
            const state = window.__INITIAL_STATE__;
            if (state && state.explore && state.explore.notes) {
                return state.explore.notes.slice(0, 5);
            }
            // 或者从 DOM 中提取
            const cards = document.querySelectorAll('.note-item, .feeds-page .note-card');
            return Array.from(cards).slice(0, 5).map(card => {
                const title = card.querySelector('.title, .note-title')?.textContent || '';
                const author = card.querySelector('.author, .user-name')?.textContent || '';
                const link = card.querySelector('a')?.href || '';
                return { title, author, link };
            });
        }""")
        
        if notes and len(notes) > 0:
            print(f"   ✓ 获取到 {len(notes)} 条内容")
            print("\n   内容预览:")
            for i, note in enumerate(notes[:3], 1):
                title = note.get('title', '') or note.get('noteCard', {}).get('title', '无标题')
                author = note.get('user', {}).get('nickname', note.get('author', '未知'))
                print(f"   [{i}] {title[:40]}... (by {author})")
        else:
            print("   ✗ 未获取到内容")
        
        # 测试 2: 搜索功能
        print("\n[5] 测试搜索功能...")
        keyword = "AI"
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"
        await page.goto(search_url)
        await asyncio.sleep(3)
        
        search_results = await page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            if (state && state.search && state.search.notes) {
                return state.search.notes.slice(0, 5);
            }
            return [];
        }""")
        
        if search_results and len(search_results) > 0:
            print(f"   ✓ 搜索 '{keyword}' 获取到 {len(search_results)} 条结果")
            for i, note in enumerate(search_results[:3], 1):
                title = note.get('title', '') or note.get('noteCard', {}).get('title', '无标题')
                print(f"   [{i}] {title[:40]}...")
        else:
            print(f"   ✗ 搜索未返回结果（可能需要等待页面加载或检查关键词）")
        
        # 测试 3: API 直接访问
        print("\n[6] 测试 API 直接访问...")
        
        # 获取当前 cookie
        cookies = await context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        print(f"   Cookie 数量: {len(cookies)}")
        print(f"   关键 Cookie: {', '.join([c for c in cookie_dict.keys() if c in ['web_session', 'a1', 'xsecappid']])}")
        
        # 使用 fetch 在页面中调用 API
        api_result = await page.evaluate("""async () => {
            try {
                const response = await fetch('https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo', {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json, text/plain, */*',
                        'Referer': 'https://www.xiaohongshu.com/'
                    },
                    credentials: 'include'
                });
                return {
                    status: response.status,
                    data: await response.json()
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        
        if api_result.get('status') == 200:
            data = api_result.get('data', {})
            if data.get('success'):
                user = data.get('data', {})
                print(f"   ✓ API 访问成功")
                print(f"   - 用户: {user.get('nickname')}")
                print(f"   - ID: {user.get('user_id')}")
            else:
                print(f"   API 返回: {data.get('msg', '未知错误')}")
        else:
            print(f"   API 状态: {api_result.get('status', '失败')}")
            if api_result.get('error'):
                print(f"   错误: {api_result['error']}")
        
        await browser.close()
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        print("\n说明:")
        print("- 浏览器模式可以绕过大部分反爬机制")
        print("- 获取的 Cookie 可用于其他 API 调用")
        print("- 建议定期更新 Cookie 以保持有效性")


async def export_cookies_for_api():
    """导出 Cookie 供 API 使用"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright 未安装")
        return
    
    print("=" * 60)
    print("导出小红书 Cookie")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://www.xiaohongshu.com")
        
        print("\n请登录小红书...")
        input("登录完成请按 Enter...")
        
        # 获取所有 cookie
        cookies = await context.cookies()
        
        print(f"\n获取到 {len(cookies)} 个 Cookie:\n")
        
        cookie_dict = {}
        for cookie in cookies:
            name = cookie['name']
            value = cookie['value']
            cookie_dict[name] = value
            # 只显示部分关键 cookie
            if name in ['web_session', 'a1', 'xsecappid', 'gid', 'webId']:
                print(f"  {name} = {value[:50]}{'...' if len(value) > 50 else ''}")
        
        # 构建 curl 命令
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        print("\n" + "-" * 60)
        print("cURL 命令示例:")
        print("-" * 60)
        print(f"""curl 'https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo' \\
  -H 'Accept: application/json, text/plain, */*' \\
  -H 'Referer: https://www.xiaohongshu.com/' \\
  -H 'Cookie: {cookie_str[:100]}...'""")
        
        # 保存到文件
        output = {
            'cookies': cookie_dict,
            'cookie_string': cookie_str,
            'export_time': str(asyncio.get_event_loop().time()),
        }
        
        with open('xiaohongshu_cookies.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Cookie 已保存到 xiaohongshu_cookies.json")
        
        await browser.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='小红书浏览器测试工具')
    parser.add_argument('command', choices=['test', 'export'], 
                       default='test', nargs='?',
                       help='test: 测试采集, export: 导出 Cookie')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        asyncio.run(test_xiaohongshu_with_browser())
    elif args.command == 'export':
        asyncio.run(export_cookies_for_api())
