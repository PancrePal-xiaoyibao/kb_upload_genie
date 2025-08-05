"""
简化邮件系统配置文件
包含基本的邮件服务器配置
"""

import os
from typing import Optional

class SimpleEmailConfig:
    """简化的邮件配置类"""
    
    # IMAP配置
    IMAP_HOST: str = os.getenv("IMAP_HOST", "imap.gmail.com")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
    IMAP_USER: str = os.getenv("IMAP_USER", "noreply@gmail.com")
    IMAP_PASSWORD: str = os.getenv("IMAP_PASSWORD", "")
    IMAP_USE_SSL: bool = os.getenv("IMAP_USE_SSL", "true").lower() == "true"
    IMAP_MAILBOX: str = os.getenv("IMAP_MAILBOX", "INBOX")
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./simple_email.db")
    
    # 文件存储配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # 系统配置
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    @classmethod
    def get_imap_config(cls) -> dict:
        """获取IMAP配置"""
        return {
            "host": cls.IMAP_HOST,
            "port": cls.IMAP_PORT,
            "user": cls.IMAP_USER,
            "password": cls.IMAP_PASSWORD,
            "use_ssl": cls.IMAP_USE_SSL,
            "mailbox": cls.IMAP_MAILBOX
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        required_fields = [
            cls.IMAP_HOST,
            cls.IMAP_USER,
            cls.IMAP_PASSWORD
        ]
        return all(field for field in required_fields)


# 创建配置实例
simple_config = SimpleEmailConfig()