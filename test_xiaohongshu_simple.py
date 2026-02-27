#!/usr/bin/env python3
"""
小红书简单采集测试
直接使用浏览器访问页面提取数据
"""
import asyncio
import sys

sys.path.insert(0, '.')


async def collect_xiaohongshu_feed():
    """
    采集小红书推荐流
    使用 Playwright 模拟真实用户访问
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("请先安装 Playwright: pip install playwright")
        return
    
    print("=" * 60)
    print("小红书推荐流采集")
    print("=" * 60)
    
    async with async_playwright() as p:
        # 启动浏览器（可见模式，方便登录）
        print("\n[1] 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        # 访问小红书
        print("[2] 打开小红书...")
        await page.goto("https://www.xiaohongshu.com")
        
        # 检查是否需要登录
        print("\n[3] 请检查登录状态")
        print("   - 如果未登录，请扫码或密码登录")
        print("   - 登录后请按 Enter 继续")
        input()
        
        # 访问推荐页
        print("\n[4] 访问推荐流...")
        await page.goto("https://www.xiaohongshu.com/explore")
        await asyncio.sleep(3)  # 等待页面加载
        
        # 滚动加载更多内容
        print("[5] 加载更多内容...")
        for i in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            print(f"   滚动 {i+1}/3")
        
        # 提取笔记数据
        print("\n[6] 提取笔记数据...")
        
        notes = await page.evaluate("""() => {
            const results = [];
            
            // 方法1: 从 window.__INITIAL_STATE__ 获取
            const state = window.__INITIAL_STATE__;
            if (state && state.explore && state.explore.notes) {
                state.explore.notes.forEach(note => {
                    if (note.noteCard) {
                        results.push({
                            id: note.noteCard.id,
                            title: note.noteCard.title || '',
                            content: note.noteCard.desc || '',
                            author: note.noteCard.user?.nickname || '未知',
                            likes: note.noteCard.interactInfo?.likedCount || 0,
                            url: `https://www.xiaohongshu.com/explore/${note.noteCard.id}`,
                            cover: note.noteCard.cover?.url || ''
                        });
                    }
                });
            }
            
            // 方法2: 从 DOM 获取（如果方法1失败）
            if (results.length === 0) {
                document.querySelectorAll('section.note-item, div.feeds-page > div > div').forEach(el => {
                    const link = el.querySelector('a[href*="/explore/"]');
                    const titleEl = el.querySelector('.title, h3, .note-title');
                    const authorEl = el.querySelector('.author, .user-name');
                    
                    if (link && titleEl) {
                        const id = link.href.match(/\/explore\/(\w+)/)?.[1];
                        results.push({
                            id: id,
                            title: titleEl.textContent || '',
                            author: authorEl?.textContent || '未知',
                            url: link.href
                        });
                    }
                });
            }
            
            return results;
        }""")
        
        print(f"\n✓ 获取到 {len(notes)} 条笔记:\n")
        print("-" * 60)
        
        for i, note in enumerate(notes[:10], 1):
            print(f"\n[{i}] {note.get('title', '无标题')[:50]}")
            print(f"    作者: {note.get('author', '未知')}")
            print(f"    点赞: {note.get('likes', 'N/A')}")
            print(f"    链接: {note.get('url', '')}")
            if note.get('content'):
                content = note['content'][:100].replace('\n', ' ')
                print(f"    内容: {content}...")
        
        # 保存结果
        if notes:
            import json
            with open('xiaohongshu_notes.json', 'w', encoding='utf-8') as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)
            print(f"\n\n✓ 数据已保存到 xiaohongshu_notes.json")
        
        await browser.close()
        
        print("\n" + "=" * 60)
        print("采集完成")
        print("=" * 60)


async def search_xiaohongshu(keyword: str):
    """搜索小红书内容"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("请先安装 Playwright")
        return
    
    print(f"\n{'='*60}")
    print(f"小红书搜索: {keyword}")
    print(f"{'='*60}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 访问搜索页
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"
        await page.goto(search_url)
        
        print(f"\n正在搜索 '{keyword}'...")
        await asyncio.sleep(4)  # 等待搜索结果
        
        # 滚动加载
        for i in range(2):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        
        # 提取搜索结果
        results = await page.evaluate("""() => {
            const notes = [];
            const state = window.__INITIAL_STATE__;
            
            if (state && state.search && state.search.notes) {
                state.search.notes.forEach(note => {
                    if (note.noteCard) {
                        notes.push({
                            title: note.noteCard.title || '',
                            author: note.noteCard.user?.nickname || '未知',
                            likes: note.noteCard.interactInfo?.likedCount || 0,
                            url: `https://www.xiaohongshu.com/explore/${note.noteCard.id}`
                        });
                    }
                });
            }
            return notes;
        }""")
        
        print(f"\n✓ 找到 {len(results)} 条结果:\n")
        for i, note in enumerate(results[:8], 1):
            print(f"[{i}] {note.get('title', '无标题')[:40]}...")
            print(f"    作者: {note.get('author')} | 点赞: {note.get('likes', 0)}")
        
        await browser.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='小红书简单采集')
    parser.add_argument('command', choices=['feed', 'search'], default='feed', nargs='?')
    parser.add_argument('--keyword', '-k', default='AI', help='搜索关键词')
    
    args = parser.parse_args()
    
    if args.command == 'feed':
        asyncio.run(collect_xiaohongshu_feed())
    elif args.command == 'search':
        asyncio.run(search_xiaohongshu(args.keyword))
