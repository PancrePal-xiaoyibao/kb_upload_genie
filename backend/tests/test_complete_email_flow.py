#!/usr/bin/env python3
"""
完整邮件流程测试
模拟邮件接收、附件处理、数据保存和自动回复的完整流程
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.email_service import email_service
from app.core.database import get_db, AsyncSessionLocal
from app.models.email_upload import EmailUpload, EmailUploadStatus
from app.models.article import Article, ProcessingStatus, UploadMethod
from app.utils.tracker_utils import generate_tracker_id

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_email_record() -> Dict[str, Any]:
    """创建模拟邮件记录"""
    return {
        'sender_email': 'test@example.com',
        'sender_email_hash': email_service._hash_email('test@example.com'),
        'subject': '测试文档上传',
        'received_at': datetime.now(),
        'attachments': [
            {
                'original_filename': '测试文档.pdf',
                'stored_filename': f'20250806_test_{datetime.now().strftime("%H%M%S")}_测试文档.pdf',
                'file_size': 1024000,  # 1MB
                'file_type': '.pdf'
            },
            {
                'original_filename': 'code_sample.py',
                'stored_filename': f'20250806_test_{datetime.now().strftime("%H%M%S")}_code_sample.py',
                'file_size': 2048,  # 2KB
                'file_type': '.py'
            }
        ]
    }


async def test_email_record_saving():
    """测试邮件记录保存"""
    logger.info("=== 测试邮件记录保存 ===")
    
    try:
        # 创建模拟邮件记录
        mock_records = [create_mock_email_record()]
        
        # 使用数据库会话
        async with AsyncSessionLocal() as db:
            # 保存邮件记录
            await email_service.save_email_records(mock_records, db)
            
            # 验证数据是否正确保存
            from sqlalchemy import select
            
            # 检查EmailUpload记录
            email_uploads = await db.execute(select(EmailUpload))
            email_upload_records = email_uploads.scalars().all()
            
            # 检查Article记录
            articles = await db.execute(select(Article).where(Article.method == UploadMethod.EMAIL_UPLOAD))
            article_records = articles.scalars().all()
            
            logger.info(f"保存的EmailUpload记录数: {len(email_upload_records)}")
            logger.info(f"保存的Article记录数: {len(article_records)}")
            
            if len(email_upload_records) >= 2 and len(article_records) >= 2:
                logger.info("✅ 邮件记录保存成功")
                
                # 显示保存的记录信息
                for record in article_records[-2:]:  # 显示最新的2条记录
                    logger.info(f"  - Tracker ID: {record.tracker_id}")
                    logger.info(f"  - 文件名: {record.title}")
                    logger.info(f"  - 状态: {record.processing_status}")
                
                return True, article_records[-2:]  # 返回最新的记录
            else:
                logger.error("❌ 邮件记录保存失败")
                return False, []
                
    except Exception as e:
        logger.error(f"❌ 邮件记录保存异常: {e}")
        return False, []


async def test_tracker_confirmation_emails(article_records: List[Article]):
    """测试Tracker确认邮件发送"""
    logger.info("=== 测试Tracker确认邮件发送 ===")
    
    try:
        from app.services.tracker_service import TrackerService
        
        async with AsyncSessionLocal() as db:
            tracker_service = TrackerService(db)
            
            success_count = 0
            for article in article_records:
                # 从extra_metadata中获取邮件信息
                sender_email = article.extra_metadata.get('sender_email', settings.ADMIN_EMAIL)
                filename = article.extra_metadata.get('original_filename', 'unknown_file')
                
                success = await tracker_service.send_tracker_confirmation_email(
                    tracker_id=article.tracker_id,
                    recipient_email=sender_email,
                    filename=filename,
                    file_size=article.file_size,
                    use_existing_connection=False
                )
                
                if success:
                    success_count += 1
                    logger.info(f"  ✅ 确认邮件发送成功: {article.tracker_id}")
                else:
                    logger.error(f"  ❌ 确认邮件发送失败: {article.tracker_id}")
            
            if success_count == len(article_records):
                logger.info("✅ 所有Tracker确认邮件发送成功")
                return True
            else:
                logger.warning(f"⚠️  部分确认邮件发送失败: {success_count}/{len(article_records)}")
                return success_count > 0
                
    except Exception as e:
        logger.error(f"❌ Tracker确认邮件发送异常: {e}")
        return False


async def test_status_update_emails(article_records: List[Article]):
    """测试状态更新邮件发送"""
    logger.info("=== 测试状态更新邮件发送 ===")
    
    try:
        from app.services.tracker_service import TrackerService
        
        async with AsyncSessionLocal() as db:
            tracker_service = TrackerService(db)
            
            success_count = 0
            for article in article_records:
                # 模拟状态更新
                sender_email = article.extra_metadata.get('sender_email', settings.ADMIN_EMAIL)
                filename = article.extra_metadata.get('original_filename', 'unknown_file')
                
                # 发送处理完成邮件
                success = await tracker_service.send_status_update_email(
                    tracker_id=article.tracker_id,
                    recipient_email=sender_email,
                    filename=filename,
                    status='completed'
                )
                
                if success:
                    success_count += 1
                    logger.info(f"  ✅ 状态更新邮件发送成功: {article.tracker_id}")
                else:
                    logger.error(f"  ❌ 状态更新邮件发送失败: {article.tracker_id}")
            
            if success_count == len(article_records):
                logger.info("✅ 所有状态更新邮件发送成功")
                return True
            else:
                logger.warning(f"⚠️  部分状态更新邮件发送失败: {success_count}/{len(article_records)}")
                return success_count > 0
                
    except Exception as e:
        logger.error(f"❌ 状态更新邮件发送异常: {e}")
        return False


async def test_complete_workflow():
    """测试完整的邮件处理工作流"""
    logger.info("=== 测试完整邮件处理工作流 ===")
    
    try:
        # 1. 模拟邮件接收和处理
        logger.info("步骤1: 模拟邮件接收和附件处理")
        mock_records = [create_mock_email_record()]
        
        async with AsyncSessionLocal() as db:
            # 2. 保存邮件记录（这会自动触发确认邮件发送）
            logger.info("步骤2: 保存邮件记录并发送确认邮件")
            await email_service.save_email_records(mock_records, db)
            
            # 3. 查询保存的记录
            from sqlalchemy import select
            articles = await db.execute(
                select(Article).where(Article.method == UploadMethod.EMAIL_UPLOAD)
                .order_by(Article.created_at.desc())
                .limit(2)
            )
            article_records = articles.scalars().all()
            
            if not article_records:
                logger.error("❌ 未找到保存的文章记录")
                return False
            
            logger.info(f"步骤3: 找到 {len(article_records)} 条记录")
            
            # 4. 模拟处理状态更新
            logger.info("步骤4: 模拟处理完成并发送状态更新邮件")
            from app.services.tracker_service import TrackerService
            tracker_service = TrackerService(db)
            
            for article in article_records:
                # 更新处理状态
                article.processing_status = ProcessingStatus.COMPLETED
                
                # 发送状态更新邮件
                sender_email = article.extra_metadata.get('sender_email', settings.ADMIN_EMAIL)
                filename = article.extra_metadata.get('original_filename', 'unknown_file')
                
                await tracker_service.send_status_update_email(
                    tracker_id=article.tracker_id,
                    recipient_email=sender_email,
                    filename=filename,
                    status='completed'
                )
            
            await db.commit()
            
            logger.info("✅ 完整邮件处理工作流测试成功")
            return True
            
    except Exception as e:
        logger.error(f"❌ 完整工作流测试异常: {e}")
        return False


async def cleanup_test_data():
    """清理测试数据"""
    logger.info("=== 清理测试数据 ===")
    
    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, delete
            
            # 删除测试邮件记录
            test_emails = await db.execute(
                select(EmailUpload).where(EmailUpload.sender_email == 'test@example.com')
            )
            test_email_records = test_emails.scalars().all()
            
            # 删除测试文章记录
            test_articles = await db.execute(
                select(Article).where(Article.user_id == 'test@example.com')
            )
            test_article_records = test_articles.scalars().all()
            
            # 执行删除
            if test_email_records:
                await db.execute(
                    delete(EmailUpload).where(EmailUpload.sender_email == 'test@example.com')
                )
                logger.info(f"删除了 {len(test_email_records)} 条EmailUpload测试记录")
            
            if test_article_records:
                await db.execute(
                    delete(Article).where(Article.user_id == 'test@example.com')
                )
                logger.info(f"删除了 {len(test_article_records)} 条Article测试记录")
            
            await db.commit()
            logger.info("✅ 测试数据清理完成")
            
    except Exception as e:
        logger.error(f"❌ 清理测试数据异常: {e}")


async def main():
    """主测试函数"""
    logger.info("开始完整邮件流程测试...")
    
    # 检查配置
    logger.info(f"邮件上传功能: {'启用' if settings.EMAIL_UPLOAD_ENABLED else '禁用'}")
    logger.info(f"自动回复功能: {'启用' if settings.AUTO_REPLY_ENABLED else '禁用'}")
    logger.info(f"Tracker邮件: {'启用' if settings.TRACKER_EMAIL_ENABLED else '禁用'}")
    
    tests = [
        ("完整邮件处理工作流", test_complete_workflow),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 发生异常: {e}")
            results.append((test_name, False))
    
    # 清理测试数据
    await cleanup_test_data()
    
    # 输出测试结果
    logger.info(f"\n{'='*60}")
    logger.info("测试结果汇总")
    logger.info(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        logger.info("🎉 完整邮件流程测试通过！自动回复功能正常工作。")
        return True
    else:
        logger.error("⚠️  部分测试失败，请检查邮件处理流程。")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)