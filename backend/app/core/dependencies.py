"""
FastAPI依赖项
包含认证和权限验证的依赖项
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, require_moderator
from app.models.user import User
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer 认证方案
security = HTTPBearer()


async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前活跃用户的依赖项
    验证JWT令牌并返回用户对象
    """
    try:
        user = await get_current_user(session, credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被锁定"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="身份验证失败"
        )


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取当前管理员用户的依赖项
    验证用户是否具有管理员权限
    """
    if not require_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_moderator_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取当前审核员用户的依赖项
    验证用户是否具有审核员或管理员权限
    """
    if not require_moderator(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要审核员或管理员权限"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    可选的当前用户依赖项
    如果提供了令牌则验证，否则返回None
    """
    if not credentials:
        return None
    
    try:
        user = await get_current_user(session, credentials.credentials)
        if user and user.is_active and not user.is_locked:
            return user
        return None
    except Exception as e:
        logger.warning(f"可选用户验证失败: {str(e)}")
        return None


# API Token 验证（用于系统间调用）
async def verify_api_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """
    验证API令牌的依赖项
    用于系统间的API调用认证
    """
    from app.core.config import settings
    
    if credentials.credentials != settings.API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True