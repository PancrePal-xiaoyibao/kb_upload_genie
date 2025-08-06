"""
上传跟踪API路由
提供Tracker ID查询功能，无需用户认证
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.tracker import (
    TrackerQueryRequest,
    TrackerStatusResponse,
    TrackerSuccessResponse,
    TrackerNotFoundResponse,
    TrackerErrorResponse
)
from app.services.tracker_service import TrackerService

router = APIRouter()


@router.post("/query", response_model=TrackerSuccessResponse)
async def query_tracker_status(
    request: TrackerQueryRequest,
    db: Session = Depends(get_db)
):
    """
    查询上传跟踪状态
    
    - **tracker_id**: 跟踪ID
    
    返回处理状态和相关元数据，无需用户认证
    """
    try:
        tracker_service = TrackerService(db)
        
        # 查询跟踪状态
        status_data = await tracker_service.get_tracker_status(request.tracker_id)
        
        if not status_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "跟踪ID未找到或已过期",
                    "error_code": "TRACKER_NOT_FOUND"
                }
            )
        
        return TrackerSuccessResponse(
            success=True,
            message="查询成功",
            data=status_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"查询失败: {str(e)}",
                "error_code": "INTERNAL_ERROR",
                "details": {"error": str(e)}
            }
        )


@router.get("/status/{tracker_id}", response_model=TrackerSuccessResponse)
async def get_tracker_status(
    tracker_id: str,
    db: Session = Depends(get_db)
):
    """
    通过GET方法查询上传跟踪状态
    
    - **tracker_id**: 跟踪ID (URL路径参数)
    
    返回处理状态和相关元数据，无需用户认证
    """
    try:
        tracker_service = TrackerService(db)
        
        # 验证tracker_id格式
        if not tracker_id or len(tracker_id) > 36:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "无效的跟踪ID格式",
                    "error_code": "INVALID_TRACKER_ID"
                }
            )
        
        # 查询跟踪状态
        status_data = await tracker_service.get_tracker_status(tracker_id)
        
        if not status_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "跟踪ID未找到或已过期",
                    "error_code": "TRACKER_NOT_FOUND"
                }
            )
        
        return TrackerSuccessResponse(
            success=True,
            message="查询成功",
            data=status_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"查询失败: {str(e)}",
                "error_code": "INTERNAL_ERROR",
                "details": {"error": str(e)}
            }
        )


@router.get("/health")
async def tracker_health():
    """跟踪服务健康检查"""
    return {
        "status": "healthy",
        "service": "tracker",
        "message": "上传跟踪服务运行正常"
    }