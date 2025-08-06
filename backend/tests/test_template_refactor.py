#!/usr/bin/env python3
"""
测试邮件模板重构
验证从文件系统加载模板的功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.templates.email_templates import email_template_manager
from app.core.config import settings


async def test_template_file_loading():
    """测试模板文件加载"""
    print("=== 测试模板文件加载 ===")
    
    try:
        # 测试获取可用模板
        available_templates = email_template_manager.get_available_templates()
        print(f"✅ 可用模板数量: {len(available_templates)}")
        
        for name, config in available_templates.items():
            print(f"  - {name}: {config['html_file']}, {config['text_file']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板文件加载失败: {e}")
        return False


async def test_template_rendering():
    """测试模板渲染"""
    print("\n=== 测试模板渲染 ===")
    
    try:
        # 测试Tracker确认邮件
        email_content = email_template_manager.get_tracker_confirmation_email(
            tracker_id="TEST_REFACTOR_001",
            filename="test_refactor.pdf",
            file_size=2048 * 1024,  # 2MB
            recipient_email="test@example.com"
        )
        
        print("✅ Tracker确认邮件渲染成功")
        print(f"主题: {email_content['subject']}")
        print(f"HTML内容长度: {len(email_content['html_body'])} 字符")
        print(f"文本内容长度: {len(email_content['text_body'])} 字符")
        
        # 验证模板变量是否被正确替换
        if "TEST_REFACTOR_001" in email_content['html_body']:
            print("✅ HTML模板变量替换正确")
        else:
            print("❌ HTML模板变量替换失败")
            return False
        
        if "TEST_REFACTOR_001" in email_content['text_body']:
            print("✅ 文本模板变量替换正确")
        else:
            print("❌ 文本模板变量替换失败")
            return False
        
        # 测试状态更新邮件
        status_email = email_template_manager.get_upload_status_email(
            tracker_id="TEST_REFACTOR_001",
            status="completed",
            filename="test_refactor.pdf",
            recipient_email="test@example.com"
        )
        
        print("✅ 状态更新邮件渲染成功")
        print(f"主题: {status_email['subject']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板渲染失败: {e}")
        return False


async def test_template_reload():
    """测试模板重新加载"""
    print("\n=== 测试模板重新加载 ===")
    
    try:
        email_template_manager.reload_templates()
        print("✅ 模板重新加载成功")
        return True
        
    except Exception as e:
        print(f"❌ 模板重新加载失败: {e}")
        return False


async def test_file_system_integration():
    """测试文件系统集成"""
    print("\n=== 测试文件系统集成 ===")
    
    try:
        # 检查模板目录
        template_dir = email_template_manager.template_dir
        print(f"模板目录: {template_dir}")
        
        if template_dir.exists():
            print("✅ 模板目录存在")
        else:
            print("❌ 模板目录不存在")
            return False
        
        # 检查模板文件
        template_files = [
            'tracker_confirmation.html',
            'tracker_confirmation.txt',
            'upload_success.html',
            'upload_success.txt',
            'upload_failed.html',
            'upload_failed.txt'
        ]
        
        missing_files = []
        for filename in template_files:
            file_path = template_dir / filename
            if file_path.exists():
                print(f"✅ {filename} 存在")
            else:
                print(f"❌ {filename} 不存在")
                missing_files.append(filename)
        
        if missing_files:
            print(f"❌ 缺失模板文件: {missing_files}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 文件系统集成测试失败: {e}")
        return False


async def test_template_content_validation():
    """测试模板内容验证"""
    print("\n=== 测试模板内容验证 ===")
    
    try:
        # 生成测试邮件
        email_content = email_template_manager.get_tracker_confirmation_email(
            tracker_id="VALIDATION_TEST_001",
            filename="validation_test.docx",
            file_size=1024 * 1024,  # 1MB
            recipient_email="validation@example.com"
        )
        
        # 验证HTML内容
        html_body = email_content['html_body']
        required_elements = [
            'VALIDATION_TEST_001',
            'validation_test.docx',
            '1.0 MB',
            'validation@example.com',
            settings.SYSTEM_NAME,
            settings.SUPPORT_EMAIL
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in html_body:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ HTML模板缺失元素: {missing_elements}")
            return False
        else:
            print("✅ HTML模板内容验证通过")
        
        # 验证文本内容
        text_body = email_content['text_body']
        for element in required_elements:
            if element not in text_body:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ 文本模板缺失元素: {missing_elements}")
            return False
        else:
            print("✅ 文本模板内容验证通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板内容验证失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始测试邮件模板重构...")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("模板文件加载", test_template_file_loading),
        ("模板渲染", test_template_rendering),
        ("模板重新加载", test_template_reload),
        ("文件系统集成", test_file_system_integration),
        ("模板内容验证", test_template_content_validation)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
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
        print("🎉 邮件模板重构成功！所有测试通过。")
        print("\n✨ 重构优势:")
        print("  - 模板与代码分离，便于维护")
        print("  - 支持热重载，便于开发调试")
        print("  - HTML文件可直接预览")
        print("  - 模板文件可版本控制")
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