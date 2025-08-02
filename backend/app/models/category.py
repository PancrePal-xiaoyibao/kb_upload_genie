"""
分类数据模型
支持树形结构的分类管理，与GitHub目录结构同步
"""

from sqlalchemy import String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from app.core.database import Base


class Category(Base):
    """分类表模型"""
    
    __tablename__ = "categories"
    __table_args__ = {"comment": "分类表"}
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, comment="分类ID")
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        comment="分类名称"
    )
    path: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        comment="分类路径"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="分类描述"
    )
    
    # 树形结构
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        comment="父分类ID"
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="分类层级"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序顺序"
    )
    
    # GitHub集成
    github_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="GitHub目录路径"
    )
    github_repo: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="GitHub仓库名"
    )
    
    # 状态和配置
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    is_auto_sync: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否自动同步GitHub"
    )
    
    # AI分类配置
    ai_keywords: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="AI分类关键词"
    )
    ai_description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="AI分类描述"
    )
    
    # 统计信息
    article_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="文章数量"
    )
    
    # 关联关系
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    articles: Mapped[List["Article"]] = relationship(
        "Article",
        back_populates="category"
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', path='{self.path}')>"
    
    @property
    def full_path(self) -> str:
        """获取完整路径"""
        if self.parent:
            return f"{self.parent.full_path}/{self.name}"
        return self.name
    
    @property
    def is_root(self) -> bool:
        """检查是否为根分类"""
        return self.parent_id is None
    
    @property
    def is_leaf(self) -> bool:
        """检查是否为叶子分类"""
        return len(self.children) == 0
    
    def get_all_children(self) -> List["Category"]:
        """获取所有子分类（递归）"""
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_all_children())
        return all_children
    
    def get_ancestors(self) -> List["Category"]:
        """获取所有祖先分类"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors[::-1]  # 反转，从根到父级