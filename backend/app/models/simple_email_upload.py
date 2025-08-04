"""
简化的邮件上传模型
只保存基本的附件信息
"""

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


class SimpleEmailUpload(Base):
    """简化的邮件上传记录模型"""
    
    __tablename__ = "simple_email_uploads"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID"
    )
    
    # 发送者邮箱（明文存储，用于公开展示）
    sender_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="发送者邮箱地址"
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
        comment="文件类型/扩展名"
    )
    
    # 邮件主题（可选）
    email_subject: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment="邮件主题"
    )
    
    # 上传时间
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="上传时间"
    )
    
    # 文件存储路径
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="文件存储路径"
    )