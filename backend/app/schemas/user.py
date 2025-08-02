"""
用户数据模式
定义用户相关的Pydantic模型
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础模式"""
    username: str
    email: EmailStr
    real_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER
    is_active: Optional[bool] = True
    github_username: Optional[str] = None
    preferred_language: Optional[str] = "zh-CN"
    timezone: Optional[str] = "Asia/Shanghai"
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名"""
        if len(v) < 3:
            raise ValueError('用户名长度不能少于3个字符')
        if len(v) > 50:
            raise ValueError('用户名长度不能超过50个字符')
        return v


class UserCreate(UserBase):
    """用户创建模式"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码"""
        if len(v) < 6:
            raise ValueError('密码长度不能少于6个字符')
        if len(v) > 100:
            raise ValueError('密码长度不能超过100个字符')
        return v


class UserUpdate(BaseModel):
    """用户更新模式"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    real_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    github_username: Optional[str] = None
    github_token: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名"""
        if v is not None:
            if len(v) < 3:
                raise ValueError('用户名长度不能少于3个字符')
            if len(v) > 50:
                raise ValueError('用户名长度不能超过50个字符')
        return v


class UserPasswordUpdate(BaseModel):
    """用户密码更新模式"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码"""
        if len(v) < 6:
            raise ValueError('密码长度不能少于6个字符')
        if len(v) > 100:
            raise ValueError('密码长度不能超过100个字符')
        return v


class UserInDBBase(UserBase):
    """数据库中的用户基础模式"""
    id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class User(UserInDBBase):
    """用户响应模式"""
    pass


class UserInDB(UserInDBBase):
    """数据库中的用户模式（包含密码哈希）"""
    password_hash: str


class UserLogin(BaseModel):
    """用户登录模式"""
    identifier: str  # 用户名或邮箱
    password: str


class UserProfile(BaseModel):
    """用户资料模式"""
    id: int
    username: str
    email: EmailStr
    real_name: Optional[str] = None
    role: UserRole
    is_active: bool
    github_username: Optional[str] = None
    preferred_language: str
    timezone: str
    created_at: str
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """用户统计模式"""
    total_articles: int = 0
    published_articles: int = 0
    draft_articles: int = 0
    total_reviews: int = 0
    approved_reviews: int = 0
    rejected_reviews: int = 0