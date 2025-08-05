"""
应用配置管理
使用 Pydantic Settings 管理环境变量和配置
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional, Union
import os


class Settings(BaseSettings):
    """应用设置类"""
    
    # 基础配置
    PROJECT_NAME: str = "KB Upload Genie"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(...)
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ALLOWED_HOSTS: Union[str, List[str]] = Field(
        default="localhost,127.0.0.1,0.0.0.0,http://localhost:3000"
    )
    
    # 数据库配置
    DATABASE_URL: str = Field(...)
    DATABASE_ECHO: bool = Field(default=False)
    
    # Redis配置 - 已移除，使用SQLite作为轻量级解决方案
    
    # JWT配置
    JWT_SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # API认证配置
    API_TOKEN: str = Field(default="admin_token_change_in_production")
    
    # 管理员账户配置
    ADMIN_EMAIL: str = Field(default="admin@example.com")
    ADMIN_PASSWORD: str = Field(default="admin123456")
    ADMIN_NAME: str = Field(default="系统管理员")
    
    # AI服务配置
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_BASE_URL: Optional[str] = Field(default=None)
    
    # GLM配置
    GLM_API_KEY: Optional[str] = Field(default=None)
    GLM_BASE_URL: str = Field(default="https://open.bigmodel.cn/api/paas/v4/")
    
    # Gemini配置
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    
    # Moonshot配置
    MOONSHOT_API_KEY: Optional[str] = Field(default=None)
    MOONSHOT_BASE_URL: str = Field(default="https://api.moonshot.cn/v1")
    
    # StepFun配置
    STEPFUN_API_KEY: Optional[str] = Field(default=None)
    STEPFUN_BASE_URL: str = Field(default="https://api.stepfun.com/v1")
    
    # GitHub配置
    GITHUB_CLIENT_ID: Optional[str] = Field(default=None)
    GITHUB_CLIENT_SECRET: Optional[str] = Field(default=None)
    GITHUB_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    
    # 文件上传配置
    UPLOAD_DIR: str = Field(default="uploads")
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024)  # 50MB
    ALLOWED_FILE_TYPES: Union[str, List[str]] = Field(
        default=".md,.txt,.docx,.pdf,.pptx"
    )
    
    # 任务队列配置 - 简化版，不使用Celery
    ENABLE_BACKGROUND_TASKS: bool = Field(default=False)
    
    # Cloudflare Turnstile配置
    TURNSTILE_SECRET_KEY: Optional[str] = Field(default=None)
    TURNSTILE_SITE_KEY: Optional[str] = Field(default=None)
    TURNSTILE_ENABLED: bool = Field(default=False)
    TURNSTILE_ALLOW_SKIP_IN_DEV: bool = Field(default=True)
    
    # 邮件配置
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_TLS: bool = Field(default=True)
    
    # 邮件上传功能配置
    EMAIL_UPLOAD_ENABLED: bool = Field(default=True, description="是否启用邮件上传功能")
    
    # 系统邮件过滤配置
    EMAIL_SYSTEM_SENDERS: Union[str, List[str]] = Field(
        default="mailer-daemon@,noreply@,no-reply@,donotreply@,do-not-reply@,postmaster@,bounce@,bounces@,system@,admin@,administrator@",
        description="要跳过的系统邮件发送者前缀列表"
    )
    
    # IMAP配置（用于接收邮件）
    IMAP_HOST: Optional[str] = Field(default=None, description="IMAP服务器地址")
    IMAP_PORT: int = Field(default=993, description="IMAP端口")
    IMAP_USER: Optional[str] = Field(default=None, description="IMAP用户名")
    IMAP_PASSWORD: Optional[str] = Field(default=None, description="IMAP密码")
    IMAP_USE_SSL: bool = Field(default=True, description="是否使用SSL")
    IMAP_MAILBOX: str = Field(default="INBOX", description="邮箱文件夹")
    
    # 邮件检查配置
    EMAIL_CHECK_INTERVAL: int = Field(default=15, description="邮件检查间隔（秒）")
    EMAIL_MARK_AS_READ: bool = Field(default=True, description="处理后是否标记为已读")
    
    # 附件限制配置
    EMAIL_MAX_ATTACHMENT_SIZE: int = Field(default=10 * 1024 * 1024, description="单个附件最大大小（字节）")
    EMAIL_MAX_ATTACHMENT_COUNT: int = Field(default=5, description="每封邮件最大附件数量")
    EMAIL_ALLOWED_EXTENSIONS: Union[str, List[str]] = Field(
        default=".pdf,.doc,.docx,.txt,.md,.zip,.rar",
        description="允许的附件扩展名"
    )
    
    # 频率限制配置
    EMAIL_HOURLY_LIMIT: int = Field(default=5, description="每小时邮件发送限制")
    EMAIL_DAILY_LIMIT: int = Field(default=20, description="每天邮件发送限制")
    
    # 域名限制配置
    EMAIL_DOMAIN_WHITELIST_ENABLED: bool = Field(default=False, description="是否启用域名白名单")
    EMAIL_ALLOWED_DOMAINS: Union[str, List[str]] = Field(
        default="gmail.com,outlook.com,qq.com,163.com",
        description="允许的邮件域名"
    )
    
    # 兼容旧的环境变量名
    ALLOWED_EMAIL_DOMAINS: Union[str, List[str]] = Field(
        default="gmail.com,outlook.com,qq.com,163.com",
        description="允许的邮件域名（兼容字段）"
    )
    MAX_EMAIL_ATTACHMENTS: int = Field(default=5, description="每封邮件最大附件数量（兼容字段）")
    MAX_ATTACHMENT_SIZE: int = Field(default=10 * 1024 * 1024, description="单个附件最大大小（兼容字段）")
    EMAIL_RATE_LIMIT_HOURLY: int = Field(default=5, description="每小时邮件发送限制（兼容字段）")
    EMAIL_RATE_LIMIT_DAILY: int = Field(default=20, description="每天邮件发送限制（兼容字段）")
    
    # Redis配置（用于频率限制）
    REDIS_URL: Optional[str] = Field(default=None, description="Redis连接URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_DB: int = Field(default=0, description="Redis数据库")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default=None)
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """解析允许的主机列表"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, v):
        """解析允许的文件类型列表"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def set_jwt_secret_key(cls, v, info):
        """设置JWT密钥，如果未提供则使用SECRET_KEY"""
        if not v and info.data:
            return info.data.get("SECRET_KEY", "")
        return v
    
    @field_validator("EMAIL_ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_email_allowed_extensions(cls, v):
        """解析允许的邮件附件扩展名列表"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @field_validator("EMAIL_ALLOWED_DOMAINS", mode="before")
    @classmethod
    def parse_email_allowed_domains(cls, v):
        """解析允许的邮件域名列表"""
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(",")]
        return v
    
    # Redis启用标志
    REDIS_ENABLED: bool = Field(default=True, description="是否启用Redis")
    
    # 移除了Celery相关的验证器，因为我们不再使用Celery
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # 允许额外的字段


# 创建设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)