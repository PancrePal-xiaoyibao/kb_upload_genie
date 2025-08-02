"""
文章相关的数据模式
定义文章相关的Pydantic模型，用于API请求和响应
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.models.article import ArticleStatus, CopyrightStatus, FileType


class ArticleBase(BaseModel):
    """文章基础模式"""
    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    description: Optional[str] = Field(None, description="文章描述")
    github_url: str = Field(..., description="GitHub仓库URL")
    github_owner: str = Field(..., min_length=1, max_length=100, description="GitHub仓库所有者")
    github_repo: str = Field(..., min_length=1, max_length=100, description="GitHub仓库名称")
    github_path: Optional[str] = Field(None, max_length=500, description="GitHub文件路径")
    github_branch: str = Field(default="main", max_length=100, description="GitHub分支")
    file_type: FileType = Field(..., description="文件类型")
    language: Optional[str] = Field(None, max_length=50, description="编程语言")
    category_id: Optional[int] = Field(None, description="分类ID")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    keywords: Optional[List[str]] = Field(default=[], description="关键词列表")
    auto_sync: bool = Field(default=True, description="是否自动同步")

    @validator('tags', 'keywords')
    def validate_lists(cls, v):
        """验证列表字段"""
        if v is None:
            return []
        if len(v) > 20:
            raise ValueError("标签或关键词数量不能超过20个")
        return v

    @validator('github_url')
    def validate_github_url(cls, v):
        """验证GitHub URL格式"""
        if not v.startswith('https://github.com/'):
            raise ValueError("必须是有效的GitHub URL")
        return v


class ArticleCreate(ArticleBase):
    """创建文章模式"""
    pass


class ArticleUpdate(BaseModel):
    """更新文章模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="文章标题")
    description: Optional[str] = Field(None, description="文章描述")
    category_id: Optional[int] = Field(None, description="分类ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    status: Optional[ArticleStatus] = Field(None, description="文章状态")
    featured: Optional[bool] = Field(None, description="是否推荐")
    auto_sync: Optional[bool] = Field(None, description="是否自动同步")

    @validator('tags', 'keywords')
    def validate_lists(cls, v):
        """验证列表字段"""
        if v is not None and len(v) > 20:
            raise ValueError("标签或关键词数量不能超过20个")
        return v


class ArticleInDB(ArticleBase):
    """数据库中的文章模式"""
    id: int
    user_id: int
    content: Optional[str] = None
    summary: Optional[str] = None
    github_commit: Optional[str] = None
    file_size: Optional[int] = None
    status: ArticleStatus
    copyright_status: CopyrightStatus
    view_count: int = 0
    download_count: int = 0
    star_count: int = 0
    fork_count: int = 0
    ai_analysis: Optional[Dict[str, Any]] = None
    ai_tags: Optional[List[str]] = None
    ai_category_suggestion: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    last_sync_at: Optional[str] = None
    sync_status: Optional[str] = None
    published_at: Optional[str] = None
    featured: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Article(ArticleInDB):
    """文章响应模式"""
    pass


class ArticleList(BaseModel):
    """文章列表模式"""
    id: int
    title: str
    description: Optional[str] = None
    github_owner: str
    github_repo: str
    file_type: FileType
    language: Optional[str] = None
    status: ArticleStatus
    copyright_status: CopyrightStatus
    view_count: int = 0
    download_count: int = 0
    star_count: int = 0
    fork_count: int = 0
    tags: Optional[List[str]] = None
    featured: bool = False
    published_at: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleDetail(ArticleInDB):
    """文章详情模式"""
    # 关联数据
    user: Optional[Dict[str, Any]] = None
    category: Optional[Dict[str, Any]] = None
    
    # 计算属性
    is_published: bool = False
    is_pending: bool = False
    has_copyright_issues: bool = False
    github_full_name: str = ""
    github_file_url: str = ""
    is_popular: bool = False
    engagement_score: float = 0.0
    display_tags: List[str] = []

    class Config:
        from_attributes = True


class ArticleSearch(BaseModel):
    """文章搜索模式"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category_id: Optional[int] = Field(None, description="分类ID")
    status: Optional[ArticleStatus] = Field(None, description="文章状态")
    copyright_status: Optional[CopyrightStatus] = Field(None, description="版权状态")
    file_type: Optional[FileType] = Field(None, description="文件类型")
    language: Optional[str] = Field(None, description="编程语言")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    featured: Optional[bool] = Field(None, description="是否推荐")
    user_id: Optional[int] = Field(None, description="用户ID")
    github_owner: Optional[str] = Field(None, description="GitHub所有者")
    min_stars: Optional[int] = Field(None, ge=0, description="最小星标数")
    min_views: Optional[int] = Field(None, ge=0, description="最小浏览数")
    date_from: Optional[str] = Field(None, description="开始日期")
    date_to: Optional[str] = Field(None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")


class ArticleStats(BaseModel):
    """文章统计模式"""
    total_articles: int = 0
    published_articles: int = 0
    pending_articles: int = 0
    draft_articles: int = 0
    total_views: int = 0
    total_downloads: int = 0
    popular_languages: List[Dict[str, Any]] = []
    popular_tags: List[Dict[str, Any]] = []
    recent_articles: List[ArticleList] = []


class ArticleSync(BaseModel):
    """文章同步模式"""
    github_url: str = Field(..., description="GitHub URL")
    force_update: bool = Field(default=False, description="是否强制更新")
    sync_content: bool = Field(default=True, description="是否同步内容")
    sync_metadata: bool = Field(default=True, description="是否同步元数据")


class ArticleSyncResult(BaseModel):
    """文章同步结果模式"""
    success: bool
    message: str
    article_id: Optional[int] = None
    changes: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class ArticleBatch(BaseModel):
    """批量操作模式"""
    article_ids: List[int] = Field(..., min_items=1, max_items=100, description="文章ID列表")
    action: str = Field(..., description="操作类型")
    params: Optional[Dict[str, Any]] = Field(None, description="操作参数")


class ArticleBatchResult(BaseModel):
    """批量操作结果模式"""
    success_count: int = 0
    failed_count: int = 0
    results: List[Dict[str, Any]] = []
    errors: List[str] = []