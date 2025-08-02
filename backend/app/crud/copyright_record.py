"""
版权记录CRUD操作
提供版权记录相关的数据库操作方法
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.copyright_record import CopyrightRecord, CopyrightStatus, CopyrightSource, SimilarityLevel
from app.schemas.copyright_record import CopyrightRecordCreate, CopyrightRecordUpdate, CopyrightSearch


class CRUDCopyrightRecord(CRUDBase[CopyrightRecord, CopyrightRecordCreate, CopyrightRecordUpdate]):
    """版权记录CRUD操作类"""

    async def get_by_article_id(
        self,
        db: AsyncSession,
        *,
        article_id: int,
        status: Optional[CopyrightStatus] = None
    ) -> List[CopyrightRecord]:
        """
        根据文章ID获取版权记录
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            status: 可选的状态过滤
            
        Returns:
            版权记录列表
        """
        query = select(CopyrightRecord).where(CopyrightRecord.article_id == article_id)
        
        if status:
            query = query.where(CopyrightRecord.status == status)
            
        query = query.order_by(desc(CopyrightRecord.similarity_score))
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        status: CopyrightStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[CopyrightRecord]:
        """
        根据状态获取版权记录
        
        Args:
            db: 数据库会话
            status: 版权状态
            skip: 跳过记录数
            limit: 限制记录数
            
        Returns:
            版权记录列表
        """
        query = select(CopyrightRecord).where(CopyrightRecord.status == status)
        query = query.order_by(desc(CopyrightRecord.similarity_score))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_high_risk_records(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[CopyrightRecord]:
        """
        获取高风险版权记录
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            
        Returns:
            高风险版权记录列表
        """
        query = select(CopyrightRecord).where(
            or_(
                CopyrightRecord.status == CopyrightStatus.VIOLATION,
                and_(
                    CopyrightRecord.similarity_score.isnot(None),
                    CopyrightRecord.similarity_score >= 0.7
                )
            )
        )
        query = query.order_by(desc(CopyrightRecord.similarity_score))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_similarity_range(
        self,
        db: AsyncSession,
        *,
        min_similarity: float,
        max_similarity: float,
        skip: int = 0,
        limit: int = 100
    ) -> List[CopyrightRecord]:
        """
        根据相似度范围查询版权记录
        
        Args:
            db: 数据库会话
            min_similarity: 最小相似度
            max_similarity: 最大相似度
            skip: 跳过记录数
            limit: 限制记录数
            
        Returns:
            版权记录列表
        """
        query = select(CopyrightRecord).where(
            and_(
                CopyrightRecord.similarity_score >= min_similarity,
                CopyrightRecord.similarity_score <= max_similarity
            )
        )
        query = query.order_by(desc(CopyrightRecord.similarity_score))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def batch_check_copyright(
        self,
        db: AsyncSession,
        *,
        article_ids: List[int],
        check_method: str = "AI_MODEL",
        force_recheck: bool = False
    ) -> Dict[str, Any]:
        """
        批量版权检查
        
        Args:
            db: 数据库会话
            article_ids: 文章ID列表
            check_method: 检查方法
            force_recheck: 是否强制重新检查
            
        Returns:
            批量检查结果
        """
        results = {
            "total": len(article_ids),
            "processed": 0,
            "new_records": 0,
            "updated_records": 0,
            "errors": []
        }
        
        for article_id in article_ids:
            try:
                # 检查是否已存在记录
                existing_query = select(CopyrightRecord).where(
                    CopyrightRecord.article_id == article_id
                )
                existing_result = await db.execute(existing_query)
                existing_record = existing_result.scalar_one_or_none()
                
                if existing_record and not force_recheck:
                    continue
                
                # 这里应该调用实际的版权检查逻辑
                # 暂时创建一个示例记录
                record_data = CopyrightRecordCreate(
                    article_id=article_id,
                    source_url=None,
                    source_title=None,
                    source_author=None,
                    similarity_score=None,
                    similarity_level=None,
                    copyright_source=None
                )
                
                if existing_record:
                    # 更新现有记录
                    update_data = {
                        "check_method": check_method,
                        "last_updated": datetime.now().isoformat(),
                        "status": CopyrightStatus.PENDING
                    }
                    for field, value in update_data.items():
                        setattr(existing_record, field, value)
                    results["updated_records"] += 1
                else:
                    # 创建新记录
                    new_record = CopyrightRecord(
                        article_id=article_id,
                        status=CopyrightStatus.PENDING,
                        check_method=check_method,
                        checked_at=datetime.now().isoformat()
                    )
                    db.add(new_record)
                    results["new_records"] += 1
                
                results["processed"] += 1
                
            except Exception as e:
                results["errors"].append(f"Article {article_id}: {str(e)}")
        
        await db.commit()
        return results

    async def update_similarity_score(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        similarity_score: float,
        similarity_level: Optional[SimilarityLevel] = None,
        matched_content: Optional[str] = None,
        analysis_details: Optional[Dict[str, Any]] = None
    ) -> Optional[CopyrightRecord]:
        """
        更新相似度分数
        
        Args:
            db: 数据库会话
            record_id: 记录ID
            similarity_score: 相似度分数
            similarity_level: 相似度等级
            matched_content: 匹配内容
            analysis_details: 分析详情
            
        Returns:
            更新后的版权记录
        """
        record = await self.get(db, id=record_id)
        if not record:
            return None
        
        # 更新相似度信息
        record.similarity_score = similarity_score
        record.similarity_level = similarity_level or self._calculate_similarity_level(similarity_score)
        record.matched_content = matched_content
        record.analysis_details = analysis_details
        record.last_updated = datetime.now().isoformat()
        
        # 根据相似度自动更新状态
        if similarity_score >= 0.9:
            record.status = CopyrightStatus.VIOLATION
        elif similarity_score >= 0.7:
            record.status = CopyrightStatus.SUSPICIOUS
        elif similarity_score >= 0.5:
            record.status = CopyrightStatus.MANUAL_REVIEW
        else:
            record.status = CopyrightStatus.CLEAN
        
        await db.commit()
        await db.refresh(record)
        return record

    async def mark_false_positive(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        is_false_positive: bool = True,
        notes: Optional[str] = None
    ) -> Optional[CopyrightRecord]:
        """
        标记误报
        
        Args:
            db: 数据库会话
            record_id: 记录ID
            is_false_positive: 是否为误报
            notes: 备注说明
            
        Returns:
            更新后的版权记录
        """
        record = await self.get(db, id=record_id)
        if not record:
            return None
        
        record.is_false_positive = is_false_positive
        record.is_resolved = is_false_positive
        if notes:
            record.resolution_notes = notes
        record.last_updated = datetime.now().isoformat()
        
        # 如果标记为误报，状态改为清洁
        if is_false_positive:
            record.status = CopyrightStatus.CLEAN
        
        await db.commit()
        await db.refresh(record)
        return record

    async def get_copyright_stats(
        self,
        db: AsyncSession,
        *,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        source_type: Optional[CopyrightSource] = None
    ) -> Dict[str, Any]:
        """
        获取版权统计信息
        
        Args:
            db: 数据库会话
            date_from: 开始日期
            date_to: 结束日期
            source_type: 来源类型
            
        Returns:
            统计信息字典
        """
        # 基础查询
        base_query = select(CopyrightRecord)
        
        # 添加日期过滤
        if date_from:
            base_query = base_query.where(CopyrightRecord.checked_at >= date_from)
        if date_to:
            base_query = base_query.where(CopyrightRecord.checked_at <= date_to)
        if source_type:
            base_query = base_query.where(CopyrightRecord.source_type == source_type)
        
        # 总记录数
        total_query = select(func.count(CopyrightRecord.id))
        if date_from:
            total_query = total_query.where(CopyrightRecord.checked_at >= date_from)
        if date_to:
            total_query = total_query.where(CopyrightRecord.checked_at <= date_to)
        if source_type:
            total_query = total_query.where(CopyrightRecord.source_type == source_type)
        
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        
        # 状态统计
        status_query = select(
            CopyrightRecord.status,
            func.count(CopyrightRecord.id)
        ).group_by(CopyrightRecord.status)
        
        if date_from:
            status_query = status_query.where(CopyrightRecord.checked_at >= date_from)
        if date_to:
            status_query = status_query.where(CopyrightRecord.checked_at <= date_to)
        if source_type:
            status_query = status_query.where(CopyrightRecord.source_type == source_type)
        
        status_result = await db.execute(status_query)
        status_counts = {status.value: count for status, count in status_result.all()}
        
        # 来源类型统计
        source_query = select(
            CopyrightRecord.source_type,
            func.count(CopyrightRecord.id)
        ).where(CopyrightRecord.source_type.isnot(None)).group_by(CopyrightRecord.source_type)
        
        if date_from:
            source_query = source_query.where(CopyrightRecord.checked_at >= date_from)
        if date_to:
            source_query = source_query.where(CopyrightRecord.checked_at <= date_to)
        
        source_result = await db.execute(source_query)
        source_counts = {source.value if source else "unknown": count for source, count in source_result.all()}
        
        # 平均相似度
        avg_query = select(func.avg(CopyrightRecord.similarity_score)).where(
            CopyrightRecord.similarity_score.isnot(None)
        )
        if date_from:
            avg_query = avg_query.where(CopyrightRecord.checked_at >= date_from)
        if date_to:
            avg_query = avg_query.where(CopyrightRecord.checked_at <= date_to)
        if source_type:
            avg_query = avg_query.where(CopyrightRecord.source_type == source_type)
        
        avg_result = await db.execute(avg_query)
        avg_similarity = avg_result.scalar() or 0.0
        
        return {
            "total_records": total_count,
            "status_counts": status_counts,
            "source_counts": source_counts,
            "average_similarity": round(avg_similarity, 3),
            "clean_records": status_counts.get(CopyrightStatus.CLEAN.value, 0),
            "suspicious_records": status_counts.get(CopyrightStatus.SUSPICIOUS.value, 0),
            "violation_records": status_counts.get(CopyrightStatus.VIOLATION.value, 0),
            "pending_records": status_counts.get(CopyrightStatus.PENDING.value, 0),
            "manual_review_records": status_counts.get(CopyrightStatus.MANUAL_REVIEW.value, 0)
        }

    async def search_records(
        self,
        db: AsyncSession,
        *,
        search_params: CopyrightSearch
    ) -> Tuple[List[CopyrightRecord], int]:
        """
        搜索版权记录
        
        Args:
            db: 数据库会话
            search_params: 搜索参数
            
        Returns:
            (记录列表, 总数)
        """
        # 构建查询
        query = select(CopyrightRecord)
        count_query = select(func.count(CopyrightRecord.id))
        
        # 添加过滤条件
        conditions = []
        
        if search_params.article_id:
            conditions.append(CopyrightRecord.article_id == search_params.article_id)
        
        if search_params.status:
            conditions.append(CopyrightRecord.status == search_params.status)
        
        if search_params.copyright_source:
            conditions.append(CopyrightRecord.source_type == search_params.copyright_source)
        
        if search_params.similarity_level:
            conditions.append(CopyrightRecord.similarity_level == search_params.similarity_level)
        
        if search_params.min_similarity is not None:
            conditions.append(CopyrightRecord.similarity_score >= search_params.min_similarity)
        
        if search_params.max_similarity is not None:
            conditions.append(CopyrightRecord.similarity_score <= search_params.max_similarity)
        
        if search_params.false_positive is not None:
            conditions.append(CopyrightRecord.is_false_positive == search_params.false_positive)
        
        if search_params.source_url:
            conditions.append(CopyrightRecord.source_url.ilike(f"%{search_params.source_url}%"))
        
        if search_params.source_author:
            conditions.append(CopyrightRecord.source_author.ilike(f"%{search_params.source_author}%"))
        
        if search_params.date_from:
            conditions.append(CopyrightRecord.checked_at >= search_params.date_from)
        
        if search_params.date_to:
            conditions.append(CopyrightRecord.checked_at <= search_params.date_to)
        
        # 应用过滤条件
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 获取总数
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # 排序
        if search_params.sort_by == "similarity_score":
            order_col = CopyrightRecord.similarity_score
        elif search_params.sort_by == "checked_at":
            order_col = CopyrightRecord.checked_at
        else:
            order_col = getattr(CopyrightRecord, search_params.sort_by, CopyrightRecord.id)
        
        if search_params.sort_order == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
        
        # 分页
        offset = (search_params.page - 1) * search_params.size
        query = query.offset(offset).limit(search_params.size)
        
        # 执行查询
        result = await db.execute(query)
        records = result.scalars().all()
        
        return records, total_count

    async def get_needs_review(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[CopyrightRecord]:
        """
        获取需要人工审核的记录
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            
        Returns:
            需要审核的版权记录列表
        """
        query = select(CopyrightRecord).where(
            or_(
                CopyrightRecord.status == CopyrightStatus.MANUAL_REVIEW,
                and_(
                    CopyrightRecord.similarity_score.isnot(None),
                    CopyrightRecord.similarity_score >= 0.5,
                    CopyrightRecord.is_resolved == False
                )
            )
        )
        query = query.order_by(desc(CopyrightRecord.similarity_score))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def batch_update_status(
        self,
        db: AsyncSession,
        *,
        record_ids: List[int],
        status: CopyrightStatus,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量更新状态
        
        Args:
            db: 数据库会话
            record_ids: 记录ID列表
            status: 新状态
            notes: 备注说明
            
        Returns:
            批量更新结果
        """
        results = {
            "total": len(record_ids),
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        for record_id in record_ids:
            try:
                record = await self.get(db, id=record_id)
                if record:
                    record.status = status
                    record.last_updated = datetime.now().isoformat()
                    if notes:
                        record.resolution_notes = notes
                    results["updated"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Record {record_id} not found")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Record {record_id}: {str(e)}")
        
        await db.commit()
        return results

    def _calculate_similarity_level(self, similarity_score: float) -> SimilarityLevel:
        """
        根据相似度分数计算相似度等级
        
        Args:
            similarity_score: 相似度分数
            
        Returns:
            相似度等级
        """
        if similarity_score >= 0.9:
            return SimilarityLevel.VERY_HIGH
        elif similarity_score >= 0.7:
            return SimilarityLevel.HIGH
        elif similarity_score >= 0.3:
            return SimilarityLevel.MEDIUM
        else:
            return SimilarityLevel.LOW


# 创建CRUD实例
copyright_record = CRUDCopyrightRecord(CopyrightRecord)