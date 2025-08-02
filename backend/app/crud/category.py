"""
分类相关的数据库操作
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    """分类CRUD操作类"""
    
    async def get_by_slug(self, db: AsyncSession, *, slug: str) -> Optional[Category]:
        """根据slug获取分类"""
        result = await db.execute(
            select(self.model).where(self.model.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_root_categories(self, db: AsyncSession) -> List[Category]:
        """获取根分类（没有父分类的分类）"""
        result = await db.execute(
            select(self.model)
            .where(self.model.parent_id.is_(None))
            .order_by(self.model.sort_order, self.model.name)
        )
        return result.scalars().all()
    
    async def get_children(self, db: AsyncSession, *, parent_id: int) -> List[Category]:
        """获取指定分类的子分类"""
        result = await db.execute(
            select(self.model)
            .where(self.model.parent_id == parent_id)
            .order_by(self.model.sort_order, self.model.name)
        )
        return result.scalars().all()
    
    async def get_tree(self, db: AsyncSession, *, parent_id: Optional[int] = None) -> List[Category]:
        """获取分类树结构"""
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.children))
            .where(self.model.parent_id == parent_id)
            .order_by(self.model.sort_order, self.model.name)
        )
        return result.scalars().all()
    
    async def get_by_level(self, db: AsyncSession, *, level: int) -> List[Category]:
        """获取指定层级的分类"""
        result = await db.execute(
            select(self.model)
            .where(self.model.level == level)
            .order_by(self.model.sort_order, self.model.name)
        )
        return result.scalars().all()
    
    async def get_active_categories(self, db: AsyncSession) -> List[Category]:
        """获取所有激活的分类"""
        result = await db.execute(
            select(self.model)
            .where(self.model.is_active == True)
            .order_by(self.model.level, self.model.sort_order, self.model.name)
        )
        return result.scalars().all()
    
    async def search_categories(
        self, 
        db: AsyncSession, 
        *, 
        keyword: str,
        include_inactive: bool = False
    ) -> List[Category]:
        """搜索分类"""
        query = select(self.model).where(
            or_(
                self.model.name.ilike(f"%{keyword}%"),
                self.model.description.ilike(f"%{keyword}%"),
                self.model.slug.ilike(f"%{keyword}%")
            )
        )
        
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        
        query = query.order_by(self.model.level, self.model.sort_order, self.model.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_github_path(self, db: AsyncSession, *, github_path: str) -> Optional[Category]:
        """根据GitHub路径获取分类"""
        result = await db.execute(
            select(self.model).where(self.model.github_path == github_path)
        )
        return result.scalar_one_or_none()
    
    async def get_auto_sync_categories(self, db: AsyncSession) -> List[Category]:
        """获取启用自动同步的分类"""
        result = await db.execute(
            select(self.model)
            .where(and_(
                self.model.auto_sync == True,
                self.model.is_active == True,
                self.model.github_path.isnot(None)
            ))
        )
        return result.scalars().all()
    
    async def create_with_path(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: CategoryCreate,
        parent_id: Optional[int] = None
    ) -> Category:
        """创建分类并自动设置层级和路径"""
        # 计算层级
        level = 0
        if parent_id:
            parent = await self.get(db, id=parent_id)
            if parent:
                level = parent.level + 1
        
        # 创建分类数据
        create_data = obj_in.model_dump()
        create_data.update({
            "parent_id": parent_id,
            "level": level,
            "article_count": 0
        })
        
        # 如果没有指定排序，设置为最后
        if "sort_order" not in create_data or create_data["sort_order"] is None:
            result = await db.execute(
                select(func.max(self.model.sort_order))
                .where(self.model.parent_id == parent_id)
            )
            max_order = result.scalar() or 0
            create_data["sort_order"] = max_order + 1
        
        return await self.create(db, obj_in=create_data)
    
    async def update_article_count(self, db: AsyncSession, *, category_id: int) -> Optional[Category]:
        """更新分类的文章数量"""
        from app.models.article import Article
        
        # 计算文章数量
        result = await db.execute(
            select(func.count(Article.id))
            .where(and_(
                Article.category_id == category_id,
                Article.status == "published"
            ))
        )
        article_count = result.scalar() or 0
        
        # 更新分类
        category = await self.get(db, id=category_id)
        if category:
            category.article_count = article_count
            await db.commit()
            await db.refresh(category)
        
        return category
    
    async def move_category(
        self, 
        db: AsyncSession, 
        *, 
        category_id: int,
        new_parent_id: Optional[int] = None
    ) -> Optional[Category]:
        """移动分类到新的父分类下"""
        category = await self.get(db, id=category_id)
        if not category:
            return None
        
        # 计算新的层级
        new_level = 0
        if new_parent_id:
            parent = await self.get(db, id=new_parent_id)
            if parent:
                new_level = parent.level + 1
        
        # 更新分类
        category.parent_id = new_parent_id
        category.level = new_level
        
        await db.commit()
        await db.refresh(category)
        
        # 递归更新所有子分类的层级
        await self._update_children_level(db, category_id=category_id, base_level=new_level)
        
        return category
    
    async def _update_children_level(
        self, 
        db: AsyncSession, 
        *, 
        category_id: int,
        base_level: int
    ):
        """递归更新子分类的层级"""
        children = await self.get_children(db, parent_id=category_id)
        
        for child in children:
            child.level = base_level + 1
            await self._update_children_level(db, category_id=child.id, base_level=child.level)
        
        await db.commit()
    
    async def get_category_stats(self, db: AsyncSession, *, category_id: int) -> Dict[str, Any]:
        """获取分类统计信息"""
        from app.models.article import Article
        
        # 获取分类信息
        category = await self.get(db, id=category_id)
        if not category:
            return {}
        
        # 统计文章数量（按状态）
        result = await db.execute(
            select(
                Article.status,
                func.count(Article.id).label('count')
            )
            .where(Article.category_id == category_id)
            .group_by(Article.status)
        )
        status_counts = {row.status: row.count for row in result}
        
        # 统计子分类数量
        children_count = len(await self.get_children(db, parent_id=category_id))
        
        return {
            "category": category,
            "article_counts": status_counts,
            "total_articles": sum(status_counts.values()),
            "children_count": children_count,
            "is_leaf": children_count == 0
        }


# 创建实例
category = CRUDCategory(Category)