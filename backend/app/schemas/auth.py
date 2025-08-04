"""
认证相关的数据模型
包含登录请求、响应和用户信息等模型
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, UserStatus


class LoginRequest(BaseModel):
    """登录请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=6, description="用户密码")


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")


class UserInfo(BaseModel):
    """用户信息模型"""
    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    name: str = Field(..., description="用户姓名")
    role: UserRole = Field(..., description="用户角色")
    status: UserStatus = Field(..., description="用户状态")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应模型"""
    user: UserInfo = Field(..., description="用户信息")
    token: TokenResponse = Field(..., description="令牌信息")
    message: str = Field(default="登录成功", description="响应消息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")