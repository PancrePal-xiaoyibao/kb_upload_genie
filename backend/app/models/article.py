"""
文章数据模型
管理GitHub仓库文章的存储和分类
"""

from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List
import enum

from app.core.database import Base


class ArticleStatus(str, enum.Enum):
    """文章状态枚举"""
    DRAFT = "draft"             # 草稿
    PENDING = "pending"         # 待审核
    PUBLISHED = "published"     # 已发布
    REJECTED = "rejected"       # 已拒绝
    ARCHIVED = "archived"       # 已归档
    DELETED = "deleted"         # 已删除


class CopyrightStatus(str, enum.Enum):
    """版权状态枚举"""
    UNKNOWN = "unknown"         # 未知
    CLEAR = "clear"            # 无版权问题
    CHECKING = "checking"       # 检查中
    SUSPECTED = "suspected"     # 疑似侵权
    CONFIRMED = "confirmed"     # 确认侵权
    RESOLVED = "resolved"       # 已解决


class FileType(str, enum.Enum):
    """文件类型枚举"""
    MARKDOWN = "markdown"       # Markdown文件
    JUPYTER = "jupyter"         # Jupyter Notebook
    CODE = "code"              # 代码文件
    DOCUMENTATION = "documentation"  # 文档
    README = "readme"          # README文件
    OTHER = "other"            # 其他类型


class UploadMethod(str, enum.Enum):
    """上传方法枚举"""
    GITHUB_DIRECT = "github_direct"    # 直接GitHub上传
    EMAIL_UPLOAD = "email_upload"      # 邮件上传
    SIMPLE_EMAIL = "simple_email"      # 简单邮件上传
    WEB_UPLOAD = "web_upload"          # 网页上传
    API_UPLOAD = "api_upload"          # API上传
    BATCH_IMPORT = "batch_import"      # 批量导入


class ProcessingStatus(str, enum.Enum):
    """处理状态枚举"""
    PENDING = "pending"         # 待处理
    PROCESSING = "processing"   # 处理中
    COMPLETED = "completed"     # 已完成
    REJECTED = "rejected"       # 已拒绝


class Article(Base):
    """文章表模型"""
    
    __tablename__ = "articles"
    __table_args__ = {"comment": "文章表"}
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, comment="文章ID")
    
    # 基本信息
    title: Mapped[str] = mapped_column(
        String(200),
        index=True,
        comment="文章标题"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="文章描述"
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="文章内容"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="文章摘要"
    )
    
    # GitHub信息
    github_url: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        comment="GitHub仓库URL"
    )
    github_owner: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="GitHub仓库所有者"
    )
    github_repo: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="GitHub仓库名称"
    )
    github_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="GitHub文件路径"
    )
    github_branch: Mapped[str] = mapped_column(
        String(100),
        default="main",
        comment="GitHub分支"
    )
    github_commit: Mapped[Optional[str]] = mapped_column(
        String(40),
        comment="GitHub提交哈希"
    )
    
    # 文件信息
    file_type: Mapped[FileType] = mapped_column(
        SQLEnum(FileType),
        comment="文件类型"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="文件大小(字节)"
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="编程语言"
    )
    
    # 关联关系
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="用户ID"
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
        comment="分类ID"
    )
    
    # 状态信息
    status: Mapped[ArticleStatus] = mapped_column(
        SQLEnum(ArticleStatus),
        default=ArticleStatus.PENDING,
        index=True,
        comment="文章状态"
    )
    copyright_status: Mapped[CopyrightStatus] = mapped_column(
        SQLEnum(CopyrightStatus),
        default=CopyrightStatus.UNKNOWN,
        index=True,
        comment="版权状态"
    )
    
    # 上传跟踪信息
    method: Mapped[Optional[UploadMethod]] = mapped_column(
        SQLEnum(UploadMethod),
        default=UploadMethod.GITHUB_DIRECT,
        index=True,
        comment="上传方法"
    )
    tracker_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        unique=True,
        index=True,
        comment="跟踪ID"
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        index=True,
        comment="处理状态"
    )
    
    # 统计信息
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="浏览次数"
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="下载次数"
    )
    star_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="GitHub星标数"
    )
    fork_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="GitHub分叉数"
    )
    
    # 标签和元数据
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="标签列表"
    )
    keywords: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="关键词列表"
    )
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="额外元数据"
    )
    
    # AI分析结果
    ai_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="AI分析结果"
    )
    ai_tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="AI生成的标签"
    )
    ai_category_suggestion: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="AI推荐分类"
    )
    
    # 同步信息
    last_sync_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="最后同步时间"
    )
    sync_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="同步状态"
    )
    auto_sync: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否自动同步"
    )
    
    # 发布信息
    published_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="发布时间"
    )
    featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否推荐"
    )
    
    # 关联关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="articles"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="articles"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="article",
        cascade="all, delete-orphan"
    )
    copyright_records: Mapped[List["CopyrightRecord"]] = relationship(
        "CopyrightRecord",
        back_populates="article",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def is_published(self) -> bool:
        """检查文章是否已发布"""
        return self.status == ArticleStatus.PUBLISHED
    
    @property
    def is_pending(self) -> bool:
        """检查文章是否待审核"""
        return self.status == ArticleStatus.PENDING
    
    @property
    def has_copyright_issues(self) -> bool:
        """检查是否有版权问题"""
        return self.copyright_status in (
            CopyrightStatus.SUSPECTED,
            CopyrightStatus.CONFIRMED
        )
    
    @property
    def github_full_name(self) -> str:
        """获取GitHub仓库全名"""
        return f"{self.github_owner}/{self.github_repo}"
    
    @property
    def github_file_url(self) -> str:
        """获取GitHub文件URL"""
        if self.github_path:
            return f"https://github.com/{self.github_owner}/{self.github_repo}/blob/{self.github_branch}/{self.github_path}"
        return self.github_url
    
    @property
    def is_popular(self) -> bool:
        """检查是否为热门文章"""
        return self.view_count > 100 or self.download_count > 50 or self.star_count > 10
    
    @property
    def engagement_score(self) -> float:
        """计算参与度分数"""
        return (self.view_count * 0.1 + 
                self.download_count * 0.5 + 
                self.star_count * 2.0 + 
                self.fork_count * 3.0)
    
    def get_display_tags(self) -> List[str]:
        """获取显示标签（合并用户标签和AI标签）"""
        display_tags = []
        if self.tags:
            display_tags.extend(self.tags)
        if self.ai_tags:
            # 添加AI标签，但避免重复
            for tag in self.ai_tags:
                if tag not in display_tags:
                    display_tags.append(tag)
        return display_tags[:10]  # 最多显示10个标签
    
    def update_stats(self, views: int = 0, downloads: int = 0, stars: int = 0, forks: int = 0):
        """更新统计信息"""
        if views > 0:
            self.view_count += views
        if downloads > 0:
            self.download_count += downloads
        if stars >= 0:
            self.star_count = stars
        if forks >= 0:
            self.fork_count = forks