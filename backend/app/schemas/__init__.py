"""
数据模式包
定义所有API相关的Pydantic数据模式
"""
from .user import (
    User, UserCreate, UserUpdate, UserPasswordUpdate,
    UserLogin, UserProfile, UserStats, UserInDB
)
from .category import (
    Category, CategoryCreate, CategoryUpdate, CategoryWithChildren,
    CategoryWithParent, CategoryTree, CategoryStats, CategoryMove, CategorySearch
)
from .article import (
    Article, ArticleCreate, ArticleUpdate, ArticleInDB, ArticleDetail,
    ArticleList, ArticleSearch, ArticleStats, ArticleSync, ArticleSyncResult,
    ArticleBatch, ArticleBatchResult
)
from .review import (
    Review, ReviewCreate, ReviewUpdate, ReviewInDB, ReviewDetail,
    ReviewList, ReviewSearch, ReviewStats, ReviewAssign,
    ReviewBatch, ReviewBatchResult
)
from .copyright_record import (
    CopyrightRecord, CopyrightRecordCreate, CopyrightRecordUpdate, CopyrightRecordInDB,
    CopyrightRecordDetail, CopyrightRecordList, CopyrightSearch, CopyrightStats,
    CopyrightCheck, CopyrightCheckResult, CopyrightBatch, CopyrightBatchResult
)

__all__ = [
    # User schemas
    "User", "UserCreate", "UserUpdate", "UserPasswordUpdate",
    "UserLogin", "UserProfile", "UserStats", "UserInDB",
    
    # Category schemas
    "Category", "CategoryCreate", "CategoryUpdate", "CategoryWithChildren",
    "CategoryWithParent", "CategoryTree", "CategoryStats", "CategoryMove", "CategorySearch",
    
    # Article schemas
    "Article", "ArticleCreate", "ArticleUpdate", "ArticleInDB", "ArticleDetail",
    "ArticleList", "ArticleSearch", "ArticleStats", "ArticleSync", "ArticleSyncResult",
    "ArticleBatch", "ArticleBatchResult",
    
    # Review schemas
    "Review", "ReviewCreate", "ReviewUpdate", "ReviewInDB", "ReviewDetail",
    "ReviewList", "ReviewSearch", "ReviewStats", "ReviewAssign",
    "ReviewBatch", "ReviewBatchResult",
    
    # Copyright Record schemas
    "CopyrightRecord", "CopyrightRecordCreate", "CopyrightRecordUpdate", "CopyrightRecordInDB",
    "CopyrightRecordDetail", "CopyrightRecordList", "CopyrightSearch", "CopyrightStats",
    "CopyrightCheck", "CopyrightCheckResult", "CopyrightBatch", "CopyrightBatchResult"
]