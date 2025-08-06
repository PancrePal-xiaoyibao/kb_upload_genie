#!/usr/bin/env python3
"""
测试邮件发送功能
验证SMTP连接和邮件模板渲染是否正常工作
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.email_service import email_service
from app.services.tracker_service import TrackerService
from app.templates.email_templates import email_template_manager
from app.core.database import get_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_smtp_connection():
    """测试SMTP连接"""
    logger.info("=== 测试SMTP连接 ===")
    
    try:
        success = await email_service.connect_smtp()
        if success:
            logger.info("✅ SMTP连接成功")
            await email_service.disconnect_smtp()
            return True
        else:
            logger.error("❌ SMTP连接失败")
            return False
    except Exception as e:
        logger.error(f"❌ SMTP连接异常: {e}")
        return False


async def test_email_template_rendering():
    """测试邮件模板渲染"""
    logger.info("=== 测试邮件模板渲染 ===")
    
    try:
        # 测试tracker确认邮件模板
        email_content = await email_template_manager.get_tracker_confirmation_email(
            tracker_id="TEST_12345",
            filename="test_document.pdf",
            file_size=1024000,  # 1MB
            recipient_email="test@example.com"
        )
        
        logger.info("✅ 邮件模板渲染成功")
        logger.info(f"邮件主题: {email_content['subject']}")
        logger.info(f"HTML内容长度: {len(email_content['html_body'])} 字符")
        logger.info(f"文本内容长度: {len(email_content['text_body'])} 字符")
        
        # 检查关键内容是否存在
        if "TEST_12345" in email_content['html_body'] and "test_document.pdf" in email_content['html_body']:
            logger.info("✅ 模板变量替换正确")
            return True
        else:
            logger.error("❌ 模板变量替换失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 邮件模板渲染异常: {e}")
        return False


async def test_send_test_email():
    """发送测试邮件"""
    logger.info("=== 发送测试邮件 ===")
    
    # 使用管理员邮箱作为测试收件人
    test_email = settings.ADMIN_EMAIL
    
    try:
        # 连接SMTP
        if not await email_service.connect_smtp():
            logger.error("❌ 无法连接SMTP服务器")
            return False
        
        # 生成邮件内容
        email_content = await email_template_manager.get_tracker_confirmation_email(
            tracker_id="TEST_EMAIL_12345",
            filename="测试文档.pdf",
            file_size=2048000,  # 2MB
            recipient_email=test_email
        )
        
        # 发送邮件
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.SMTP_USER
        msg['To'] = test_email
        msg['Subject'] = f"[测试] {email_content['subject']}"
        
        # 添加纯文本和HTML内容
        text_part = MIMEText(email_content['text_body'], 'plain', 'utf-8')
        html_part = MIMEText(email_content['html_body'], 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # 发送邮件
        await asyncio.to_thread(email_service.smtp_connection.send_message, msg)
        
        logger.info(f"✅ 测试邮件发送成功: {test_email}")
        
        # 断开连接
        await email_service.disconnect_smtp()
        return True
        
    except Exception as e:
        logger.error(f"❌ 发送测试邮件失败: {e}")
        try:
            await email_service.disconnect_smtp()
        except:
            pass
        return False


async def test_tracker_service_integration():
    """测试TrackerService集成"""
    logger.info("=== 测试TrackerService集成 ===")
    
    try:
        # 创建数据库会话
        async for db in get_db():
            tracker_service = TrackerService(db)
            
            # 测试发送确认邮件
            success = await tracker_service.send_tracker_confirmation_email(
                tracker_id="INTEGRATION_TEST_12345",
                recipient_email=settings.ADMIN_EMAIL,
                filename="集成测试文档.pdf",
                file_size=1536000,  # 1.5MB
                use_existing_connection=False
            )
            
            if success:
                logger.info("✅ TrackerService集成测试成功")
                return True
            else:
                logger.error("❌ TrackerService集成测试失败")
                return False
            
    except Exception as e:
        logger.error(f"❌ TrackerService集成测试异常: {e}")
        return False


async def main():
    """主测试函数"""
    logger.info("开始邮件发送功能测试...")
    
    # 检查配置
    logger.info(f"SMTP配置: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    logger.info(f"SMTP用户: {settings.SMTP_USER}")
    logger.info(f"使用SSL: {settings.SMTP_PORT == 465}")
    logger.info(f"使用TLS: {settings.SMTP_TLS}")
    
    tests = [
        ("SMTP连接测试", test_smtp_connection),
        ("邮件模板渲染测试", test_email_template_rendering),
        ("发送测试邮件", test_send_test_email),
        ("TrackerService集成测试", test_tracker_service_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 发生异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    logger.info(f"\n{'='*50}")
    logger.info("测试结果汇总")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        logger.info("🎉 所有测试通过！邮件发送功能正常工作。")
        return True
    else:
        logger.error("⚠️  部分测试失败，请检查配置和网络连接。")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)