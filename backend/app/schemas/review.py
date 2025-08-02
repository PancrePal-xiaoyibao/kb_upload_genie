"""
审核相关的数据模式
定义审核相关的Pydantic模型，用于API请求和响应
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.review import ReviewType, ReviewStatus, ReviewCategory


class ReviewBase(BaseModel):
    """审核基础模式"""
    article_id: int = Field(..., description="文章ID")
    review_type: ReviewType = Field(..., description="审核类型")
    review_category: ReviewCategory = Field(..., description="审核分类")
    comments: Optional[str] = Field(None, description="审核意见")
    score: Optional[float] = Field(None, ge=0, le=100, description="审核评分")
    priority: int = Field(default=1, ge=1, le=5, description="优先级")


class ReviewCreate(ReviewBase):
    """创建审核模式"""
    pass


class ReviewUpdate(BaseModel):
    """更新审核模式"""
    status: Optional[ReviewStatus] = Field(None, description="审核状态")
    comments: Optional[str] = Field(None, description="审核意见")
    score: Optional[float] = Field(None, ge=0, le=100, description="审核评分")
    priority: Optional[int] = Field(None, ge=1, le=5, description="优先级")
    ai_confidence: Optional[float] = Field(None, ge=0, le=1, description="AI置信度")
    ai_suggestions: Optional[List[str]] = Field(None, description="AI建议")
    review_details: Optional[Dict[str, Any]] = Field(None, description="审核详情")


class ReviewInDB(ReviewBase):
    """数据库中的审核模式"""
    id: int
    reviewer_id: Optional[int] = None
    status: ReviewStatus
    ai_confidence: Optional[float] = None
    ai_suggestions: Optional[List[str]] = None
    review_details: Optional[Dict[str, Any]] = None
    workflow_step: Optional[str] = None
    escalation_level: int = 0
    auto_approved: bool = False
    requires_human_review: bool = False
    review_deadline: Optional[str] = None
    assigned_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Review(ReviewInDB):
    """审核响应模式"""
    pass


class ReviewList(BaseModel):
    """审核列表模式"""
    id: int
    article_id: int
    review_type: ReviewType
    review_category: ReviewCategory
    status: ReviewStatus
    score: Optional[float] = None
    priority: int
    reviewer_id: Optional[int] = None
    auto_approved: bool = False
    requires_human_review: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewDetail(ReviewInDB):
    """审核详情模式"""
    # 关联数据
    article: Optional[Dict[str, Any]] = None
    reviewer: Optional[Dict[str, Any]] = None
    
    # 计算属性
    is_pending: bool = False
    is_completed: bool = False
    is_overdue: bool = False
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class ReviewStats(BaseModel):
    """审核统计模式"""
    total_reviews: int = 0
    pending_reviews: int = 0
    completed_reviews: int = 0
    approved_reviews: int = 0
    rejected_reviews: int = 0
    auto_approved_reviews: int = 0
    average_score: float = 0.0
    average_duration_hours: float = 0.0
    review_types_count: Dict[str, int] = {}
    review_categories_count: Dict[str, int] = {}


class ReviewSearch(BaseModel):
    """审核搜索模式"""
    article_id: Optional[int] = Field(None, description="文章ID")
    reviewer_id: Optional[int] = Field(None, description="审核员ID")
    review_type: Optional[ReviewType] = Field(None, description="审核类型")
    review_category: Optional[ReviewCategory] = Field(None, description="审核分类")
    status: Optional[ReviewStatus] = Field(None, description="审核状态")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="最小评分")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="最大评分")
    priority: Optional[int] = Field(None, ge=1, le=5, description="优先级")
    auto_approved: Optional[bool] = Field(None, description="是否自动审核")
    requires_human_review: Optional[bool] = Field(None, description="是否需要人工审核")
    date_from: Optional[str] = Field(None, description="开始日期")
    date_to: Optional[str] = Field(None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")


class ReviewAssign(BaseModel):
    """审核分配模式"""
    review_ids: List[int] = Field(..., min_items=1, description="审核ID列表")
    reviewer_id: int = Field(..., description="审核员ID")
    deadline: Optional[str] = Field(None, description="截止时间")
    priority: Optional[int] = Field(None, ge=1, le=5, description="优先级")


class ReviewBatch(BaseModel):
    """批量审核模式"""
    review_ids: List[int] = Field(..., min_items=1, max_items=50, description="审核ID列表")
    action: str = Field(..., description="操作类型")
    status: Optional[ReviewStatus] = Field(None, description="新状态")
    comments: Optional[str] = Field(None, description="批量意见")
    score: Optional[float] = Field(None, ge=0, le=100, description="批量评分")


class ReviewBatchResult(BaseModel):
    """批量审核结果模式"""
    success_count: int = 0
    failed_count: int = 0
    results: List[Dict[str, Any]] = []
    errors: List[str] = []