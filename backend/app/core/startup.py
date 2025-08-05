"""
应用启动和关闭事件处理
"""

import logging
from contextlib import asynccontextmanager

from app.core.database import init_db, close_db
from app.tasks.email_tasks import email_task_manager
from app.services.redis_service import redis_service
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")
        
        # 启动邮件检查任务
        if settings.EMAIL_UPLOAD_ENABLED:
            await email_task_manager.start_email_checking()
            logger.info("邮件检查任务启动完成")
        
        logger.info("应用启动完成")
        
        yield
        
    finally:
        # 关闭时执行
        logger.info("应用关闭中...")
        
        try:
            # 停止邮件检查任务
            await email_task_manager.stop_email_checking()
            logger.info("邮件检查任务已停止")
            
            # 关闭Redis连接
            await redis_service.close()
            logger.info("Redis连接已关闭")
            
            # 关闭数据库连接
            await close_db()
            logger.info("数据库连接已关闭")
            
        except Exception as e:
            logger.error(f"应用关闭时出错: {e}")
        
        logger.info("应用关闭完成")


async def startup_event():
    """启动事件处理（兼容旧版本FastAPI）"""
    logger.info("应用启动事件触发")
    
    # 初始化数据库
    await init_db()
    
    # 启动邮件检查任务
    if settings.EMAIL_UPLOAD_ENABLED:
        await email_task_manager.start_email_checking()


async def shutdown_event():
    """关闭事件处理（兼容旧版本FastAPI）"""
    logger.info("应用关闭事件触发")
    
    # 停止邮件检查任务
    await email_task_manager.stop_email_checking()
    
    # 关闭Redis连接
    await redis_service.close()
    
    # 关闭数据库连接
    await close_db()