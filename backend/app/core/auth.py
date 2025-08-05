"""
JWT认证工具模块
包含JWT令牌生成、验证和用户认证相关功能
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT验证失败: {str(e)}")
        return None


async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    """验证用户凭据"""
    try:
        # 查询用户
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"用户不存在: {email}")
            return None
        
        # 检查用户状态
        if not user.is_active:
            logger.warning(f"用户账户未激活: {email}")
            return None
        
        if user.is_locked:
            logger.warning(f"用户账户被锁定: {email}")
            return None
        
        # 验证密码
        if not user.check_password(password):
            # 增加登录失败次数
            user.login_attempts += 1
            if user.login_attempts >= 5:
                # 锁定账户1小时
                user.locked_until = datetime.utcnow() + timedelta(hours=1)
                logger.warning(f"用户账户因多次登录失败被锁定: {email}")
            
            await session.commit()
            return None
        
        # 登录成功，重置失败次数
        user.login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        await session.commit()
        
        logger.info(f"用户登录成功: {email}")
        return user
        
    except Exception as e:
        logger.error(f"用户认证失败: {str(e)}")
        return None


async def get_current_user(session: AsyncSession, token: str) -> Optional[User]:
    """根据JWT令牌获取当前用户"""
    payload = verify_token(token)
    if not payload:
        return None
    
    user_id: str = payload.get("sub")
    if not user_id:
        return None
    
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        return None


def require_admin(user: User) -> bool:
    """检查用户是否为管理员"""
    return user and user.can_manage_system()


def require_moderator(user: User) -> bool:
    """检查用户是否为审核员或管理员"""
    return user and user.is_moderator and user.is_active and not user.is_locked