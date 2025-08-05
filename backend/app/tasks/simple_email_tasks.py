"""
简化的邮件任务
定期检查邮件并处理附件
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.simple_email_service import simple_email_service

logger = logging.getLogger(__name__)


class SimpleEmailTaskManager:
    """简化的邮件任务管理器"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 60  # 检查间隔（秒）
    
    async def start_email_monitoring(self):
        """启动邮件监控任务"""
        if self.is_running:
            logger.warning("邮件监控任务已在运行")
            return
        
        self.is_running = True
        logger.info("启动邮件监控任务")
        
        while self.is_running:
            try:
                await self._check_and_process_emails()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"邮件监控任务出错: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def stop_email_monitoring(self):
        """停止邮件监控任务"""
        self.is_running = False
        logger.info("停止邮件监控任务")
    
    async def _check_and_process_emails(self):
        """检查并处理新邮件"""
        try:
            # 获取数据库会话
            async for db in get_db():
                # 获取新邮件
                email_records = await simple_email_service.fetch_new_emails(db)
                
                if email_records:
                    # 保存邮件记录
                    await simple_email_service.save_email_records(email_records, db)
                    logger.info(f"处理了 {len(email_records)} 封新邮件")
                else:
                    logger.debug("没有新邮件")
                
                break  # 只需要一个数据库会话
                
        except Exception as e:
            logger.error(f"处理邮件时出错: {e}")
    
    async def process_single_check(self):
        """手动执行一次邮件检查"""
        logger.info("手动执行邮件检查")
        await self._check_and_process_emails()


# 创建全局任务管理器实例
simple_email_task_manager = SimpleEmailTaskManager()


async def start_background_tasks():
    """启动后台任务"""
    await simple_email_task_manager.start_email_monitoring()


async def stop_background_tasks():
    """停止后台任务"""
    await simple_email_task_manager.stop_email_monitoring()