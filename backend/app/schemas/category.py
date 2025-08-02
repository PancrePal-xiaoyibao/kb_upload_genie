"""
分类相关的数据模式
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CategoryBase(BaseModel):
    """分类基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    slug: str = Field(..., min_length=1, max_length=100, description="分类标识符")
    description: Optional[str] = Field(None, description="分类描述")
    sort_order: Optional[int] = Field(0, description="排序顺序")
    github_path: Optional[str] = Field(None, max_length=500, description="GitHub路径")
    github_repo: Optional[str] = Field(None, max_length=200, description="GitHub仓库")
    is_active: bool = Field(True, description="是否激活")
    auto_sync: bool = Field(False, description="是否自动同步")
    ai_keywords: Optional[List[str]] = Field(None, description="AI关键词")
    ai_description: Optional[str] = Field(None, description="AI描述")


class CategoryCreate(CategoryBase):
    """创建分类模式"""
    parent_id: Optional[int] = Field(None, description="父分类ID")
    
    @validator('slug')
    def validate_slug(cls, v):
        """验证slug格式"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('slug只能包含字母、数字、连字符和下划线')
        return v.lower()


class CategoryUpdate(BaseModel):
    """更新分类模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    github_path: Optional[str] = Field(None, max_length=500)
    github_repo: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    auto_sync: Optional[bool] = None
    ai_keywords: Optional[List[str]] = None
    ai_description: Optional[str] = None
    
    @validator('slug')
    def validate_slug(cls, v):
        """验证slug格式"""
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('slug只能包含字母、数字、连字符和下划线')
        return v.lower() if v else v


class CategoryInDBBase(CategoryBase):
    """数据库分类基础模式"""
    id: int
    parent_id: Optional[int]
    level: int
    article_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Category(CategoryInDBBase):
    """分类响应模式"""
    pass


class CategoryWithChildren(Category):
    """包含子分类的分类模式"""
    children: List['CategoryWithChildren'] = []


class CategoryWithParent(Category):
    """包含父分类的分类模式"""
    parent: Optional['Category'] = None


class CategoryTree(BaseModel):
    """分类树模式"""
    category: Category
    children: List['CategoryTree'] = []
    depth: int = 0


class CategoryStats(BaseModel):
    """分类统计模式"""
    category: Category
    article_counts: Dict[str, int] = {}
    total_articles: int = 0
    children_count: int = 0
    is_leaf: bool = True


class CategoryMove(BaseModel):
    """移动分类模式"""
    category_id: int = Field(..., description="要移动的分类ID")
    new_parent_id: Optional[int] = Field(None, description="新的父分类ID")


class CategorySearch(BaseModel):
    """分类搜索模式"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    include_inactive: bool = Field(False, description="是否包含未激活的分类")


# 更新前向引用
CategoryWithChildren.model_rebuild()
CategoryTree.model_rebuild()