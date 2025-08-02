"""
文章相关的数据库操作
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.article import Article, ArticleStatus, CopyrightStatus
from app.schemas.article import ArticleCreate, ArticleUpdate


class CRUDArticle(CRUDBase[Article, ArticleCreate, ArticleUpdate]):
    """文章CRUD操作类"""
    
    async def get_by_github_url(self, db: AsyncSession, *, github_url: str) -> Optional[Article]:
        """根据GitHub URL获取文章"""
        result = await db.execute(
            select(self.model).where(self.model.github_url == github_url)
        )
        return result.scalar_one_or_none()
    
    async def get_by_category(
        self, 
        db: AsyncSession, 
        *, 
        category_id: int,
        status: Optional[ArticleStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Article]:
        """获取指定分类的文章"""
        query = select(self.model).where(self.model.category_id == category_id)
        
        if status:
            query = query.where(self.model.status == status)
        
        query = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int,
        status: Optional[ArticleStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Article]:
        """获取指定用户的文章"""
        query = select(self.model).where(self.model.user_id == user_id)
        
        if status:
            query = query.where(self.model.status == status)
        
        query = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_status(
        self, 
        db: AsyncSession, 
        *, 
        status: ArticleStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Article]:
        """获取指定状态的文章"""
        result = await db.execute(
            select(self.model)
            .where(self.model.status == status)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_published(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0,
        limit: int = 100
    ) -> List[Article]:
        """获取已发布的文章"""
        return await self.get_by_status(db, status=ArticleStatus.published, skip=skip, limit=limit)
    
    async def get_pending_review(self, db: AsyncSession) -> List[Article]:
        """获取待审核的文章"""
        result = await db.execute(
            select(self.model)
            .where(self.model.status == ArticleStatus.pending)
            .order_by(asc(self.model.created_at))
        )
        return result.scalars().all()
    
    async def search_articles(
        self, 
        db: AsyncSession, 
        *, 
        keyword: str,
        category_id: Optional[int] = None,
        status: Optional[ArticleStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Article]:
        """搜索文章"""
        query = select(self.model).where(
            or_(
                self.model.title.ilike(f"%{keyword}%"),
                self.model.content.ilike(f"%{keyword}%"),
                self.model.summary.ilike(f"%{keyword}%"),
                self.model.keywords.ilike(f"%{keyword}%"),
                self.model.author.ilike(f"%{keyword}%")
            )
        )
        
        if category_id:
            query = query.where(self.model.category_id == category_id)
        
        if status:
            query = query.where(self.model.status == status)
        
        query = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_copyright_issues(
        self, 
        db: AsyncSession, 
        *, 
        copyright_status: Optional[CopyrightStatus] = None
    ) -> List[Article]:
        """获取有版权问题的文章"""
        query = select(self.model)
        
        if copyright_status:
            query = query.where(self.model.copyright_status == copyright_status)
        else:
            query = query.where(
                self.model.copyright_status.in_([
                    CopyrightStatus.SUSPECTED,
                    CopyrightStatus.CONFIRMED
                ])
            )
        
        query = query.order_by(desc(self.model.updated_at))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_popular_articles(
        self, 
        db: AsyncSession, 
        *, 
        limit: int = 10,
        days: int = 30
    ) -> List[Article]:
        """获取热门文章（基于浏览量和下载量）"""
        # 这里简化处理，实际可以根据时间范围和权重计算
        result = await db.execute(
            select(self.model)
            .where(self.model.status == ArticleStatus.published)
            .order_by(desc(self.model.view_count + self.model.download_count * 2))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_recent_articles(
        self, 
        db: AsyncSession, 
        *, 
        limit: int = 10
    ) -> List[Article]:
        """获取最新文章"""
        result = await db.execute(
            select(self.model)
            .where(self.model.status == ArticleStatus.published)
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def increment_view_count(self, db: AsyncSession, *, article_id: int) -> Optional[Article]:
        """增加文章浏览量"""
        article = await self.get(db, id=article_id)
        if article:
            article.view_count += 1
            await db.commit()
            await db.refresh(article)
        return article
    
    async def increment_download_count(self, db: AsyncSession, *, article_id: int) -> Optional[Article]:
        """增加文章下载量"""
        article = await self.get(db, id=article_id)
        if article:
            article.download_count += 1
            await db.commit()
            await db.refresh(article)
        return article
    
    async def update_status(
        self, 
        db: AsyncSession, 
        *, 
        article_id: int,
        status: ArticleStatus
    ) -> Optional[Article]:
        """更新文章状态"""
        article = await self.get(db, id=article_id)
        if article:
            article.status = status
            await db.commit()
            await db.refresh(article)
        return article
    
    async def update_copyright_status(
        self, 
        db: AsyncSession, 
        *, 
        article_id: int,
        copyright_status: CopyrightStatus
    ) -> Optional[Article]:
        """更新文章版权状态"""
        article = await self.get(db, id=article_id)
        if article:
            article.copyright_status = copyright_status
            await db.commit()
            await db.refresh(article)
        return article
    
    async def get_articles_with_relations(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0,
        limit: int = 100
    ) -> List[Article]:
        """获取文章及其关联数据"""
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(self.model.category),
                selectinload(self.model.user),
                selectinload(self.model.reviews),
                selectinload(self.model.copyright_records)
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_article_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """获取文章统计信息"""
        # 按状态统计
        result = await db.execute(
            select(
                self.model.status,
                func.count(self.model.id).label('count')
            ).group_by(self.model.status)
        )
        status_counts = {row.status: row.count for row in result}
        
        # 按版权状态统计
        result = await db.execute(
            select(
                self.model.copyright_status,
                func.count(self.model.id).label('count')
            ).group_by(self.model.copyright_status)
        )
        copyright_counts = {row.copyright_status: row.count for row in result}
        
        # 总统计
        result = await db.execute(
            select(
                func.count(self.model.id).label('total'),
                func.sum(self.model.view_count).label('total_views'),
                func.sum(self.model.download_count).label('total_downloads'),
                func.avg(self.model.ai_score).label('avg_ai_score')
            )
        )
        totals = result.first()
        
        return {
            "status_counts": status_counts,
            "copyright_counts": copyright_counts,
            "total_articles": totals.total or 0,
            "total_views": totals.total_views or 0,
            "total_downloads": totals.total_downloads or 0,
            "average_ai_score": float(totals.avg_ai_score or 0)
        }
    
    async def get_user_article_stats(self, db: AsyncSession, *, user_id: int) -> Dict[str, Any]:
        """获取用户文章统计信息"""
        result = await db.execute(
            select(
                self.model.status,
                func.count(self.model.id).label('count')
            )
            .where(self.model.user_id == user_id)
            .group_by(self.model.status)
        )
        status_counts = {row.status: row.count for row in result}
        
        result = await db.execute(
            select(
                func.count(self.model.id).label('total'),
                func.sum(self.model.view_count).label('total_views'),
                func.sum(self.model.download_count).label('total_downloads')
            )
            .where(self.model.user_id == user_id)
        )
        totals = result.first()
        
        return {
            "status_counts": status_counts,
            "total_articles": totals.total or 0,
            "total_views": totals.total_views or 0,
            "total_downloads": totals.total_downloads or 0
        }


# 创建实例
article = CRUDArticle(Article)