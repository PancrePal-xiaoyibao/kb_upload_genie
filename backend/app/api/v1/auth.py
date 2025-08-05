"""
认证相关的API路由
包含登录、登出、令牌刷新等接口
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_current_user
from app.core.auth import (
    authenticate_user, 
    create_access_token, 
    create_refresh_token,
    verify_token
)
from app.core.config import settings
from app.core.turnstile import verify_turnstile
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    TokenResponse, 
    UserInfo,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ApiResponse
)
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    用户登录接口
    
    - **email**: 用户邮箱
    - **password**: 用户密码
    - **turnstile_token**: Turnstile验证令牌（可选）
    
    返回用户信息和访问令牌
    """
    try:
        # Turnstile验证（如果启用）
        if settings.TURNSTILE_ENABLED:
            client_ip = request.client.host if request.client else None
            await verify_turnstile(login_data.turnstile_token, client_ip)
        
        # 验证用户凭据
        user = await authenticate_user(session, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )
        
        # 创建访问令牌和刷新令牌
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # 构造响应
        user_info = UserInfo.model_validate(user)
        token_info = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        logger.info(f"用户登录成功: {user.email}")
        return LoginResponse(user=user_info, token=token_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    
    返回新的访问令牌
    """
    try:
        # 验证刷新令牌
        payload = verify_token(refresh_data.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌格式"
            )
        
        # 获取用户信息
        user = await session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # 刷新令牌保持不变
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败，请重新登录"
        )


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(require_current_user)):
    """
    获取当前登录用户的信息
    
    需要在请求头中提供有效的访问令牌
    """
    return UserInfo.model_validate(current_user)


@router.post("/change-password", response_model=ApiResponse, summary="修改密码")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(require_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    修改当前用户密码
    
    - **old_password**: 旧密码
    - **new_password**: 新密码
    """
    try:
        # 验证旧密码
        if not current_user.check_password(password_data.old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 设置新密码
        current_user.set_password(password_data.new_password)
        await session.commit()
        
        logger.info(f"用户修改密码成功: {current_user.email}")
        return ApiResponse(
            success=True,
            message="密码修改成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败，请稍后重试"
        )


@router.post("/logout", response_model=ApiResponse, summary="用户登出")
async def logout():
    """
    用户登出接口
    
    注意：由于JWT是无状态的，实际的令牌失效需要在客户端处理
    """
    # 在实际应用中，可以将令牌加入黑名单
    # 这里只是返回成功响应
    return ApiResponse(
        success=True,
        message="登出成功"
    )