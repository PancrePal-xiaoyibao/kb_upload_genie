"""CRUD操作包
包含所有数据库操作的CRUD类
"""

from .base import CRUDBase
from .user import CRUDUser, user
from .category import CRUDCategory, category
from .article import CRUDArticle, article
from .review import CRUDReview, review
from .copyright_record import CRUDCopyrightRecord, copyright_record

__all__ = [
    "CRUDBase",
    "CRUDUser", "user",
    "CRUDCategory", "category",
    "CRUDArticle", "article",
    "CRUDReview", "review",
    "CRUDCopyrightRecord", "copyright_record"
]