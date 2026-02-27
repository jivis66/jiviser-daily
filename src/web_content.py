"""
内容管理 Web 界面模块
提供已采集内容的管理功能
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

router = APIRouter(prefix="/content", tags=["content"])


# 数据模型
class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    quality_score: Optional[int] = None


class ContentCreateRequest(BaseModel):
    title: str
    url: str
    source: str
    content: Optional[str] = None
    summary: Optional[str] = None


CONTENT_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Agent - 内容管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar h1 { font-size: 1.5em; }
        .nav-links a {
            color: white;
            text-decoration: none;
            margin-left: 20px;
            opacity: 0.9;
        }
        .nav-links a:hover { opacity: 1; }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        
        .filters {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .filters input, .filters select {
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .filters input:focus, .filters select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #666;
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .content-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .content-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: all 0.3s;
        }
        
        .content-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .content-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }
        
        .content-title {
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            line-height: 1.4;
            margin-right: 10px;
        }
        
        .content-source {
            display: inline-block;
            padding: 4px 10px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 20px;
            font-size: 0.8em;
            margin-bottom: 10px;
        }
        
        .content-summary {
            color: #666;
            font-size: 0.95em;
            line-height: 1.5;
            margin-bottom: 15px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .content-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85em;
            color: #999;
        }
        
        .content-score {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .score-bar {
            width: 60px;
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
        }
        
        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #f44336 0%, #ff9800 50%, #4caf50 100%);
            border-radius: 3px;
        }
        
        .content-actions {
            display: flex;
            gap: 8px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        
        .content-actions button {
            flex: 1;
            padding: 8px;
            font-size: 0.85em;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 30px;
        }
        
        .pagination button {
            padding: 10px 20px;
        }
        
        .pagination .page-info {
            display: flex;
            align-items: center;
            padding: 0 20px;
            color: #666;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.active {
            display: flex;
        }
        
        .modal-content {
            background: white;
            border-radius: 12px;
            padding: 30px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-title {
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            color: #666;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .stats-bar {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .container { padding: 15px; }
            .content-grid { grid-template-columns: 1fr; }
            .filters { flex-direction: column; align-items: stretch; }
            .filters input, .filters select { width: 100%; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>📝 内容管理</h1>
        <div class="nav-links">
            <a href="/">🏠 首页</a>
            <a href="/dashboard">📊 监控面板</a>
            <a href="/scheduler">⏰ 定时任务</a>
        </div>
    </nav>
    
    <div class="container">
        <!-- Stats -->
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-value" id="total-count">-</div>
                <div class="stat-label">总内容</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="today-count">-</div>
                <div class="stat-label">今日新增</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="avg-score">-</div>
                <div class="stat-label">平均质量分</div>
            </div>
        </div>
        
        <!-- Filters -->
        <div class="filters">
            <input type="text" id="search-input" placeholder="🔍 搜索标题...">
            <select id="source-filter">
                <option value="">所有来源</option>
            </select>
            <select id="status-filter">
                <option value="">所有状态</option>
                <option value="pending">待处理</option>
                <option value="selected">已选中</option>
                <option value="rejected">已拒绝</option>
            </select>
            <select id="sort-by">
                <option value="time">按时间</option>
                <option value="score">按质量分</option>
                <option value="source">按来源</option>
            </select>
            <button class="btn btn-primary" onclick="applyFilters()">应用筛选</button>
            <button class="btn btn-secondary" onclick="resetFilters()">重置</button>
            <button class="btn btn-primary" onclick="openAddModal()">+ 添加内容</button>
        </div>
        
        <!-- Content Grid -->
        <div class="content-grid" id="content-grid">
            <!-- Content will be loaded here -->
        </div>
        
        <!-- Pagination -->
        <div class="pagination">
            <button class="btn btn-secondary" onclick="prevPage()">← 上一页</button>
            <span class="page-info">第 <span id="current-page">1</span> 页</span>
            <button class="btn btn-secondary" onclick="nextPage()">下一页 →</button>
        </div>
    </div>
    
    <!-- Edit Modal -->
    <div class="modal" id="edit-modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title">✏️ 编辑内容</span>
                <button class="close-btn" onclick="closeModal('edit-modal')">&times;</button>
            </div>
            <input type="hidden" id="edit-id">
            <div class="form-group">
                <label>标题</label>
                <input type="text" id="edit-title">
            </div>
            <div class="form-group">
                <label>摘要</label>
                <textarea id="edit-summary"></textarea>
            </div>
            <div class="form-group">
                <label>质量分 (0-100)</label>
                <input type="number" id="edit-score" min="0" max="100">
            </div>
            <div style="text-align: right;">
                <button class="btn btn-secondary" onclick="closeModal('edit-modal')">取消</button>
                <button class="btn btn-primary" onclick="saveEdit()">保存</button>
            </div>
        </div>
    </div>
    
    <!-- Add Modal -->
    <div class="modal" id="add-modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title">➕ 添加内容</span>
                <button class="close-btn" onclick="closeModal('add-modal')">&times;</button>
            </div>
            <div class="form-group">
                <label>标题 *</label>
                <input type="text" id="add-title" placeholder="输入标题">
            </div>
            <div class="form-group">
                <label>URL *</label>
                <input type="text" id="add-url" placeholder="https://...">
            </div>
            <div class="form-group">
                <label>来源 *</label>
                <input type="text" id="add-source" placeholder="例如: 微信公众号">
            </div>
            <div class="form-group">
                <label>内容</label>
                <textarea id="add-content" placeholder="正文内容（可选）"></textarea>
            </div>
            <div class="form-group">
                <label>摘要</label>
                <textarea id="add-summary" placeholder="内容摘要（可选）"></textarea>
            </div>
            <div style="text-align: right;">
                <button class="btn btn-secondary" onclick="closeModal('add-modal')">取消</button>
                <button class="btn btn-primary" onclick="saveNew()">添加</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentPage = 1;
        let currentContentId = null;
        
        document.addEventListener('DOMContentLoaded', () => {
            loadStats();
            loadContent();
            loadSources();
        });
        
        async function loadStats() {
            try {
                const response = await fetch('/api/v1/content/stats');
                const data = await response.json();
                
                document.getElementById('total-count').textContent = data.total || 0;
                document.getElementById('today-count').textContent = data.today || 0;
                document.getElementById('avg-score').textContent = data.avg_score || '-';
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        async function loadSources() {
            try {
                const response = await fetch('/api/v1/content/sources');
                const data = await response.json();
                
                const select = document.getElementById('source-filter');
                data.sources.forEach(source => {
                    const option = document.createElement('option');
                    option.value = source;
                    option.textContent = source;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading sources:', error);
            }
        }
        
        async function loadContent() {
            try {
                const search = document.getElementById('search-input').value;
                const source = document.getElementById('source-filter').value;
                const status = document.getElementById('status-filter').value;
                const sort = document.getElementById('sort-by').value;
                
                const params = new URLSearchParams({
                    page: currentPage,
                    limit: 12,
                    search: search,
                    source: source,
                    status: status,
                    sort: sort
                });
                
                const response = await fetch(`/api/v1/content?${params}`);
                const data = await response.json();
                
                const grid = document.getElementById('content-grid');
                grid.innerHTML = '';
                
                data.items.forEach(item => {
                    const card = createContentCard(item);
                    grid.appendChild(card);
                });
                
                document.getElementById('current-page').textContent = currentPage;
            } catch (error) {
                console.error('Error loading content:', error);
            }
        }
        
        function createContentCard(item) {
            const div = document.createElement('div');
            div.className = 'content-card';
            
            const score = item.quality_score || 0;
            const scorePercent = Math.min(score, 100);
            
            div.innerHTML = `
                <div class="content-header">
                    <span class="content-title">${escapeHtml(item.title)}</span>
                </div>
                <span class="content-source">${escapeHtml(item.source)}</span>
                <div class="content-summary">${escapeHtml(item.summary || item.content || '无摘要')}</div>
                <div class="content-meta">
                    <span>${new Date(item.fetch_time || item.created_at).toLocaleDateString()}</span>
                    <div class="content-score">
                        <span>${score}分</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${scorePercent}%"></div>
                        </div>
                    </div>
                </div>
                <div class="content-actions">
                    <button class="btn btn-secondary" onclick="viewContent('${item.id}')">👁️ 查看</button>
                    <button class="btn btn-primary" onclick="editContent('${item.id}')">✏️ 编辑</button>
                    <button class="btn btn-danger" onclick="deleteContent('${item.id}')">🗑️ 删除</button>
                </div>
            `;
            
            return div;
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function applyFilters() {
            currentPage = 1;
            loadContent();
        }
        
        function resetFilters() {
            document.getElementById('search-input').value = '';
            document.getElementById('source-filter').value = '';
            document.getElementById('status-filter').value = '';
            document.getElementById('sort-by').value = 'time';
            currentPage = 1;
            loadContent();
        }
        
        function prevPage() {
            if (currentPage > 1) {
                currentPage--;
                loadContent();
            }
        }
        
        function nextPage() {
            currentPage++;
            loadContent();
        }
        
        function openModal(modalId) {
            document.getElementById(modalId).classList.add('active');
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }
        
        function openAddModal() {
            openModal('add-modal');
        }
        
        async function editContent(id) {
            try {
                const response = await fetch(`/api/v1/content/${id}`);
                const item = await response.json();
                
                currentContentId = id;
                document.getElementById('edit-id').value = id;
                document.getElementById('edit-title').value = item.title;
                document.getElementById('edit-summary').value = item.summary || '';
                document.getElementById('edit-score').value = item.quality_score || 50;
                
                openModal('edit-modal');
            } catch (error) {
                console.error('Error:', error);
                alert('加载失败');
            }
        }
        
        async function saveEdit() {
            try {
                const data = {
                    title: document.getElementById('edit-title').value,
                    summary: document.getElementById('edit-summary').value,
                    quality_score: parseInt(document.getElementById('edit-score').value)
                };
                
                const response = await fetch(`/api/v1/content/${currentContentId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    closeModal('edit-modal');
                    loadContent();
                    loadStats();
                } else {
                    alert('保存失败');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('保存失败');
            }
        }
        
        async function saveNew() {
            try {
                const data = {
                    title: document.getElementById('add-title').value,
                    url: document.getElementById('add-url').value,
                    source: document.getElementById('add-source').value,
                    content: document.getElementById('add-content').value,
                    summary: document.getElementById('add-summary').value
                };
                
                if (!data.title || !data.url || !data.source) {
                    alert('请填写必填项');
                    return;
                }
                
                const response = await fetch('/api/v1/content', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    closeModal('add-modal');
                    loadContent();
                    loadStats();
                    
                    // Clear form
                    document.getElementById('add-title').value = '';
                    document.getElementById('add-url').value = '';
                    document.getElementById('add-source').value = '';
                    document.getElementById('add-content').value = '';
                    document.getElementById('add-summary').value = '';
                } else {
                    alert('添加失败');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('添加失败');
            }
        }
        
        async function deleteContent(id) {
            if (!confirm('确定要删除此内容吗？')) return;
            
            try {
                const response = await fetch(`/api/v1/content/${id}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    loadContent();
                    loadStats();
                } else {
                    alert('删除失败');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('删除失败');
            }
        }
        
        function viewContent(id) {
            window.open(`/api/v1/content/${id}/view`, '_blank');
        }
    </script>
</body>
</html>
"""


@router.get("", response_class=HTMLResponse)
async def content_page():
    """内容管理页面"""
    return CONTENT_HTML


@router.get("/api/v1/content")
async def api_get_content(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    search: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = Query("time", regex="^(time|score|source)$")
):
    """API: 获取内容列表"""
    try:
        from src.database import get_session, ContentRepository
        from sqlalchemy import select
        from src.database import ContentItemDB
        
        async with get_session() as session:
            # 构建查询
            query = select(ContentItemDB)
            
            # 筛选条件
            if search:
                query = query.where(ContentItemDB.title.contains(search))
            if source:
                query = query.where(ContentItemDB.source == source)
            if status:
                query = query.where(ContentItemDB.status == status)
            
            # 排序
            if sort == "time":
                query = query.order_by(ContentItemDB.fetch_time.desc())
            elif sort == "score":
                query = query.order_by(ContentItemDB.quality_score.desc())
            elif sort == "source":
                query = query.order_by(ContentItemDB.source)
            
            # 分页
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            items = result.scalars().all()
            
            return {
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "url": item.url,
                        "source": item.source,
                        "summary": item.summary,
                        "content": item.content[:200] if item.content else None,
                        "quality_score": item.quality_score,
                        "status": item.status,
                        "fetch_time": item.fetch_time.isoformat() if item.fetch_time else None,
                        "created_at": item.created_at.isoformat() if item.created_at else None
                    }
                    for item in items
                ],
                "page": page,
                "limit": limit
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/content/{content_id}")
async def api_get_content_item(content_id: str):
    """API: 获取单个内容"""
    try:
        from src.database import get_session, ContentRepository
        
        async with get_session() as session:
            repo = ContentRepository(session)
            item = await repo.get_by_id(content_id)
            
            if not item:
                raise HTTPException(status_code=404, detail="内容不存在")
            
            return {
                "id": item.id,
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "content": item.content,
                "summary": item.summary,
                "quality_score": item.quality_score,
                "status": item.status,
                "fetch_time": item.fetch_time.isoformat() if item.fetch_time else None
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/v1/content/{content_id}")
async def api_update_content(content_id: str, request: ContentUpdateRequest):
    """API: 更新内容"""
    try:
        from src.database import get_session, ContentRepository
        
        async with get_session() as session:
            repo = ContentRepository(session)
            item = await repo.get_by_id(content_id)
            
            if not item:
                raise HTTPException(status_code=404, detail="内容不存在")
            
            # 更新字段
            if request.title is not None:
                item.title = request.title
            if request.summary is not None:
                item.summary = request.summary
            if request.quality_score is not None:
                item.quality_score = request.quality_score
            
            await repo.update(item)
            
            return {"success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/v1/content/{content_id}")
async def api_delete_content(content_id: str):
    """API: 删除内容"""
    try:
        from src.database import get_session
        from sqlalchemy import delete
        from src.database import ContentItemDB
        
        async with get_session() as session:
            await session.execute(
                delete(ContentItemDB).where(ContentItemDB.id == content_id)
            )
            await session.commit()
            
            return {"success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/content")
async def api_create_content(request: ContentCreateRequest):
    """API: 创建内容"""
    try:
        from src.database import get_session
        from src.database import ContentItemDB
        from datetime import datetime, timezone
        import hashlib
        
        async with get_session() as session:
            # 生成 ID
            url_hash = hashlib.md5(request.url.encode()).hexdigest()[:12]
            content_id = f"manual_{url_hash}"
            
            # 创建内容
            item = ContentItemDB(
                id=content_id,
                title=request.title,
                url=request.url,
                source=request.source,
                content=request.content,
                summary=request.summary,
                source_type="manual",
                status="pending",
                fetch_time=datetime.now(timezone.utc),
                quality_score=50  # 默认分数
            )
            
            session.add(item)
            await session.commit()
            
            return {"success": True, "id": content_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/content/stats")
async def api_content_stats():
    """API: 获取内容统计"""
    try:
        from src.database import get_session
        from sqlalchemy import func, select
        from src.database import ContentItemDB
        from datetime import datetime, timedelta, timezone
        
        async with get_session() as session:
            # 总数
            result = await session.execute(select(func.count()).select_from(ContentItemDB))
            total = result.scalar()
            
            # 今日新增
            today = datetime.now(timezone.utc).date()
            result = await session.execute(
                select(func.count())
                .select_from(ContentItemDB)
                .where(func.date(ContentItemDB.fetch_time) == today)
            )
            today_count = result.scalar()
            
            # 平均质量分
            result = await session.execute(
                select(func.avg(ContentItemDB.quality_score))
                .select_from(ContentItemDB)
            )
            avg_score = result.scalar()
            
            return {
                "total": total,
                "today": today_count,
                "avg_score": round(avg_score, 1) if avg_score else 0
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/content/sources")
async def api_content_sources():
    """API: 获取所有内容来源"""
    try:
        from src.database import get_session
        from sqlalchemy import distinct, select
        from src.database import ContentItemDB
        
        async with get_session() as session:
            result = await session.execute(
                select(distinct(ContentItemDB.source))
                .where(ContentItemDB.source.isnot(None))
            )
            sources = [r[0] for r in result.all()]
            
            return {"sources": sources}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
