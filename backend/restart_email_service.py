#!/usr/bin/env python3
"""
邮件服务重启脚本
用于在出现卡死问题时重启邮件检查服务
"""

import asyncio
import logging
from app.tasks.email_tasks import email_task_manager
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def restart_email_service():
    """重启邮件服务"""
    logger.info("🔄 开始重启邮件检查服务...")
    
    try:
        # 停止当前的邮件检查任务
        logger.info("⏹️ 停止当前邮件检查任务...")
        await email_task_manager.stop_email_checking()
        
        # 等待一小段时间确保任务完全停止
        await asyncio.sleep(2)
        
        # 重新启动邮件检查任务
        if settings.EMAIL_UPLOAD_ENABLED:
            logger.info("▶️ 重新启动邮件检查任务...")
            await email_task_manager.start_email_checking()
            logger.info("✅ 邮件检查服务重启成功")
        else:
            logger.warning("⚠️ 邮件上传功能未启用，跳过启动")
            
    except Exception as e:
        logger.error(f"❌ 邮件服务重启失败: {e}")
        raise


async def check_email_service_status():
    """检查邮件服务状态"""
    logger.info("📊 检查邮件服务状态...")
    
    try:
        # 获取统计信息
        stats = email_task_manager.stats
        
        logger.info("📈 邮件服务统计:")
        logger.info(f"  - 总处理邮件数: {stats.get('total_emails_processed', 0)}")
        logger.info(f"  - 总附件数: {stats.get('total_attachments_saved', 0)}")
        logger.info(f"  - 错误次数: {stats.get('errors_count', 0)}")
        logger.info(f"  - 最后检查时间: {stats.get('last_check_time', 'N/A')}")
        logger.info(f"  - 服务运行状态: {'运行中' if email_task_manager.running else '已停止'}")
        
        # 显示配置信息
        logger.info("⚙️ 邮件配置:")
        logger.info(f"  - 邮件上传启用: {settings.EMAIL_UPLOAD_ENABLED}")
        logger.info(f"  - 检查间隔: {settings.EMAIL_CHECK_INTERVAL}秒")
        logger.info(f"  - 允许域名: {settings.EMAIL_ALLOWED_DOMAINS}")
        logger.info(f"  - IMAP服务器: {settings.IMAP_HOST}:{settings.IMAP_PORT}")
        
    except Exception as e:
        logger.error(f"❌ 获取邮件服务状态失败: {e}")


async def main():
    """主函数"""
    logger.info("🚀 邮件服务管理工具启动")
    
    # 检查当前状态
    await check_email_service_status()
    
    # 重启服务
    await restart_email_service()
    
    # 再次检查状态
    await asyncio.sleep(3)
    await check_email_service_status()
    
    logger.info("🎉 邮件服务管理完成")


if __name__ == "__main__":
    asyncio.run(main())
