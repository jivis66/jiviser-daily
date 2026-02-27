"""
主服务模块 - FastAPI 应用入口
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_column_config, get_settings
from src.database import (
    ContentRepository, 
    DailyReportRepository, 
    get_session, 
    init_db
)
from src.filter.selector import ContentSelector
from src.models import (
    ContentItem, 
    DailyReport, 
    GenerateReportRequest, 
    GenerateReportResponse,
    FeedbackRequest,
    HealthStatus,
    UserProfile
)
from src.output.formatter import ChatFormatter, MarkdownFormatter
from src.output.publisher import Publisher, PushResult
from src.personalization.profile import ProfileManager
from src.scheduler import DailyTaskManager, get_scheduler
from src.scheduler_manager import get_scheduler_manager
from src.service import DailyAgentService
from src.web_setup import router as setup_router
from src.web_scheduler import router as scheduler_router
from src.web_content import router as content_router

settings = get_settings()


# 全局服务实例
_service: Optional[DailyAgentService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _service
    
    # 启动时初始化
    print(f"[Startup] {settings.app_name} 正在启动...")
    
    # 初始化数据库
    await init_db()
    
    # 初始化服务
    _service = DailyAgentService()
    await _service.initialize()
    
    # 启动定时任务
    scheduler = get_scheduler()
    daily_manager = DailyTaskManager(scheduler)
    daily_manager.setup(
        generate_func=_service.generate_daily_report,
        push_func=_service.push_report,
        push_time=settings.default_push_time
    )
    daily_manager.start()
    
    # 初始化定时任务管理器（用于 Web 管理）
    scheduler_manager = get_scheduler_manager()
    scheduler_manager.setup(
        generate_func=_service.generate_daily_report,
        push_func=_service.push_report
    )
    
    print(f"[Startup] {settings.app_name} 启动完成")
    
    yield
    
    # 关闭时清理
    print(f"[Shutdown] {settings.app_name} 正在关闭...")
    daily_manager.shutdown()
    print(f"[Shutdown] {settings.app_name} 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="完美个性化日报信息收集 Agent",
    version="1.0.0",
    lifespan=lifespan
)

# 注册 Web 界面路由
app.include_router(setup_router)
app.include_router(scheduler_router)
app.include_router(content_router)


# 依赖注入
async def get_db_session():
    """获取数据库会话"""
    async with get_session() as session:
        yield session


def get_service() -> DailyAgentService:
    """获取服务实例"""
    if _service is None:
        raise HTTPException(status_code=503, detail="服务尚未初始化")
    return _service


# API 路由

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check() -> HealthStatus:
    """健康检查"""
    return HealthStatus(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )


@app.post("/api/v1/reports/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    service: DailyAgentService = Depends(get_service),
    session: AsyncSession = Depends(get_db_session)
):
    """
    生成日报
    
    - 支持指定日期（默认今天）
    - 支持指定分栏
    - 支持强制刷新
    """
    try:
        date = request.date or datetime.now(timezone.utc)
        
        # 检查是否已存在
        if not request.force_refresh:
            repo = DailyReportRepository(session)
            existing = await repo.get_by_date(request.user_id or "default", date)
            if existing:
                return GenerateReportResponse(
                    success=True,
                    report_id=existing.id,
                    message="日报已存在",
                    data={"report_id": existing.id, "date": date.isoformat()}
                )
        
        # 生成日报
        report = await service.generate_daily_report(
            user_id=request.user_id or "default",
            date=date,
            column_ids=request.columns
        )
        
        return GenerateReportResponse(
            success=True,
            report_id=report.id,
            message="日报生成成功",
            data={
                "report_id": report.id,
                "date": date.isoformat(),
                "total_items": report.total_items
            }
        )
        
    except Exception as e:
        return GenerateReportResponse(
            success=False,
            message=f"生成失败: {str(e)}"
        )


@app.post("/api/v1/reports/{report_id}/push")
async def push_report(
    report_id: str,
    channels: Optional[List[str]] = None,
    service: DailyAgentService = Depends(get_service),
    session: AsyncSession = Depends(get_db_session)
):
    """推送日报"""
    try:
        # 获取日报
        repo = DailyReportRepository(session)
        report = await repo.get_by_id(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="日报不存在")
        
        # 推送
        results = await service.push_report(report, channels)
        
        return {
            "success": True,
            "report_id": report_id,
            "results": {
                k.value if hasattr(k, 'value') else k: {
                    "success": v.success,
                    "message": v.message
                }
                for k, v in results.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reports/{report_id}")
async def get_report(
    report_id: str,
    format: str = "json",
    session: AsyncSession = Depends(get_db_session)
):
    """获取日报"""
    try:
        repo = DailyReportRepository(session)
        report = await repo.get_by_id(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="日报不存在")
        
        if format == "markdown":
            # 返回 Markdown 格式
            formatter = MarkdownFormatter()
            # TODO: 获取分栏内容和 items
            content = f"# {report.title}\n\n生成时间: {report.created_at}"
            return {"content": content}
        
        # 返回 JSON
        return {
            "id": report.id,
            "title": report.title,
            "date": report.date.isoformat(),
            "total_items": report.total_items,
            "is_sent": report.is_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reports")
async def list_reports(
    user_id: str = "default",
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session)
):
    """获取日报列表"""
    from sqlalchemy import select
    from src.database import DailyReportDB
    
    result = await session.execute(
        select(DailyReportDB)
        .where(DailyReportDB.user_id == user_id)
        .order_by(DailyReportDB.date.desc())
        .offset(offset)
        .limit(limit)
    )
    reports = result.scalars().all()
    
    return {
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "date": r.date.isoformat(),
                "total_items": r.total_items,
                "is_sent": r.is_sent
            }
            for r in reports
        ],
        "total": len(reports)
    }


@app.get("/api/v1/contents")
async def list_contents(
    column_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session)
):
    """获取内容列表"""
    try:
        repo = ContentRepository(session)
        
        if column_id:
            items = await repo.get_by_column(
                column_id=column_id,
                status=status,
                limit=limit
            )
        else:
            # 获取所有内容
            from sqlalchemy import select
            from src.database import ContentItemDB
            
            query = select(ContentItemDB).limit(limit)
            if status:
                query = query.where(ContentItemDB.status == status)
            
            result = await session.execute(query)
            items = result.scalars().all()
        
        return {
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "source": item.source,
                    "url": item.url,
                    "status": item.status,
                    "quality_score": item.quality_score,
                    "column_id": item.column_id
                }
                for item in items
            ],
            "total": len(items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """提交反馈"""
    try:
        from src.database import UserFeedbackDB
        
        # 保存反馈
        feedback = UserFeedbackDB(
            user_id=request.user_id,
            content_id=request.item_id,
            feedback_type=request.feedback_type,
            comment=request.comment
        )
        session.add(feedback)
        await session.commit()
        
        # 更新用户画像
        profile_manager = ProfileManager(session)
        await profile_manager.add_feedback(
            request.user_id,
            request.item_id,
            request.feedback_type
        )
        
        return {"success": True, "message": "反馈已提交"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/profile/{user_id}")
async def get_profile(
    user_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """获取用户画像"""
    try:
        manager = ProfileManager(session)
        profile = await manager.get_profile(user_id)
        
        return {
            "user_id": profile.user_id,
            "interests": profile.interests,
            "preferred_sources": profile.preferred_sources,
            "push_channels": [c.value for c in profile.push_channels],
            "push_time": profile.push_time,
            "summary_style": profile.summary_style
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/profile/{user_id}")
async def update_profile(
    user_id: str,
    data: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """更新用户画像"""
    try:
        manager = ProfileManager(session)
        profile = await manager.get_profile(user_id)
        
        # 更新字段
        if "interests" in data:
            profile.interests = data["interests"]
        if "push_time" in data:
            profile.push_time = data["push_time"]
        if "push_channels" in data:
            from src.models import ChannelType
            profile.push_channels = [ChannelType(c) for c in data["push_channels"]]
        
        await manager.save_profile(profile)
        
        return {"success": True, "message": "画像已更新"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/collect")
async def trigger_collection(
    service: DailyAgentService = Depends(get_service)
):
    """手动触发采集"""
    try:
        result = await service.collect_all()
        
        total_collected = sum(
            len(r.items) for r in result.values() if r.success
        )
        
        return {
            "success": True,
            "total_collected": total_collected,
            "details": {
                name: {
                    "success": r.success,
                    "count": len(r.items),
                    "message": r.message
                }
                for name, r in result.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reload")
async def reload_config():
    """重新加载配置（热更新）"""
    try:
        config = get_column_config()
        config.reload()
        
        return {
            "success": True,
            "message": "配置已重新加载"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
