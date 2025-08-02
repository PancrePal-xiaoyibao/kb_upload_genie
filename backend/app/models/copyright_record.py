"""
版权记录数据模型
用于记录版权检查和相似度分析结果
"""

from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum, JSON, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List
import enum

from app.core.database import Base


class CopyrightStatus(str, enum.Enum):
    """版权状态枚举"""
    CLEAN = "clean"                 # 无版权问题
    SUSPICIOUS = "suspicious"       # 疑似侵权
    VIOLATION = "violation"         # 确认侵权
    PENDING = "pending"             # 待检查
    MANUAL_REVIEW = "manual_review" # 需人工审核


class CopyrightSource(str, enum.Enum):
    """版权来源枚举"""
    GITHUB = "github"               # GitHub仓库
    STACKOVERFLOW = "stackoverflow" # Stack Overflow
    BLOG = "blog"                   # 博客文章
    DOCUMENTATION = "documentation" # 官方文档
    TUTORIAL = "tutorial"           # 教程网站
    FORUM = "forum"                 # 论坛
    OTHER = "other"                 # 其他来源


class SimilarityLevel(str, enum.Enum):
    """相似度等级枚举"""
    LOW = "low"         # 低相似度 (0-30%)
    MEDIUM = "medium"   # 中等相似度 (30-70%)
    HIGH = "high"       # 高相似度 (70-90%)
    VERY_HIGH = "very_high"  # 极高相似度 (90%+)


class CopyrightRecord(Base):
    """版权记录表模型"""
    
    __tablename__ = "copyright_records"
    __table_args__ = {"comment": "版权检查记录表"}
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, comment="版权记录ID")
    
    # 关联关系
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True,
        comment="文章ID"
    )
    
    # 版权检查基本信息
    status: Mapped[CopyrightStatus] = mapped_column(
        SQLEnum(CopyrightStatus),
        default=CopyrightStatus.PENDING,
        comment="版权状态"
    )
    check_method: Mapped[str] = mapped_column(
        String(100),
        comment="检查方法(AI模型、工具等)"
    )
    check_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="检查工具版本"
    )
    
    # 相似内容信息
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="原始来源URL"
    )
    source_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="原始来源标题"
    )
    source_type: Mapped[Optional[CopyrightSource]] = mapped_column(
        SQLEnum(CopyrightSource),
        comment="来源类型"
    )
    source_author: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="原始作者"
    )
    source_license: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="原始许可证"
    )
    
    # 相似度分析
    similarity_score: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="相似度分数(0.0-1.0)"
    )
    similarity_level: Mapped[Optional[SimilarityLevel]] = mapped_column(
        SQLEnum(SimilarityLevel),
        comment="相似度等级"
    )
    matched_content: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="匹配的内容片段"
    )
    matched_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="匹配百分比"
    )
    
    # 检查详情
    analysis_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="详细分析结果"
    )
    matched_sections: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        comment="匹配的代码段"
    )
    risk_factors: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="风险因素"
    )
    
    # 处理信息
    is_false_positive: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否为误报"
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否已解决"
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="解决方案说明"
    )
    
    # 审核信息
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="审核员ID"
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="审核备注"
    )
    
    # 检查时间
    checked_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="检查时间"
    )
    last_updated: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="最后更新时间"
    )
    
    # 关联关系
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="copyright_records"
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewed_by]
    )
    
    def __repr__(self) -> str:
        return f"<CopyrightRecord(id={self.id}, article_id={self.article_id}, status='{self.status}', similarity={self.similarity_score})>"
    
    @property
    def has_copyright_issues(self) -> bool:
        """检查是否有版权问题"""
        return self.status in (CopyrightStatus.SUSPICIOUS, CopyrightStatus.VIOLATION)
    
    @property
    def is_high_risk(self) -> bool:
        """检查是否为高风险"""
        return (
            self.similarity_score is not None and self.similarity_score >= 0.7
        ) or self.status == CopyrightStatus.VIOLATION
    
    @property
    def needs_review(self) -> bool:
        """检查是否需要人工审核"""
        return self.status == CopyrightStatus.MANUAL_REVIEW or (
            self.similarity_score is not None and 
            self.similarity_score >= 0.5 and 
            not self.is_resolved
        )
    
    @property
    def risk_level(self) -> str:
        """获取风险等级"""
        if self.status == CopyrightStatus.VIOLATION:
            return "critical"
        elif self.status == CopyrightStatus.SUSPICIOUS:
            return "high"
        elif self.similarity_score and self.similarity_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def get_similarity_description(self) -> str:
        """获取相似度描述"""
        if not self.similarity_score:
            return "未检测"
        
        score = self.similarity_score * 100
        if score >= 90:
            return f"极高相似度 ({score:.1f}%)"
        elif score >= 70:
            return f"高相似度 ({score:.1f}%)"
        elif score >= 30:
            return f"中等相似度 ({score:.1f}%)"
        else:
            return f"低相似度 ({score:.1f}%)"
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要"""
        return {
            "status": self.status.value,
            "risk_level": self.risk_level,
            "similarity_score": self.similarity_score,
            "similarity_description": self.get_similarity_description(),
            "has_issues": self.has_copyright_issues,
            "needs_review": self.needs_review,
            "is_resolved": self.is_resolved,
            "source_url": self.source_url,
            "source_type": self.source_type.value if self.source_type else None
        }