"""
邮件上传模型
处理通过邮件上传的文件记录
"""

from sqlalchemy import String, Integer, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import Base


class EmailUploadStatus(str, Enum):
    """邮件上传状态"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已通过
    REJECTED = "rejected"    # 已拒绝
    PROCESSING = "processing"  # 处理中


class EmailUpload(Base):
    """邮件上传记录模型"""
    
    __tablename__ = "email_uploads"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID"
    )
    
    # 邮件信息
    sender_email_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="发送者邮箱哈希值"
    )
    
    sender_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="发送者邮箱原始地址"
    )
    
    # 文件信息
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="原始文件名"
    )
    
    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="存储文件名"
    )
    
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="文件大小（字节）"
    )
    
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="文件类型"
    )
    
    # 邮件内容
    email_subject: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment="邮件主题"
    )
    
    email_body: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="邮件正文"
    )
    
    # 状态和审核
    status: Mapped[EmailUploadStatus] = mapped_column(
        SQLEnum(EmailUploadStatus),
        default=EmailUploadStatus.PENDING,
        comment="上传状态"
    )
    
    # 时间戳
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="邮件接收时间"
    )
    
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="处理时间"
    )
    
    # 审核信息
    reviewer_id: Mapped[str] = mapped_column(
        String(36),
        nullable=True,
        comment="审核员ID"
    )
    
    review_comment: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="审核备注"
    )
    
    # 元数据
    extra_metadata: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="额外元数据（JSON格式）"
    )


class EmailRateLimit(Base):
    """邮件发送频率限制记录"""
    
    __tablename__ = "email_rate_limits"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID"
    )
    
    email_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="邮箱哈希值"
    )
    
    hourly_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="小时内发送次数"
    )
    
    daily_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="当日发送次数"
    )
    
    last_hourly_reset: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="小时计数重置时间"
    )
    
    last_daily_reset: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="日计数重置时间"
    )
    
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否被阻止"
    )
    
    blocked_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="阻止到期时间"
    )


class EmailDomainRule(Base):
    """邮件域名规则配置"""
    
    __tablename__ = "email_domain_rules"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID"
    )
    
    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="域名"
    )
    
    is_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否允许（True=白名单，False=黑名单）"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="规则描述"
    )


class EmailConfig(Base):
    """邮件服务配置"""
    
    __tablename__ = "email_configs"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID"
    )
    
    config_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="配置键名"
    )
    
    config_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="配置值"
    )
    
    config_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="string",
        comment="配置类型（string, int, bool, json）"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="配置描述"
    )
    
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否加密存储"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )


class AttachmentRule(Base):
    """附件规则配置"""
    
    __tablename__ = "attachment_rules"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID"
    )
    
    rule_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="规则名称"
    )
    
    max_file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10 * 1024 * 1024,  # 10MB
        comment="最大文件大小（字节）"
    )
    
    max_file_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="最大文件数量"
    )
    
    allowed_extensions: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="允许的文件扩展名（JSON数组）"
    )
    
    blocked_extensions: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="禁止的文件扩展名（JSON数组）"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )
