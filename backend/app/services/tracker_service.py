"""
上传跟踪服务
处理跟踪ID查询和状态管理
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.article import Article, ProcessingStatus, UploadMethod
from app.schemas.tracker import TrackerStatusResponse


class TrackerService:
    """上传跟踪服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_tracker_status(self, tracker_id: str) -> Optional[TrackerStatusResponse]:
        """
        根据tracker_id查询上传状态
        
        Args:
            tracker_id: 跟踪ID
            
        Returns:
            TrackerStatusResponse: 跟踪状态响应，如果未找到返回None
        """
        try:
            # 查询文章记录
            stmt = select(Article).where(Article.tracker_id == tracker_id)
            result = await self.db.execute(stmt)
            article = result.scalar_one_or_none()
            
            if not article:
                return None
            
            # 构建元数据
            metadata = self._build_metadata(article)
            
            # 确定处理完成时间
            processed_at = None
            if article.processing_status in [ProcessingStatus.COMPLETED, ProcessingStatus.REJECTED]:
                processed_at = article.updated_at
            
            # 构建错误信息
            error_message = None
            if article.processing_status == ProcessingStatus.REJECTED:
                error_message = self._get_rejection_reason(article)
            
            return TrackerStatusResponse(
                tracker_id=tracker_id,
                processing_status=article.processing_status,
                upload_method=article.method,
                title=article.title,
                file_type=article.file_type.value if article.file_type else None,
                file_size=article.file_size,
                created_at=article.created_at,
                updated_at=article.updated_at,
                processed_at=processed_at,
                metadata=metadata,
                error_message=error_message
            )
            
        except Exception as e:
            raise Exception(f"查询跟踪状态失败: {str(e)}")
    
    def _build_metadata(self, article: Article) -> Dict[str, Any]:
        """
        构建元数据信息
        
        Args:
            article: 文章对象
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {
            "article_id": article.id,
            "github_info": {
                "owner": article.github_owner,
                "repo": article.github_repo,
                "branch": article.github_branch,
                "path": article.github_path,
                "url": article.github_url
            } if article.github_url else None,
            "status_info": {
                "article_status": article.status.value,
                "copyright_status": article.copyright_status.value
            },
            "stats": {
                "view_count": article.view_count,
                "download_count": article.download_count,
                "star_count": article.star_count,
                "fork_count": article.fork_count
            },
            "tags": article.tags or [],
            "keywords": article.keywords or [],
            "language": article.language,
            "featured": article.featured
        }
        
        # 添加AI分析结果（如果有）
        if article.ai_analysis:
            metadata["ai_analysis"] = article.ai_analysis
        
        if article.ai_tags:
            metadata["ai_tags"] = article.ai_tags
        
        if article.ai_category_suggestion:
            metadata["ai_category_suggestion"] = article.ai_category_suggestion
        
        # 添加同步信息
        if article.last_sync_at:
            metadata["sync_info"] = {
                "last_sync_at": article.last_sync_at,
                "sync_status": article.sync_status,
                "auto_sync": article.auto_sync
            }
        
        # 添加发布信息
        if article.published_at:
            metadata["published_at"] = article.published_at
        
        return metadata
    
    def _get_rejection_reason(self, article: Article) -> Optional[str]:
        """
        获取拒绝原因
        
        Args:
            article: 文章对象
            
        Returns:
            Optional[str]: 拒绝原因
        """
        # 检查版权问题
        if article.has_copyright_issues:
            return f"版权问题: {article.copyright_status.value}"
        
        # 检查额外元数据中的错误信息
        if article.extra_metadata and "error" in article.extra_metadata:
            return article.extra_metadata["error"]
        
        # 检查审核记录
        if article.reviews:
            latest_review = max(article.reviews, key=lambda r: r.created_at)
            if latest_review.status == "rejected" and latest_review.comment:
                return f"审核拒绝: {latest_review.comment}"
        
        return "处理被拒绝，具体原因请联系管理员"
    
    async def update_processing_status(
        self, 
        tracker_id: str, 
        status: ProcessingStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新处理状态
        
        Args:
            tracker_id: 跟踪ID
            status: 新的处理状态
            error_message: 错误信息（可选）
            
        Returns:
            bool: 更新是否成功
        """
        try:
            article = self.db.query(Article).filter(
                Article.tracker_id == tracker_id
            ).first()
            
            if not article:
                return False
            
            # 更新处理状态
            article.processing_status = status
            article.updated_at = datetime.utcnow()
            
            # 如果有错误信息，保存到额外元数据中
            if error_message:
                if not article.extra_metadata:
                    article.extra_metadata = {}
                article.extra_metadata["error"] = error_message
                article.extra_metadata["error_time"] = datetime.utcnow().isoformat()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新处理状态失败: {str(e)}")
    
    async def get_tracker_statistics(self) -> Dict[str, Any]:
        """
        获取跟踪统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 统计各状态的数量
            status_counts = {}
            for status in ProcessingStatus:
                stmt = select(Article).where(Article.processing_status == status)
                result = await self.db.execute(stmt)
                count = len(result.scalars().all())
                status_counts[status.value] = count
            
            # 统计各上传方法的数量
            method_counts = {}
            for method in UploadMethod:
                stmt = select(Article).where(Article.method == method)
                result = await self.db.execute(stmt)
                count = len(result.scalars().all())
                method_counts[method.value] = count
            
            # 总数统计
            stmt = select(Article).where(Article.tracker_id.isnot(None))
            result = await self.db.execute(stmt)
            total_tracked = len(result.scalars().all())
            
            return {
                "total_tracked": total_tracked,
                "status_distribution": status_counts,
                "method_distribution": method_counts,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"获取统计信息失败: {str(e)}")
