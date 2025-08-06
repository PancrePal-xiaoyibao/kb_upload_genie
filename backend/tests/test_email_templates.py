"""
邮件模板管理器单元测试
测试邮件模板的生成、渲染和错误处理
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any

from app.templates.email_templates import EmailTemplateManager, EmailTemplateError


class TestEmailTemplateManager:
    """邮件模板管理器测试类"""
    
    @pytest.fixture
    def template_manager(self):
        """创建测试用的模板管理器"""
        manager = EmailTemplateManager()
        return manager
    
    @pytest.fixture
    def sample_template_data(self):
        """示例模板数据"""
        return {
            'tracker_id': 'TEST123',
            'filename': 'test_file.pdf',
            'file_size': 1024 * 1024,  # 1MB
            'recipient_email': 'test@example.com',
            'upload_time': '2024-01-01 12:00:00',
            'query_url': 'http://localhost:3000/tracker/TEST123',
            'support_email': 'support@example.com',
            'system_name': '知识库上传系统'
        }
    
    @pytest.fixture
    def temp_template_dir(self):
        """创建临时模板目录"""
        temp_dir = tempfile.mkdtemp()
        
        # 创建测试模板文件
        html_content = """
        <html>
        <body>
            <h1>{{ system_name }}</h1>
            <p>Tracker ID: {{ tracker_id }}</p>
            <p>文件名: {{ filename }}</p>
            <p>文件大小: {{ file_size }}</p>
        </body>
        </html>
        """
        
        text_content = """
        {{ system_name }}
        Tracker ID: {{ tracker_id }}
        文件名: {{ filename }}
        文件大小: {{ file_size }}
        """
        
        # 写入测试模板文件
        Path(temp_dir, 'tracker_confirmation.html').write_text(html_content, encoding='utf-8')
        Path(temp_dir, 'tracker_confirmation.txt').write_text(text_content, encoding='utf-8')
        Path(temp_dir, 'upload_success.html').write_text(html_content, encoding='utf-8')
        Path(temp_dir, 'upload_success.txt').write_text(text_content, encoding='utf-8')
        Path(temp_dir, 'upload_failed.html').write_text(html_content, encoding='utf-8')
        Path(temp_dir, 'upload_failed.txt').write_text(text_content, encoding='utf-8')
        
        yield temp_dir
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
    
    def test_init(self):
        """测试初始化"""
        manager = EmailTemplateManager()
        
        assert manager.template_dir.exists()
        assert 'tracker_confirmation' in manager.templates
        assert 'upload_success' in manager.templates
        assert 'upload_failed' in manager.templates
        assert not manager._initialized
    
    def test_format_file_size(self, template_manager):
        """测试文件大小格式化"""
        manager = template_manager
        
        # 测试各种文件大小
        assert manager._format_file_size(0) == "0 B"
        assert manager._format_file_size(512) == "512 B"
        assert manager._format_file_size(1024) == "1.0 KB"
        assert manager._format_file_size(1024 * 1024) == "1.0 MB"
        assert manager._format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert manager._format_file_size(1536) == "1.5 KB"  # 1.5KB
        
        # 测试负数
        assert manager._format_file_size(-100) == "0 B"
    
    def test_get_status_text(self, template_manager):
        """测试状态文本获取"""
        manager = template_manager
        
        assert manager._get_status_text('pending') == '待处理'
        assert manager._get_status_text('processing') == '处理中'
        assert manager._get_status_text('completed') == '处理完成'
        assert manager._get_status_text('failed') == '处理失败'
        assert manager._get_status_text('unknown') == 'unknown'
        
        # 测试大小写不敏感
        assert manager._get_status_text('COMPLETED') == '处理完成'
    
    def test_get_available_templates(self, template_manager):
        """测试获取可用模板列表"""
        manager = template_manager
        templates = manager.get_available_templates()
        
        assert isinstance(templates, dict)
        assert 'tracker_confirmation' in templates
        assert 'upload_success' in templates
        assert 'upload_failed' in templates
        
        # 检查模板配置结构
        for template_name, config in templates.items():
            assert 'subject_template' in config
            assert 'html_template' in config
            assert 'text_template' in config
    
    @pytest.mark.asyncio
    async def test_validate_template_files_success(self, temp_template_dir):
        """测试模板文件验证成功"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        # 应该不抛出异常
        await manager._validate_template_files()
    
    @pytest.mark.asyncio
    async def test_validate_template_files_missing(self):
        """测试模板文件缺失"""
        manager = EmailTemplateManager()
        manager.template_dir = Path('/nonexistent/path')
        
        with pytest.raises(EmailTemplateError) as exc_info:
            await manager._validate_template_files()
        
        assert "邮件模板文件缺失" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_template_file_success(self, temp_template_dir):
        """测试加载模板文件成功"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        content = await manager._load_template_file('tracker_confirmation.html')
        assert 'system_name' in content
        assert 'tracker_id' in content
    
    @pytest.mark.asyncio
    async def test_load_template_file_not_found(self, template_manager):
        """测试加载不存在的模板文件"""
        manager = template_manager
        
        with pytest.raises(EmailTemplateError) as exc_info:
            await manager._load_template_file('nonexistent.html')
        
        assert "模板文件不存在" in str(exc_info.value)
    
    def test_render_subject_template(self, template_manager, sample_template_data):
        """测试主题模板渲染"""
        manager = template_manager
        
        subject_template = "文件上传确认 - Tracker ID: {{ tracker_id }}"
        result = manager._render_subject_template(subject_template, sample_template_data)
        
        assert result == "文件上传确认 - Tracker ID: TEST123"
    
    def test_render_subject_template_error(self, template_manager):
        """测试主题模板渲染错误"""
        manager = template_manager
        
        # 使用无效的模板语法
        subject_template = "文件上传确认 - {{ invalid_syntax"
        
        with pytest.raises(EmailTemplateError) as exc_info:
            manager._render_subject_template(subject_template, {})
        
        assert "主题模板渲染失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_tracker_confirmation_email(self, temp_template_dir):
        """测试生成Tracker确认邮件"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        result = await manager.get_tracker_confirmation_email(
            tracker_id='TEST123',
            filename='test.pdf',
            file_size=1024,
            recipient_email='test@example.com'
        )
        
        assert isinstance(result, dict)
        assert 'subject' in result
        assert 'html_body' in result
        assert 'text_body' in result
        
        assert 'TEST123' in result['subject']
        assert 'TEST123' in result['html_body']
        assert 'TEST123' in result['text_body']
        assert '1.0 KB' in result['html_body']  # 文件大小格式化
    
    @pytest.mark.asyncio
    async def test_get_upload_status_email_success(self, temp_template_dir):
        """测试生成上传成功状态邮件"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        result = await manager.get_upload_status_email(
            tracker_id='TEST123',
            status='completed',
            filename='test.pdf',
            recipient_email='test@example.com'
        )
        
        assert isinstance(result, dict)
        assert 'subject' in result
        assert 'html_body' in result
        assert 'text_body' in result
        
        assert 'test.pdf' in result['subject']
        assert 'TEST123' in result['html_body']
    
    @pytest.mark.asyncio
    async def test_get_upload_status_email_failed(self, temp_template_dir):
        """测试生成上传失败状态邮件"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        result = await manager.get_upload_status_email(
            tracker_id='TEST123',
            status='failed',
            filename='test.pdf',
            recipient_email='test@example.com',
            error_message='文件处理失败'
        )
        
        assert isinstance(result, dict)
        assert 'subject' in result
        assert 'html_body' in result
        assert 'text_body' in result
        
        assert 'test.pdf' in result['subject']
        assert 'TEST123' in result['html_body']
    
    @pytest.mark.asyncio
    async def test_reload_templates(self, temp_template_dir):
        """测试重新加载模板"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        # 初始化
        await manager.initialize()
        
        # 重新加载应该成功
        await manager.reload_templates()
        
        # 验证缓存被清除
        assert len(manager._template_cache) == 0
    
    @pytest.mark.asyncio
    async def test_validate_template_syntax_valid(self, temp_template_dir):
        """测试验证有效的模板语法"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        result = await manager.validate_template_syntax('tracker_confirmation')
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_template_syntax_invalid(self, template_manager):
        """测试验证无效的模板"""
        manager = template_manager
        
        result = await manager.validate_template_syntax('nonexistent_template')
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert '模板不存在' in result['errors'][0]
    
    @pytest.mark.asyncio
    async def test_concurrent_template_rendering(self, temp_template_dir):
        """测试并发模板渲染"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        # 创建多个并发任务
        tasks = []
        for i in range(5):
            task = manager.get_tracker_confirmation_email(
                tracker_id=f'TEST{i}',
                filename=f'test{i}.pdf',
                file_size=1024 * (i + 1),
                recipient_email=f'test{i}@example.com'
            )
            tasks.append(task)
        
        # 并发执行
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == 5
        for i, result in enumerate(results):
            assert f'TEST{i}' in result['subject']
            assert f'test{i}.pdf' in result['html_body']
    
    @pytest.mark.asyncio
    async def test_template_error_handling(self, template_manager):
        """测试模板错误处理"""
        manager = template_manager
        
        # 模拟模板文件不存在的情况
        with patch.object(manager, '_validate_template_files', side_effect=EmailTemplateError("测试错误")):
            with pytest.raises(EmailTemplateError):
                await manager.get_tracker_confirmation_email(
                    tracker_id='TEST123',
                    filename='test.pdf',
                    file_size=1024,
                    recipient_email='test@example.com'
                )
    
    def test_template_cache(self, template_manager):
        """测试模板缓存功能"""
        manager = template_manager
        
        # 第一次调用
        template1 = manager._get_jinja_template('tracker_confirmation.html')
        
        # 第二次调用应该返回缓存的模板
        template2 = manager._get_jinja_template('tracker_confirmation.html')
        
        # 应该是同一个对象（缓存生效）
        assert template1 is template2
    
    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, temp_template_dir):
        """测试初始化的幂等性"""
        manager = EmailTemplateManager()
        manager.template_dir = Path(temp_template_dir)
        
        # 多次初始化应该是安全的
        await manager.initialize()
        await manager.initialize()
        await manager.initialize()
        
        assert manager._initialized is True


class TestEmailTemplateManagerIntegration:
    """邮件模板管理器集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_email_generation_workflow(self):
        """测试完整的邮件生成工作流"""
        manager = EmailTemplateManager()
        
        # 测试Tracker确认邮件
        tracker_email = await manager.get_tracker_confirmation_email(
            tracker_id='INTEGRATION_TEST_123',
            filename='integration_test.pdf',
            file_size=2048,
            recipient_email='integration@example.com'
        )
        
        # 验证邮件内容
        assert 'INTEGRATION_TEST_123' in tracker_email['subject']
        assert 'integration_test.pdf' in tracker_email['html_body']
        assert '2.0 KB' in tracker_email['html_body']
        
        # 测试成功状态邮件
        success_email = await manager.get_upload_status_email(
            tracker_id='INTEGRATION_TEST_123',
            status='completed',
            filename='integration_test.pdf',
            recipient_email='integration@example.com'
        )
        
        assert 'integration_test.pdf' in success_email['subject']
        assert '处理完成' in success_email['html_body']
        
        # 测试失败状态邮件
        failed_email = await manager.get_upload_status_email(
            tracker_id='INTEGRATION_TEST_123',
            status='failed',
            filename='integration_test.pdf',
            recipient_email='integration@example.com',
            error_message='集成测试错误'
        )
        
        assert 'integration_test.pdf' in failed_email['subject']
        assert '处理失败' in failed_email['html_body']
        assert '集成测试错误' in failed_email['html_body']
    
    @pytest.mark.asyncio
    async def test_template_manager_singleton_behavior(self):
        """测试模板管理器单例行为"""
        from app.templates.email_templates import email_template_manager
        
        # 全局实例应该可以正常工作
        result = await email_template_manager.get_tracker_confirmation_email(
            tracker_id='SINGLETON_TEST',
            filename='singleton_test.pdf',
            file_size=1024,
            recipient_email='singleton@example.com'
        )
        
        assert 'SINGLETON_TEST' in result['subject']
        assert isinstance(result, dict)
        assert all(key in result for key in ['subject', 'html_body', 'text_body'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])