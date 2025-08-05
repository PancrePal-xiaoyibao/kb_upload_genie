"""
数据模型
包含所有数据库模型定义
"""

from .article import Article, ArticleStatus, CopyrightStatus as ArticleCopyrightStatus, FileType
from .category import Category
from .user import User, UserRole
from .review import Review, ReviewType, ReviewStatus, ReviewCategory
from .copyright_record import CopyrightRecord, CopyrightStatus, CopyrightSource, SimilarityLevel
from .email_upload import (
    EmailUpload, 
    EmailUploadStatus, 
    EmailRateLimit, 
    EmailDomainRule, 
    EmailConfig, 
    AttachmentRule
)
from .simple_email_upload import SimpleEmailUpload

__all__ = [
    "User",
    "UserRole", 
    "Category",
    "Article",
    "ArticleStatus",
    "ArticleCopyrightStatus",
    "FileType",
    "Review",
    "ReviewType",
    "ReviewStatus", 
    "ReviewCategory",
    "CopyrightRecord",
    "CopyrightStatus",
    "CopyrightSource",
    "SimilarityLevel",
    "EmailUpload",
    "EmailUploadStatus",
    "EmailRateLimit",
    "EmailDomainRule",
    "EmailConfig",
    "AttachmentRule",
    "SimpleEmailUpload",
]
