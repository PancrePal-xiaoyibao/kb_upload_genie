"""
管理员相关的API路由
包含管理员专用的接口和功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_admin_user, get_current_moderator_user
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import UserInfo, ApiResponse
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/dashboard", response_model=dict, summary="管理员仪表板")
async def admin_dashboard(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    管理员仪表板
    显示系统统计信息
    """
    try:
        # 统计用户数量
        result = await session.execute(select(User))
        all_users = result.scalars().all()
        
        user_stats = {
            "total_users": len(all_users),
            "active_users": len([u for u in all_users if u.status == UserStatus.ACTIVE]),
            "admin_users": len([u for u in all_users if u.role == UserRole.ADMIN]),
            "moderator_users": len([u for u in all_users if u.role == UserRole.MODERATOR]),
            "regular_users": len([u for u in all_users if u.role == UserRole.USER])
        }
        
        return {
            "message": "欢迎访问管理员仪表板",
            "current_admin": {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.name
            },
            "system_stats": user_stats
        }
        
    except Exception as e:
        logger.error(f"获取管理员仪表板数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取仪表板数据失败"
        )


@router.get("/users", response_model=List[UserInfo], summary="获取所有用户")
async def get_all_users(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    获取所有用户列表
    仅管理员可访问
    """
    try:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        return [UserInfo.model_validate(user) for user in users]
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/users/{user_id}", response_model=UserInfo, summary="获取用户详情")
async def get_user_detail(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的详细信息
    仅管理员可访问
    """
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserInfo.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户详情失败"
        )


@router.put("/users/{user_id}/status", response_model=ApiResponse, summary="修改用户状态")
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    修改用户状态
    仅管理员可操作
    """
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改自己的状态"
            )
        
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        old_status = user.status
        user.status = new_status
        await session.commit()
        
        logger.info(f"管理员 {current_user.email} 将用户 {user.email} 状态从 {old_status} 修改为 {new_status}")
        
        return ApiResponse(
            success=True,
            message=f"用户状态已修改为 {new_status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改用户状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改用户状态失败"
        )


@router.get("/moderator/test", response_model=dict, summary="审核员测试接口")
async def moderator_test(
    current_user: User = Depends(get_current_moderator_user)
):
    """
    审核员测试接口
    审核员和管理员都可以访问
    """
    return {
        "message": "审核员权限验证成功",
        "user": {
            "email": current_user.email,
            "role": current_user.role.value,
            "name": current_user.name
        }
    }


@router.get("/system/info", response_model=dict, summary="系统信息")
async def system_info(
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取系统信息
    仅管理员可访问
    """
    from app.core.config import settings
    
    return {
        "system": {
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "debug_mode": settings.DEBUG,
            "database_url": settings.DATABASE_URL.split("://")[0] + "://***",  # 隐藏敏感信息
            "jwt_algorithm": settings.JWT_ALGORITHM,
            "admin_email": settings.ADMIN_EMAIL
        },
        "current_admin": {
            "email": current_user.email,
            "name": current_user.name,
            "login_time": current_user.last_login_at
        }
    }