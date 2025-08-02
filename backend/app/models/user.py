"""
用户数据模型
包含用户基本信息、角色权限等
"""

from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    USER = "user"           # 普通用户
    REVIEWER = "reviewer"   # 审核员
    ADMIN = "admin"         # 管理员


class User(Base):
    """用户表模型"""
    
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表"}
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, comment="用户ID")
    
    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        index=True,
        comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True,
        comment="邮箱地址"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        comment="密码哈希值"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="真实姓名"
    )
    
    # 角色和状态
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,
        comment="用户角色"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    # GitHub相关信息
    github_username: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="GitHub用户名"
    )
    github_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="GitHub访问令牌"
    )
    
    # 用户偏好设置
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="zh-CN",
        comment="首选语言"
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Shanghai",
        comment="时区设置"
    )
    
    # 关联关系
    articles: Mapped[List["Article"]] = relationship(
        "Article",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="reviewer",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_reviewer(self) -> bool:
        """检查是否为审核员或管理员"""
        return self.role in (UserRole.REVIEWER, UserRole.ADMIN)
    
    @property
    def can_review(self) -> bool:
        """检查是否有审核权限"""
        return self.is_reviewer and self.is_active