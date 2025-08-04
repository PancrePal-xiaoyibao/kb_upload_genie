"""
邮件相关的后台任务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.services.email_service import email_service
from app.services.attachment_service import attachment_service
from app.services.domain_service import domain_service
from app.services.notification_service import notification_service
from app.services.redis_service import redis_service
from app.core.config import settings
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class EmailTaskManager:
    """邮件任务管理器"""
    
    def __init__(self):
        self.running = False
        self.check_task = None
        self.maintenance_task = None
        self.stats = {
            "total_emails_processed": 0,
            "total_attachments_saved": 0,
            "total_notifications_sent": 0,
            "last_check_time": None,
            "last_maintenance_time": None,
            "errors_count": 0
        }
    
    async def start_email_checking(self):
        """启动邮件检查任务"""
        if not settings.EMAIL_UPLOAD_ENABLED:
            logger.info("邮件上传功能未启用，跳过邮件检查")
            return
        
        if self.running:
            logger.warning("邮件检查任务已在运行")
            return
        
        self.running = True
        self.check_task = asyncio.create_task(self._email_check_loop())
        self.maintenance_task = asyncio.create_task(self._maintenance_loop())
        logger.info("邮件检查任务已启动")
    
    async def stop_email_checking(self):
        """停止邮件检查任务"""
        if not self.running:
            return
        
        self.running = False
        
        # 停止邮件检查任务
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        
        # 停止维护任务
        if self.maintenance_task:
            self.maintenance_task.cancel()
            try:
                await self.maintenance_task
            except asyncio.CancelledError:
                pass
        
        logger.info("邮件检查任务已停止")
    
    async def _email_check_loop(self):
        """邮件检查循环"""
        while self.running:
            try:
                logger.debug("开始检查新邮件")
                
                # 使用数据库会话并设置超时
                async with AsyncSessionLocal() as db:
                    # 设置邮件检查超时时间（30秒）
                    try:
                        email_records = await asyncio.wait_for(
                            email_service.fetch_new_emails(db),
                            timeout=30.0
                        )
                        
                        if email_records:
                            # 保存邮件记录
                            await email_service.save_email_records(email_records, db)
                            
                            # 更新统计信息
                            self.stats["total_emails_processed"] += len(email_records)
                            
                            # 计算附件总数
                            total_attachments = sum(len(record.get('attachments', [])) for record in email_records)
                            self.stats["total_attachments_saved"] += total_attachments
                            
                            logger.info(f"处理了 {len(email_records)} 封邮件，{total_attachments} 个附件")
                        else:
                            logger.debug("没有新邮件")
                    
                    except asyncio.TimeoutError:
                        logger.error("邮件检查超时（30秒），跳过本次检查")
                        self.stats["errors_count"] += 1
                    
                    self.stats["last_check_time"] = datetime.now()
                
                logger.debug("邮件检查完成")
                
            except Exception as e:
                logger.error(f"邮件检查出错: {e}")
                self.stats["errors_count"] += 1
            
            # 等待下次检查
            try:
                await asyncio.sleep(settings.EMAIL_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
    
    async def _maintenance_loop(self):
        """维护任务循环"""
        while self.running:
            try:
                # 每小时运行一次维护任务
                await asyncio.sleep(3600)  # 1小时
                
                if not self.running:
                    break
                
                logger.info("开始运行维护任务")
                await self._run_maintenance_tasks()
                self.stats["last_maintenance_time"] = datetime.now()
                logger.info("维护任务完成")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"维护任务出错: {e}")
                self.stats["errors_count"] += 1
    
    async def _run_maintenance_tasks(self):
        """运行维护任务"""
        try:
            # 清理过期的频率限制记录
            await self._cleanup_old_rate_limits()
            
            # 清理过期的上传记录
            await self._cleanup_old_uploads()
            
            # 清理旧附件文件
            cleaned_files = await attachment_service.cleanup_old_attachments(days_old=30)
            if cleaned_files > 0:
                logger.info(f"清理了 {cleaned_files} 个旧附件文件")
            
            # 清理域名缓存（可选）
            await domain_service.clear_all_domain_cache()
            
        except Exception as e:
            logger.error(f"维护任务执行失败: {e}")
            raise
    
    async def check_emails_once(self):
        """手动检查一次邮件"""
        try:
            async with AsyncSessionLocal() as db:
                email_records = await email_service.fetch_new_emails(db)
                
                if email_records:
                    await email_service.save_email_records(email_records, db)
                    self.stats["total_emails_processed"] += len(email_records)
                    
                    total_attachments = sum(len(record.get('attachments', [])) for record in email_records)
                    self.stats["total_attachments_saved"] += total_attachments
                    
                    logger.info(f"手动检查处理了 {len(email_records)} 封邮件，{total_attachments} 个附件")
                    return len(email_records)
                else:
                    logger.info("手动检查未发现新邮件")
                    return 0
                    
        except Exception as e:
            logger.error(f"手动邮件检查失败: {e}")
            self.stats["errors_count"] += 1
            raise
    
    async def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        return {
            "running": self.running,
            "stats": self.stats.copy(),
            "config": {
                "email_upload_enabled": settings.EMAIL_UPLOAD_ENABLED,
                "check_interval": settings.EMAIL_CHECK_INTERVAL,
                "max_attachment_size": settings.EMAIL_MAX_ATTACHMENT_SIZE,
                "max_attachment_count": settings.EMAIL_MAX_ATTACHMENT_COUNT
            }
        }
    
    async def _cleanup_old_rate_limits(self):
        """清理过期的频率限制记录"""
        try:
            async with AsyncSessionLocal() as session:
                from app.models.email_upload import EmailRateLimit
                from sqlalchemy import delete
                
                # 删除7天前的记录
                cutoff_date = datetime.now() - timedelta(days=7)
                
                stmt = delete(EmailRateLimit).where(
                    EmailRateLimit.last_daily_reset < cutoff_date
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info(f"清理了 {deleted_count} 条过期的频率限制记录")
        
        except Exception as e:
            logger.error(f"清理频率限制记录失败: {e}")
    
    async def _cleanup_old_uploads(self):
        """清理过期的上传记录"""
        try:
            async with AsyncSessionLocal() as session:
                from app.models.email_upload import EmailUpload, EmailUploadStatus
                from sqlalchemy import select, delete
                
                # 删除30天前被拒绝的记录
                cutoff_date = datetime.now() - timedelta(days=30)
                
                # 先查询要删除的记录
                stmt = select(EmailUpload).where(
                    EmailUpload.status == EmailUploadStatus.REJECTED,
                    EmailUpload.processed_at < cutoff_date
                )
                
                result = await session.execute(stmt)
                old_uploads = result.scalars().all()
                
                # 删除对应的文件
                for upload in old_uploads:
                    try:
                        await attachment_service.delete_attachment(upload.stored_filename)
                    except Exception as e:
                        logger.warning(f"删除文件失败 {upload.stored_filename}: {e}")
                
                # 删除数据库记录
                if old_uploads:
                    delete_stmt = delete(EmailUpload).where(
                        EmailUpload.status == EmailUploadStatus.REJECTED,
                        EmailUpload.processed_at < cutoff_date
                    )
                    
                    await session.execute(delete_stmt)
                    await session.commit()
                    
                    logger.info(f"清理了 {len(old_uploads)} 条过期的上传记录")
        
        except Exception as e:
            logger.error(f"清理上传记录失败: {e}")


# 全局邮件任务管理器实例
email_task_manager = EmailTaskManager()


async def cleanup_old_rate_limits():
    """清理过期的频率限制记录"""
    from app.core.database import AsyncSessionLocal
    from app.models.email_upload import EmailRateLimit
    from sqlalchemy import delete
    
    try:
        async with AsyncSessionLocal() as session:
            # 删除7天前的记录
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            stmt = delete(EmailRateLimit).where(
                EmailRateLimit.last_daily_reset < cutoff_date
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 条过期的频率限制记录")
    
    except Exception as e:
        logger.error(f"清理频率限制记录失败: {e}")


async def cleanup_old_uploads():
    """清理过期的上传记录（可选）"""
    from app.core.database import AsyncSessionLocal
    from app.models.email_upload import EmailUpload, EmailUploadStatus
    from sqlalchemy import select, delete
    import os
    
    try:
        async with AsyncSessionLocal() as session:
            # 删除30天前被拒绝的记录
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # 先查询要删除的记录，以便删除对应的文件
            stmt = select(EmailUpload).where(
                EmailUpload.status == EmailUploadStatus.REJECTED,
                EmailUpload.processed_at < cutoff_date
            )
            
            result = await session.execute(stmt)
            old_uploads = result.scalars().all()
            
            # 删除文件
            for upload in old_uploads:
                try:
                    file_path = os.path.join(
                        settings.UPLOAD_DIR, 
                        "email_uploads", 
                        upload.stored_filename
                    )
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug(f"删除文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {upload.stored_filename}: {e}")
            
            # 删除数据库记录
            if old_uploads:
                delete_stmt = delete(EmailUpload).where(
                    EmailUpload.status == EmailUploadStatus.REJECTED,
                    EmailUpload.processed_at < cutoff_date
                )
                
                await session.execute(delete_stmt)
                await session.commit()
                
                logger.info(f"清理了 {len(old_uploads)} 条过期的上传记录")
    
    except Exception as e:
        logger.error(f"清理上传记录失败: {e}")


async def run_maintenance_tasks():
    """运行维护任务"""
    logger.info("开始运行邮件相关维护任务")
    
    await cleanup_old_rate_limits()
    await cleanup_old_uploads()
    
    logger.info("邮件相关维护任务完成")