"""
审核记录数据模型
包含AI审核和人工审核的记录管理
"""

from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
import enum

from app.core.database import Base


class ReviewType(str, enum.Enum):
    """审核类型枚举"""
    AI = "ai"           # AI审核
    HUMAN = "human"     # 人工审核
    SYSTEM = "system"   # 系统审核


class ReviewStatus(str, enum.Enum):
    """审核状态枚举"""
    PENDING = "pending"     # 待审核
    APPROVED = "approved"   # 通过
    REJECTED = "rejected"   # 拒绝
    NEEDS_REVISION = "needs_revision"  # 需要修改


class ReviewCategory(str, enum.Enum):
    """审核分类枚举"""
    CONTENT_QUALITY = "content_quality"    # 内容质量
    COPYRIGHT = "copyright"                 # 版权检查
    CLASSIFICATION = "classification"       # 分类审核
    COMPLIANCE = "compliance"               # 合规性检查
    TECHNICAL = "technical"                 # 技术审核


class Review(Base):
    """审核记录表模型"""
    
    __tablename__ = "reviews"
    __table_args__ = {"comment": "审核记录表"}
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, comment="审核记录ID")
    
    # 关联关系
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True,
        comment="文章ID"
    )
    reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="审核员ID"
    )
    
    # 审核基本信息
    review_type: Mapped[ReviewType] = mapped_column(
        SQLEnum(ReviewType),
        comment="审核类型"
    )
    review_category: Mapped[ReviewCategory] = mapped_column(
        SQLEnum(ReviewCategory),
        comment="审核分类"
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus),
        default=ReviewStatus.PENDING,
        comment="审核状态"
    )
    
    # 审核结果
    score: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="审核评分(0-100)"
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="置信度(0.0-1.0)"
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="审核意见"
    )
    
    # AI审核特有字段
    ai_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="AI模型名称"
    )
    ai_model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="AI模型版本"
    )
    ai_response_time: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="AI响应时间(秒)"
    )
    ai_raw_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="AI原始响应"
    )
    
    # 审核详情
    issues_found: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="发现的问题"
    )
    suggestions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="改进建议"
    )
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="审核标签"
    )
    
    # 审核流程
    is_final: Mapped[bool] = mapped_column(
        default=False,
        comment="是否为最终审核"
    )
    requires_human_review: Mapped[bool] = mapped_column(
        default=False,
        comment="是否需要人工审核"
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="优先级(0-10)"
    )
    
    # 审核时间
    started_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="开始审核时间"
    )
    completed_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="完成审核时间"
    )
    
    # 关联关系
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="reviews"
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reviews"
    )
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, article_id={self.article_id}, type='{self.review_type}', status='{self.status}')>"
    
    @property
    def is_ai_review(self) -> bool:
        """检查是否为AI审核"""
        return self.review_type == ReviewType.AI
    
    @property
    def is_human_review(self) -> bool:
        """检查是否为人工审核"""
        return self.review_type == ReviewType.HUMAN
    
    @property
    def is_completed(self) -> bool:
        """检查审核是否完成"""
        return self.status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED)
    
    @property
    def is_passed(self) -> bool:
        """检查审核是否通过"""
        return self.status == ReviewStatus.APPROVED
    
    @property
    def has_high_confidence(self) -> bool:
        """检查是否高置信度"""
        return self.confidence is not None and self.confidence >= 0.8
    
    def get_issue_summary(self) -> str:
        """获取问题摘要"""
        if not self.issues_found:
            return "无问题"
        
        issues = self.issues_found.get("issues", [])
        if not issues:
            return "无问题"
        
        return f"发现 {len(issues)} 个问题"