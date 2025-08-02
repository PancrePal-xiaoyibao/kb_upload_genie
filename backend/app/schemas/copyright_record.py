"""
版权记录相关的数据模式
定义版权记录相关的Pydantic模型，用于API请求和响应
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.copyright_record import CopyrightStatus, CopyrightSource, SimilarityLevel


class CopyrightRecordBase(BaseModel):
    """版权记录基础模式"""
    article_id: int = Field(..., description="文章ID")
    source_url: Optional[str] = Field(None, description="来源URL")
    source_title: Optional[str] = Field(None, description="来源标题")
    source_author: Optional[str] = Field(None, description="来源作者")
    similarity_score: Optional[float] = Field(None, ge=0, le=1, description="相似度分数")
    similarity_level: Optional[SimilarityLevel] = Field(None, description="相似度等级")
    copyright_source: Optional[CopyrightSource] = Field(None, description="版权来源")


class CopyrightRecordCreate(CopyrightRecordBase):
    """创建版权记录模式"""
    pass


class CopyrightRecordUpdate(BaseModel):
    """更新版权记录模式"""
    status: Optional[CopyrightStatus] = Field(None, description="版权状态")
    source_url: Optional[str] = Field(None, description="来源URL")
    source_title: Optional[str] = Field(None, description="来源标题")
    source_author: Optional[str] = Field(None, description="来源作者")
    similarity_score: Optional[float] = Field(None, ge=0, le=1, description="相似度分数")
    similarity_level: Optional[SimilarityLevel] = Field(None, description="相似度等级")
    copyright_source: Optional[CopyrightSource] = Field(None, description="版权来源")
    matched_content: Optional[str] = Field(None, description="匹配内容")
    similarity_details: Optional[Dict[str, Any]] = Field(None, description="相似度详情")
    check_details: Optional[Dict[str, Any]] = Field(None, description="检查详情")
    resolution_notes: Optional[str] = Field(None, description="解决说明")


class CopyrightRecordInDB(CopyrightRecordBase):
    """数据库中的版权记录模式"""
    id: int
    status: CopyrightStatus
    matched_content: Optional[str] = None
    matched_length: Optional[int] = None
    total_matches: Optional[int] = None
    similarity_details: Optional[Dict[str, Any]] = None
    check_method: Optional[str] = None
    check_tool: Optional[str] = None
    check_version: Optional[str] = None
    check_details: Optional[Dict[str, Any]] = None
    false_positive: bool = False
    verified_by_human: bool = False
    resolution_status: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[str] = None
    check_requested_by: Optional[int] = None
    check_requested_at: Optional[str] = None
    last_checked_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CopyrightRecord(CopyrightRecordInDB):
    """版权记录响应模式"""
    pass


class CopyrightRecordList(BaseModel):
    """版权记录列表模式"""
    id: int
    article_id: int
    status: CopyrightStatus
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    similarity_score: Optional[float] = None
    similarity_level: Optional[SimilarityLevel] = None
    copyright_source: Optional[CopyrightSource] = None
    false_positive: bool = False
    verified_by_human: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CopyrightRecordDetail(CopyrightRecordInDB):
    """版权记录详情模式"""
    # 关联数据
    article: Optional[Dict[str, Any]] = None
    resolver: Optional[Dict[str, Any]] = None
    requester: Optional[Dict[str, Any]] = None
    
    # 计算属性
    has_copyright_issues: bool = False
    risk_level: str = ""
    similarity_description: str = ""

    class Config:
        from_attributes = True


class CopyrightStats(BaseModel):
    """版权统计模式"""
    total_records: int = 0
    clear_records: int = 0
    suspected_records: int = 0
    confirmed_records: int = 0
    resolved_records: int = 0
    false_positive_records: int = 0
    average_similarity_score: float = 0.0
    status_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    similarity_level_counts: Dict[str, int] = {}


class CopyrightSearch(BaseModel):
    """版权记录搜索模式"""
    article_id: Optional[int] = Field(None, description="文章ID")
    status: Optional[CopyrightStatus] = Field(None, description="版权状态")
    copyright_source: Optional[CopyrightSource] = Field(None, description="版权来源")
    similarity_level: Optional[SimilarityLevel] = Field(None, description="相似度等级")
    min_similarity: Optional[float] = Field(None, ge=0, le=1, description="最小相似度")
    max_similarity: Optional[float] = Field(None, ge=0, le=1, description="最大相似度")
    false_positive: Optional[bool] = Field(None, description="是否误报")
    verified_by_human: Optional[bool] = Field(None, description="是否人工验证")
    source_url: Optional[str] = Field(None, description="来源URL")
    source_author: Optional[str] = Field(None, description="来源作者")
    date_from: Optional[str] = Field(None, description="开始日期")
    date_to: Optional[str] = Field(None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")


class CopyrightCheck(BaseModel):
    """版权检查模式"""
    article_id: int = Field(..., description="文章ID")
    check_method: Optional[str] = Field(None, description="检查方法")
    force_recheck: bool = Field(default=False, description="是否强制重新检查")
    check_external: bool = Field(default=True, description="是否检查外部来源")
    check_internal: bool = Field(default=True, description="是否检查内部来源")


class CopyrightCheckResult(BaseModel):
    """版权检查结果模式"""
    success: bool
    message: str
    article_id: int
    records_found: int = 0
    highest_similarity: float = 0.0
    status: CopyrightStatus
    records: List[CopyrightRecordList] = []
    errors: Optional[List[str]] = None


class CopyrightBatch(BaseModel):
    """批量版权操作模式"""
    record_ids: List[int] = Field(..., min_items=1, max_items=50, description="记录ID列表")
    action: str = Field(..., description="操作类型")
    status: Optional[CopyrightStatus] = Field(None, description="新状态")
    false_positive: Optional[bool] = Field(None, description="是否标记为误报")
    resolution_notes: Optional[str] = Field(None, description="解决说明")


class CopyrightBatchResult(BaseModel):
    """批量版权操作结果模式"""
    success_count: int = 0
    failed_count: int = 0
    results: List[Dict[str, Any]] = []
    errors: List[str] = []