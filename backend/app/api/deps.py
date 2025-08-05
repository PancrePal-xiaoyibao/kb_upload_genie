"""
API依赖项
提供通用的依赖注入函数
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
import logging

from app.core.database import AsyncSessionLocal
from app.core.auth import verify_token
from app.models.user import User, UserRole
from app.schemas.auth import TokenPayload

logger = logging.getLogger(__name__)

# 使用OAuth2PasswordBearer来提取Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_db() -> Generator[AsyncSession, None, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    根据JWT令牌获取当前用户
    如果令牌无效或用户不存在，则返回None
    """
    if not token:
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token)
        if payload is None:
            logger.warning("验证令牌失败，payload为空")
            return None
        
        # 使用Pydantic模型进行验证
        token_data = TokenPayload(**payload)
        
    except JWTError as e:
        logger.warning(f"JWT解码失败: {e}")
        return None
    except Exception as e:
        logger.error(f"解析token payload出错: {e}")
        return None

    try:
        result = await db.execute(select(User).where(User.id == token_data.sub))
        user = result.scalar_one_or_none()
        if user is None:
            logger.warning(f"未找到用户: id={token_data.sub}")
        return user
    except Exception as e:
        logger.error(f"数据库查询用户失败: {e}")
        return None


async def require_current_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    依赖项：必须获取当前用户
    如果用户未登录或令牌无效，则抛出401异常
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_admin_user(
    current_user: User = Depends(require_current_user)
) -> User:
    """
    依赖项：要求当前用户必须是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user

async def get_optional_current_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    依赖项：获取可选的当前用户
    如果用户未登录，则返回None，不抛出异常
    """
    return current_user