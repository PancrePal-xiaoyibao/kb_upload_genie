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
    
    # 邮件配置
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_TLS: bool = Field(default=True)
    
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
    
    # 移除了Celery相关的验证器，因为我们不再使用Celery
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)