"""
定时任务 Web 界面模块
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.scheduler_manager import get_scheduler_manager

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


# 数据模型
class UpdateScheduleRequest(BaseModel):
    hour: int
    minute: int


class BackfillRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str
    user_id: str = "default"


SCHEDULER_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Agent - 定时任务管理</title>
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
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s;
            margin-right: 5px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #666;
        }
        
        .btn-success {
            background: #4caf50;
            color: white;
        }
        
        .btn-warning {
            background: #ff9800;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
        }
        
        tr:hover { background: #f9f9f9; }
        
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .status-badge.success { background: #e8f5e9; color: #2e7d32; }
        .status-badge.warning { background: #fff3e0; color: #ef6c00; }
        .status-badge.error { background: #ffebee; color: #c62828; }
        .status-badge.never { background: #f5f5f5; color: #666; }
        
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
            max-width: 500px;
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
        
        input, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 16px;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .time-inputs {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .time-inputs input {
            width: 80px;
            text-align: center;
        }
        
        .backfill-form {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .log-entry {
            padding: 10px;
            border-left: 3px solid #667eea;
            background: #f9f9f9;
            margin-bottom: 10px;
            border-radius: 0 6px 6px 0;
        }
        
        .log-time {
            font-size: 0.85em;
            color: #666;
        }
        
        .log-status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        
        .log-status.success { background: #e8f5e9; color: #2e7d32; }
        .log-status.error { background: #ffebee; color: #c62828; }
        
        @media (max-width: 768px) {
            .container { padding: 15px; }
            .backfill-form { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>⏰ 定时任务管理</h1>
        <div class="nav-links">
            <a href="/">🏠 首页</a>
            <a href="/dashboard">📊 监控面板</a>
            <a href="/setup">⚙️ 配置向导</a>
        </div>
    </nav>
    
    <div class="container">
        <!-- Task List -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">📋 定时任务列表</span>
                <button class="btn btn-secondary" onclick="refreshTasks()">🔄 刷新</button>
            </div>
            <table id="tasks-table">
                <thead>
                    <tr>
                        <th>任务名称</th>
                        <th>调度规则</th>
                        <th>下次执行</th>
                        <th>上次执行</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Tasks will be loaded here -->
                </tbody>
            </table>
        </div>
        
        <!-- Quick Actions -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">⚡ 快捷操作</span>
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="openBackfillModal()">
                    📅 历史补发
                </button>
                <button class="btn btn-success" onclick="runTaskNow('daily_generate')">
                    ▶️ 立即生成日报
                </button>
                <button class="btn btn-secondary" onclick="showHistory()">
                    📜 执行历史
                </button>
            </div>
        </div>
        
        <!-- Execution History -->
        <div class="card" id="history-card" style="display: none;">
            <div class="card-header">
                <span class="card-title">📜 最近执行历史</span>
                <button class="btn btn-secondary" onclick="loadHistory()">刷新</button>
            </div>
            <div id="history-list">
                <!-- History will be loaded here -->
            </div>
        </div>
    </div>
    
    <!-- Edit Schedule Modal -->
    <div class="modal" id="edit-modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title">⏰ 修改调度时间</span>
                <button class="close-btn" onclick="closeModal('edit-modal')">&times;</button>
            </div>
            <div class="form-group">
                <label>执行时间</label>
                <div class="time-inputs">
                    <input type="number" id="edit-hour" min="0" max="23" value="09">
                    <span>:</span>
                    <input type="number" id="edit-minute" min="0" max="59" value="00">
                </div>
            </div>
            <div style="text-align: right;">
                <button class="btn btn-secondary" onclick="closeModal('edit-modal')">取消</button>
                <button class="btn btn-primary" onclick="saveSchedule()">保存</button>
            </div>
        </div>
    </div>
    
    <!-- Backfill Modal -->
    <div class="modal" id="backfill-modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title">📅 历史补发</span>
                <button class="close-btn" onclick="closeModal('backfill-modal')">&times;</button>
            </div>
            <p style="margin-bottom: 15px; color: #666;">补发指定日期范围内的日报</p>
            <div class="backfill-form">
                <div class="form-group">
                    <label>开始日期</label>
                    <input type="date" id="backfill-start">
                </div>
                <div class="form-group">
                    <label>结束日期</label>
                    <input type="date" id="backfill-end">
                </div>
            </div>
            <div class="form-group">
                <label>用户ID（可选）</label>
                <input type="text" id="backfill-user" placeholder="default" value="default">
            </div>
            <div id="backfill-result" style="margin: 15px 0; display: none;">
                <!-- Result will be shown here -->
            </div>
            <div style="text-align: right;">
                <button class="btn btn-secondary" onclick="closeModal('backfill-modal')">取消</button>
                <button class="btn btn-primary" onclick="runBackfill()">开始补发</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentTaskId = null;
        
        // Load tasks on page load
        document.addEventListener('DOMContentLoaded', loadTasks);
        
        async function loadTasks() {
            try {
                const response = await fetch('/api/v1/scheduler/tasks');
                const data = await response.json();
                
                const tbody = document.querySelector('#tasks-table tbody');
                tbody.innerHTML = '';
                
                data.tasks.forEach(task => {
                    const row = document.createElement('tr');
                    
                    const statusClass = task.last_run_status === 'success' ? 'success' :
                                       task.last_run_status === 'error' ? 'error' :
                                       task.last_run_status === 'never' ? 'never' : 'warning';
                    
                    const statusText = task.last_run_status === 'success' ? '成功' :
                                      task.last_run_status === 'error' ? '失败' :
                                      task.last_run_status === 'never' ? '从未执行' : '未知';
                    
                    row.innerHTML = `
                        <td><strong>${task.name}</strong></td>
                        <td>${task.trigger}</td>
                        <td>${task.next_run_time ? new Date(task.next_run_time).toLocaleString() : '已暂停'}</td>
                        <td>${task.last_run_time ? new Date(task.last_run_time).toLocaleString() : '-'}</td>
                        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                        <td>
                            <button class="btn btn-success" onclick="runTaskNow('${task.id}')">运行</button>
                            <button class="btn btn-primary" onclick="openEditModal('${task.id}', '${task.trigger}')">编辑</button>
                            ${task.enabled ? 
                                `<button class="btn btn-warning" onclick="pauseTask('${task.id}')">暂停</button>` :
                                `<button class="btn btn-success" onclick="resumeTask('${task.id}')">恢复</button>`
                            }
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                });
            } catch (error) {
                console.error('Error loading tasks:', error);
            }
        }
        
        function refreshTasks() {
            loadTasks();
        }
        
        function openEditModal(taskId, trigger) {
            currentTaskId = taskId;
            
            // Parse current time from trigger
            const match = trigger.match(/(\d+):(\d+)/);
            if (match) {
                document.getElementById('edit-hour').value = match[1].padStart(2, '0');
                document.getElementById('edit-minute').value = match[2].padStart(2, '0');
            }
            
            document.getElementById('edit-modal').classList.add('active');
        }
        
        function openBackfillModal() {
            // Set default dates
            const today = new Date();
            const weekAgo = new Date(today - 7 * 24 * 60 * 60 * 1000);
            
            document.getElementById('backfill-end').value = today.toISOString().split('T')[0];
            document.getElementById('backfill-start').value = weekAgo.toISOString().split('T')[0];
            
            document.getElementById('backfill-modal').classList.add('active');
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }
        
        async function saveSchedule() {
            const hour = parseInt(document.getElementById('edit-hour').value);
            const minute = parseInt(document.getElementById('edit-minute').value);
            
            try {
                const response = await fetch(`/api/v1/scheduler/tasks/${currentTaskId}/schedule`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({hour, minute})
                });
                
                if (response.ok) {
                    closeModal('edit-modal');
                    loadTasks();
                } else {
                    alert('更新失败');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('更新失败');
            }
        }
        
        async function runTaskNow(taskId) {
            if (!confirm('确定要立即执行此任务？')) return;
            
            try {
                const btn = event.target;
                btn.textContent = '⏳ 执行中...';
                btn.disabled = true;
                
                const response = await fetch(`/api/v1/scheduler/tasks/${taskId}/run`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('任务执行成功！');
                } else {
                    alert('任务执行失败: ' + result.error);
                }
                
                loadTasks();
            } catch (error) {
                console.error('Error:', error);
                alert('执行失败');
            } finally {
                event.target.textContent = '运行';
                event.target.disabled = false;
            }
        }
        
        async function pauseTask(taskId) {
            try {
                const response = await fetch(`/api/v1/scheduler/tasks/${taskId}/pause`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    loadTasks();
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function resumeTask(taskId) {
            try {
                const response = await fetch(`/api/v1/scheduler/tasks/${taskId}/resume`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    loadTasks();
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function runBackfill() {
            const startDate = document.getElementById('backfill-start').value;
            const endDate = document.getElementById('backfill-end').value;
            const userId = document.getElementById('backfill-user').value || 'default';
            
            if (!startDate || !endDate) {
                alert('请选择开始和结束日期');
                return;
            }
            
            if (startDate > endDate) {
                alert('开始日期不能晚于结束日期');
                return;
            }
            
            try {
                const btn = document.querySelector('#backfill-modal .btn-primary');
                btn.textContent = '⏳ 补发中...';
                btn.disabled = true;
                
                const response = await fetch('/api/v1/scheduler/backfill', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({start_date: startDate, end_date: endDate, user_id: userId})
                });
                
                const result = await response.json();
                
                const resultDiv = document.getElementById('backfill-result');
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `
                    <div style="background: ${result.failed === 0 ? '#e8f5e9' : '#fff3e0'}; padding: 15px; border-radius: 6px;">
                        <p><strong>补发完成！</strong></p>
                        <p>总计: ${result.total} 天</p>
                        <p style="color: #2e7d32;">成功: ${result.success} 天</p>
                        ${result.failed > 0 ? `<p style="color: #c62828;">失败: ${result.failed} 天</p>` : ''}
                    </div>
                `;
                
            } catch (error) {
                console.error('Error:', error);
                alert('补发失败');
            } finally {
                const btn = document.querySelector('#backfill-modal .btn-primary');
                btn.textContent = '开始补发';
                btn.disabled = false;
            }
        }
        
        function showHistory() {
            const card = document.getElementById('history-card');
            card.style.display = card.style.display === 'none' ? 'block' : 'none';
            if (card.style.display === 'block') {
                loadHistory();
            }
        }
        
        async function loadHistory() {
            try {
                const response = await fetch('/api/v1/scheduler/history');
                const data = await response.json();
                
                const list = document.getElementById('history-list');
                list.innerHTML = '';
                
                data.history.forEach(h => {
                    const entry = document.createElement('div');
                    entry.className = 'log-entry';
                    
                    const statusClass = h.status;
                    const statusText = h.status === 'success' ? '成功' : 
                                      h.status === 'error' ? '失败' : '运行中';
                    
                    entry.innerHTML = `
                        <span class="log-time">${new Date(h.start_time).toLocaleString()}</span>
                        <span class="log-status ${statusClass}">${statusText}</span>
                        <p style="margin-top: 5px;"><strong>${h.task_name}</strong></p>
                        ${h.error_message ? `<p style="color: #c62828; font-size: 0.9em;">${h.error_message}</p>` : ''}
                    `;
                    
                    list.appendChild(entry);
                });
            } catch (error) {
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
"""


@router.get("", response_class=HTMLResponse)
async def scheduler_page():
    """定时任务管理页面"""
    return SCHEDULER_HTML


@router.get("/api/v1/scheduler/tasks")
async def api_get_tasks():
    """API: 获取所有定时任务"""
    manager = get_scheduler_manager()
    tasks = manager.get_tasks()
    
    return {
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "trigger": t.trigger,
                "next_run_time": t.next_run_time.isoformat() if t.next_run_time else None,
                "last_run_time": t.last_run_time.isoformat() if t.last_run_time else None,
                "last_run_status": t.last_run_status,
                "last_error": t.last_error,
                "enabled": t.enabled
            }
            for t in tasks
        ]
    }


@router.post("/api/v1/scheduler/tasks/{task_id}/run")
async def api_run_task(task_id: str):
    """API: 立即执行任务"""
    manager = get_scheduler_manager()
    result = await manager.run_task_now(task_id)
    return result


@router.post("/api/v1/scheduler/tasks/{task_id}/pause")
async def api_pause_task(task_id: str):
    """API: 暂停任务"""
    manager = get_scheduler_manager()
    success = manager.pause_task(task_id)
    return {"success": success}


@router.post("/api/v1/scheduler/tasks/{task_id}/resume")
async def api_resume_task(task_id: str):
    """API: 恢复任务"""
    manager = get_scheduler_manager()
    success = manager.resume_task(task_id)
    return {"success": success}


@router.put("/api/v1/scheduler/tasks/{task_id}/schedule")
async def api_update_schedule(task_id: str, request: UpdateScheduleRequest):
    """API: 更新任务调度时间"""
    manager = get_scheduler_manager()
    success = manager.update_schedule(task_id, request.hour, request.minute)
    
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {"success": True}


@router.post("/api/v1/scheduler/backfill")
async def api_backfill(request: BackfillRequest):
    """API: 历史补发"""
    manager = get_scheduler_manager()
    result = await manager.backfill_reports(
        start_date=request.start_date,
        end_date=request.end_date,
        user_id=request.user_id
    )
    return result


@router.get("/api/v1/scheduler/history")
async def api_get_history(task_id: Optional[str] = None, limit: int = 20):
    """API: 获取任务执行历史"""
    manager = get_scheduler_manager()
    history = manager.get_history(task_id=task_id, limit=limit)
    
    return {
        "history": [
            {
                "task_id": h.task_id,
                "task_name": h.task_name,
                "start_time": h.start_time.isoformat(),
                "end_time": h.end_time.isoformat() if h.end_time else None,
                "status": h.status,
                "error_message": h.error_message,
                "result": h.result
            }
            for h in history
        ]
    }
