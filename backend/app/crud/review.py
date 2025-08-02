"""
审核记录CRUD操作
提供审核相关的数据库操作方法
"""

from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.review import Review, ReviewType, ReviewStatus, ReviewCategory
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewSearch


class CRUDReview(CRUDBase[Review, ReviewCreate, ReviewUpdate]):
    """审核记录CRUD操作类"""

    async def get_by_article_id(
        self, 
        db: AsyncSession, 
        *, 
        article_id: int,
        review_type: Optional[ReviewType] = None
    ) -> List[Review]:
        """根据文章ID获取审核记录"""
        query = select(self.model).where(self.model.article_id == article_id)
        
        if review_type:
            query = query.where(self.model.review_type == review_type)
        
        query = query.order_by(self.model.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_reviewer(
        self, 
        db: AsyncSession, 
        *, 
        reviewer_id: int,
        status: Optional[ReviewStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Review]:
        """根据审核员获取审核列表"""
        query = select(self.model).where(self.model.reviewer_id == reviewer_id)
        
        if status:
            query = query.where(self.model.status == status)
        
        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_status(
        self, 
        db: AsyncSession, 
        *, 
        status: ReviewStatus,
        review_type: Optional[ReviewType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Review]:
        """根据状态获取审核记录"""
        query = select(self.model).where(self.model.status == status)
        
        if review_type:
            query = query.where(self.model.review_type == review_type)
        
        query = query.order_by(self.model.priority.desc(), self.model.created_at.asc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def assign_reviewer(
        self, 
        db: AsyncSession, 
        *, 
        review_id: int,
        reviewer_id: int
    ) -> Optional[Review]:
        """分配审核员"""
        review = await self.get(db, id=review_id)
        if not review:
            return None
        
        # 更新审核员和分配时间
        review.reviewer_id = reviewer_id
        review.assigned_at = datetime.now().isoformat()
        
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def batch_assign(
        self, 
        db: AsyncSession, 
        *, 
        review_ids: List[int],
        reviewer_id: int
    ) -> Dict[str, Any]:
        """批量分配审核"""
        assigned_count = 0
        failed_ids = []
        
        for review_id in review_ids:
            try:
                review = await self.assign_reviewer(
                    db, review_id=review_id, reviewer_id=reviewer_id
                )
                if review:
                    assigned_count += 1
                else:
                    failed_ids.append(review_id)
            except Exception:
                failed_ids.append(review_id)
        
        return {
            "assigned_count": assigned_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }

    async def update_status(
        self, 
        db: AsyncSession, 
        *, 
        review_id: int,
        status: ReviewStatus,
        comments: Optional[str] = None,
        score: Optional[int] = None
    ) -> Optional[Review]:
        """更新审核状态"""
        review = await self.get(db, id=review_id)
        if not review:
            return None
        
        # 更新状态和相关信息
        review.status = status
        if comments:
            review.comments = comments
        if score is not None:
            review.score = score
        
        # 如果审核完成，设置完成时间
        if status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED):
            review.completed_at = datetime.now().isoformat()
            review.is_final = True
        
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def get_pending_reviews(
        self, 
        db: AsyncSession, 
        *, 
        reviewer_id: Optional[int] = None,
        review_type: Optional[ReviewType] = None,
        priority_min: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Review]:
        """获取待审核列表"""
        query = select(self.model).where(self.model.status == ReviewStatus.PENDING)
        
        if reviewer_id:
            query = query.where(self.model.reviewer_id == reviewer_id)
        
        if review_type:
            query = query.where(self.model.review_type == review_type)
        
        if priority_min:
            query = query.where(self.model.priority >= priority_min)
        
        # 按优先级和创建时间排序
        query = query.order_by(
            self.model.priority.desc(), 
            self.model.created_at.asc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_reviewer_workload(
        self, 
        db: AsyncSession, 
        *, 
        reviewer_id: int
    ) -> Dict[str, Any]:
        """获取审核员工作负载"""
        # 统计各状态的审核数量
        pending_count = await db.execute(
            select(func.count(self.model.id)).where(
                and_(
                    self.model.reviewer_id == reviewer_id,
                    self.model.status == ReviewStatus.PENDING
                )
            )
        )
        
        completed_count = await db.execute(
            select(func.count(self.model.id)).where(
                and_(
                    self.model.reviewer_id == reviewer_id,
                    self.model.status.in_([ReviewStatus.APPROVED, ReviewStatus.REJECTED])
                )
            )
        )
        
        # 计算平均评分
        avg_score = await db.execute(
            select(func.avg(self.model.score)).where(
                and_(
                    self.model.reviewer_id == reviewer_id,
                    self.model.score.isnot(None)
                )
            )
        )
        
        return {
            "reviewer_id": reviewer_id,
            "pending_reviews": pending_count.scalar() or 0,
            "completed_reviews": completed_count.scalar() or 0,
            "average_score": round(avg_score.scalar() or 0, 2)
        }

    async def get_review_stats(
        self, 
        db: AsyncSession, 
        *, 
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        review_type: Optional[ReviewType] = None
    ) -> Dict[str, Any]:
        """获取审核统计信息"""
        query = select(self.model)
        
        # 添加日期过滤
        if date_from:
            query = query.where(self.model.created_at >= date_from)
        if date_to:
            query = query.where(self.model.created_at <= date_to)
        if review_type:
            query = query.where(self.model.review_type == review_type)
        
        # 总数统计
        total_count = await db.execute(
            select(func.count(self.model.id)).select_from(query.subquery())
        )
        
        # 各状态统计
        status_stats = {}
        for status in ReviewStatus:
            count = await db.execute(
                select(func.count(self.model.id)).where(
                    and_(
                        query.whereclause,
                        self.model.status == status
                    )
                )
            )
            status_stats[status.value] = count.scalar() or 0
        
        # 类型统计
        type_stats = {}
        for r_type in ReviewType:
            count = await db.execute(
                select(func.count(self.model.id)).where(
                    and_(
                        query.whereclause,
                        self.model.review_type == r_type
                    )
                )
            )
            type_stats[r_type.value] = count.scalar() or 0
        
        # 平均评分
        avg_score = await db.execute(
            select(func.avg(self.model.score)).where(
                and_(
                    query.whereclause,
                    self.model.score.isnot(None)
                )
            )
        )
        
        return {
            "total_reviews": total_count.scalar() or 0,
            "status_distribution": status_stats,
            "type_distribution": type_stats,
            "average_score": round(avg_score.scalar() or 0, 2)
        }

    async def search_reviews(
        self, 
        db: AsyncSession, 
        *, 
        search_params: ReviewSearch
    ) -> List[Review]:
        """搜索审核记录"""
        query = select(self.model)
        
        # 添加搜索条件
        if search_params.article_id:
            query = query.where(self.model.article_id == search_params.article_id)
        
        if search_params.reviewer_id:
            query = query.where(self.model.reviewer_id == search_params.reviewer_id)
        
        if search_params.review_type:
            query = query.where(self.model.review_type == search_params.review_type)
        
        if search_params.review_category:
            query = query.where(self.model.review_category == search_params.review_category)
        
        if search_params.status:
            query = query.where(self.model.status == search_params.status)
        
        if search_params.min_score is not None:
            query = query.where(self.model.score >= search_params.min_score)
        
        if search_params.max_score is not None:
            query = query.where(self.model.score <= search_params.max_score)
        
        if search_params.priority:
            query = query.where(self.model.priority == search_params.priority)
        
        if search_params.requires_human_review is not None:
            query = query.where(self.model.requires_human_review == search_params.requires_human_review)
        
        if search_params.date_from:
            query = query.where(self.model.created_at >= search_params.date_from)
        
        if search_params.date_to:
            query = query.where(self.model.created_at <= search_params.date_to)
        
        # 排序
        if hasattr(self.model, search_params.sort_by):
            sort_column = getattr(self.model, search_params.sort_by)
            if search_params.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(self.model.created_at.desc())
        
        # 分页
        skip = (search_params.page - 1) * search_params.size
        query = query.offset(skip).limit(search_params.size)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_high_priority_reviews(
        self, 
        db: AsyncSession, 
        *, 
        min_priority: int = 3,
        skip: int = 0,
        limit: int = 50
    ) -> List[Review]:
        """获取高优先级审核"""
        query = select(self.model).where(
            and_(
                self.model.priority >= min_priority,
                self.model.status == ReviewStatus.PENDING
            )
        ).order_by(
            self.model.priority.desc(),
            self.model.created_at.asc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def batch_update_status(
        self, 
        db: AsyncSession, 
        *, 
        review_ids: List[int],
        status: ReviewStatus,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量更新审核状态"""
        updated_count = 0
        failed_ids = []
        
        for review_id in review_ids:
            try:
                review = await self.update_status(
                    db, 
                    review_id=review_id, 
                    status=status, 
                    comments=comments
                )
                if review:
                    updated_count += 1
                else:
                    failed_ids.append(review_id)
            except Exception:
                failed_ids.append(review_id)
        
        return {
            "updated_count": updated_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }


# 创建实例
review = CRUDReview(Review)