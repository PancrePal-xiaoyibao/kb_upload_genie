"""
用户数据模型
包含用户基本信息、角色权限等
"""

from sqlalchemy import String, Boolean, Enum as SQLEnum, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
import enum
import uuid
from passlib.context import CryptContext

from app.core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    USER = "user"           # 普通用户
    MODERATOR = "moderator" # 审核员
    ADMIN = "admin"         # 管理员


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"       # 激活
    INACTIVE = "inactive"   # 未激活
    SUSPENDED = "suspended" # 暂停
    DELETED = "deleted"     # 已删除


class User(Base):
    """用户表模型"""
    
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表"}
    
    # 主键
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="用户ID"
    )
    
    # 基本信息
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="邮箱地址"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希值"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="用户姓名"
    )
    
    # 角色和状态
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,
        comment="用户角色"
    )
    
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        default=UserStatus.ACTIVE,
        comment="用户状态"
    )
    
    # 认证相关
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间"
    )
    
    login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="登录尝试次数"
    )
    
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="账户锁定到期时间"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 元数据
    profile_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户配置数据（JSON格式）"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="管理员备注"
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
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    # 密码加密上下文
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self._pwd_context.verify(password, self.password_hash)
    
    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = self._hash_password(password)
    
    @classmethod
    def _hash_password(cls, password: str) -> str:
        """生成密码哈希值"""
        return cls._pwd_context.hash(password)
    
    @property
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_moderator(self) -> bool:
        """检查是否为审核员或管理员"""
        return self.role in (UserRole.MODERATOR, UserRole.ADMIN)
    
    @property
    def is_active(self) -> bool:
        """检查是否为活跃用户"""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def can_manage_system(self) -> bool:
        """检查是否有系统管理权限"""
        return self.is_admin and self.is_active and not self.is_locked