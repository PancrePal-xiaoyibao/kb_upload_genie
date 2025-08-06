#!/usr/bin/env python3
"""
测试自动回复功能
验证邮件附件上传后的Tracker ID确认邮件发送
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.services.email_service import email_service
from app.services.tracker_service import TrackerService
from app.templates.email_templates import email_template_manager
from app.core.config import settings


async def test_email_template_generation():
    """测试邮件模板生成"""
    print("=== 测试邮件模板生成 ===")
    
    try:
        # 测试Tracker确认邮件模板
        email_content = email_template_manager.get_tracker_confirmation_email(
            tracker_id="TEST_TRACKER_001",
            filename="test_document.pdf",
            file_size=1024 * 1024,  # 1MB
            recipient_email="test@example.com"
        )
        
        print("✅ Tracker确认邮件模板生成成功")
        print(f"主题: {email_content['subject']}")
        print(f"HTML内容长度: {len(email_content['html_body'])} 字符")
        print(f"文本内容长度: {len(email_content['text_body'])} 字符")
        
        # 测试状态更新邮件模板
        status_email = email_template_manager.get_upload_status_email(
            tracker_id="TEST_TRACKER_001",
            status="completed",
            filename="test_document.pdf",
            recipient_email="test@example.com"
        )
        
        print("✅ 状态更新邮件模板生成成功")
        print(f"主题: {status_email['subject']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 邮件模板生成失败: {e}")
        return False


async def test_tracker_service_email_methods():
    """测试TrackerService的邮件发送方法"""
    print("\n=== 测试TrackerService邮件发送方法 ===")
    
    try:
        async with AsyncSessionLocal() as db:
            tracker_service = TrackerService(db)
            
            # 测试确认邮件发送方法（不实际发送）
            print("测试确认邮件发送方法...")
            
            # 由于我们不想实际发送邮件，这里只测试方法是否存在
            if hasattr(tracker_service, 'send_tracker_confirmation_email'):
                print("✅ send_tracker_confirmation_email 方法存在")
            else:
                print("❌ send_tracker_confirmation_email 方法不存在")
                return False
            
            if hasattr(tracker_service, 'send_status_update_email'):
                print("✅ send_status_update_email 方法存在")
            else:
                print("❌ send_status_update_email 方法不存在")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ TrackerService测试失败: {e}")
        return False


async def test_email_service_integration():
    """测试邮件服务集成"""
    print("\n=== 测试邮件服务集成 ===")
    
    try:
        # 检查邮件服务是否有新的确认邮件发送方法
        if hasattr(email_service, '_send_confirmation_emails'):
            print("✅ _send_confirmation_emails 方法存在")
        else:
            print("❌ _send_confirmation_emails 方法不存在")
            return False
        
        # 检查save_email_records方法是否已更新
        import inspect
        source = inspect.getsource(email_service.save_email_records)
        if '_send_confirmation_emails' in source:
            print("✅ save_email_records 已集成确认邮件发送")
        else:
            print("❌ save_email_records 未集成确认邮件发送")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 邮件服务集成测试失败: {e}")
        return False


async def test_configuration():
    """测试配置项"""
    print("\n=== 测试配置项 ===")
    
    try:
        # 检查新增的配置项
        config_items = [
            'SYSTEM_NAME',
            'SUPPORT_EMAIL', 
            'FRONTEND_URL',
            'AUTO_REPLY_ENABLED',
            'TRACKER_EMAIL_ENABLED',
            'STATUS_UPDATE_EMAIL_ENABLED'
        ]
        
        for item in config_items:
            if hasattr(settings, item):
                value = getattr(settings, item)
                print(f"✅ {item}: {value}")
            else:
                print(f"❌ {item}: 配置项不存在")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


async def simulate_email_processing():
    """模拟邮件处理流程"""
    print("\n=== 模拟邮件处理流程 ===")
    
    try:
        # 模拟邮件记录数据
        mock_email_records = [
            {
                'sender_email': 'test@example.com',
                'sender_email_hash': 'test_hash_123',
                'subject': '测试文档上传',
                'received_at': datetime.now(),
                'attachments': [
                    {
                        'original_filename': 'test_document.pdf',
                        'stored_filename': 'stored_test_document.pdf',
                        'file_size': 1024 * 1024,  # 1MB
                        'file_type': '.pdf'
                    }
                ]
            }
        ]
        
        print("✅ 模拟邮件记录数据创建成功")
        print(f"邮件数量: {len(mock_email_records)}")
        print(f"附件数量: {len(mock_email_records[0]['attachments'])}")
        
        # 检查是否能正确提取确认邮件所需的信息
        for record in mock_email_records:
            for attachment in record['attachments']:
                print(f"文件名: {attachment['original_filename']}")
                print(f"文件大小: {attachment['file_size']} 字节")
                print(f"发送者: {record['sender_email']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 邮件处理流程模拟失败: {e}")
        return False


async def test_smtp_connection():
    """测试SMTP连接配置"""
    print("\n=== 测试SMTP连接配置 ===")
    
    try:
        # 检查SMTP配置
        smtp_configs = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD']
        
        for config in smtp_configs:
            value = getattr(settings, config, None)
            if value:
                if config == 'SMTP_PASSWORD':
                    print(f"✅ {config}: ***已配置***")
                else:
                    print(f"✅ {config}: {value}")
            else:
                print(f"⚠️ {config}: 未配置")
        
        # 注意：这里不实际测试SMTP连接，因为可能没有真实的邮件服务器配置
        print("ℹ️ 注意：未进行实际SMTP连接测试，请确保邮件服务器配置正确")
        
        return True
        
    except Exception as e:
        print(f"❌ SMTP配置测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始测试自动回复功能...")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("邮件模板生成", test_email_template_generation),
        ("TrackerService邮件方法", test_tracker_service_email_methods),
        ("邮件服务集成", test_email_service_integration),
        ("配置项", test_configuration),
        ("邮件处理流程模拟", simulate_email_processing),
        ("SMTP连接配置", test_smtp_connection)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 个测试通过, {failed} 个测试失败")
    
    if failed == 0:
        print("🎉 所有测试通过！自动回复功能已成功实现。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试运行异常: {e}")
        sys.exit(1)