"""
邮件模板管理器集成测试
测试与实际邮件服务的集成
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any

from app.templates.email_templates import EmailTemplateManager, EmailTemplateError, email_template_manager
from app.core.config import settings


class TestEmailTemplateIntegration:
    """邮件模板集成测试类"""
    
    @pytest.mark.asyncio
    async def test_real_template_files_exist(self):
        """测试真实的模板文件是否存在"""
        manager = EmailTemplateManager()
        
        # 检查模板目录是否存在
        assert manager.template_dir.exists(), f"模板目录不存在: {manager.template_dir}"
        
        # 检查所有必需的模板文件
        for template_name, config in manager.templates.items():
            html_path = manager.template_dir / config['html_template']
            text_path = manager.template_dir / config['text_template']
            
            assert html_path.exists(), f"HTML模板文件不存在: {html_path}"
            assert text_path.exists(), f"文本模板文件不存在: {text_path}"
    
    @pytest.mark.asyncio
    async def test_real_template_syntax_validation(self):
        """测试真实模板文件的语法验证"""
        manager = EmailTemplateManager()
        
        for template_name in manager.templates.keys():
            result = await manager.validate_template_syntax(template_name)
            assert result['valid'], f"模板语法无效 {template_name}: {result['errors']}"
    
    @pytest.mark.asyncio
    async def test_template_rendering_with_real_data(self):
        """使用真实数据测试模板渲染"""
        manager = EmailTemplateManager()
        
        # 测试数据
        test_data = {
            'tracker_id': 'REAL_TEST_12345',
            'filename': '测试文档.pdf',
            'file_size': 1024 * 1024 * 2,  # 2MB
            'recipient_email': 'test@example.com'
        }
        
        # 测试Tracker确认邮件
        tracker_email = await manager.get_tracker_confirmation_email(**test_data)
        
        # 验证邮件结构
        assert isinstance(tracker_email, dict)
        assert all(key in tracker_email for key in ['subject', 'html_body', 'text_body'])
        
        # 验证内容包含必要信息
        assert test_data['tracker_id'] in tracker_email['subject']
        assert test_data['filename'] in tracker_email['html_body']
        assert '2.0 MB' in tracker_email['html_body']  # 文件大小格式化
        assert settings.SYSTEM_NAME in tracker_email['html_body']
        
        # 验证HTML和文本版本都包含关键信息
        for content in [tracker_email['html_body'], tracker_email['text_body']]:
            assert test_data['tracker_id'] in content
            assert test_data['filename'] in content
            assert test_data['recipient_email'] in content
    
    @pytest.mark.asyncio
    async def test_status_email_rendering_with_real_data(self):
        """使用真实数据测试状态邮件渲染"""
        manager = EmailTemplateManager()
        
        test_data = {
            'tracker_id': 'STATUS_TEST_67890',
            'filename': '状态测试文档.docx',
            'recipient_email': 'status@example.com'
        }
        
        # 测试成功状态邮件
        success_email = await manager.get_upload_status_email(
            status='completed',
            error_message=None,
            **test_data
        )
        
        assert '处理完成' in success_email['html_body']
        assert test_data['filename'] in success_email['subject']
        
        # 测试失败状态邮件
        failed_email = await manager.get_upload_status_email(
            status='failed',
            error_message='文件格式不支持',
            **test_data
        )
        
        assert '处理失败' in failed_email['html_body']
        assert '文件格式不支持' in failed_email['html_body']
    
    @pytest.mark.asyncio
    async def test_template_performance(self):
        """测试模板渲染性能"""
        manager = EmailTemplateManager()
        
        import time
        
        # 预热
        await manager.get_tracker_confirmation_email(
            tracker_id='PERF_TEST',
            filename='perf_test.pdf',
            file_size=1024,
            recipient_email='perf@example.com'
        )
        
        # 性能测试
        start_time = time.time()
        
        tasks = []
        for i in range(10):
            task = manager.get_tracker_confirmation_email(
                tracker_id=f'PERF_TEST_{i}',
                filename=f'perf_test_{i}.pdf',
                file_size=1024 * (i + 1),
                recipient_email=f'perf{i}@example.com'
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 10个邮件模板渲染应该在合理时间内完成（比如2秒）
        assert duration < 2.0, f"模板渲染性能不佳，耗时: {duration}秒"
        assert len(results) == 10
        
        # 验证所有结果都正确
        for i, result in enumerate(results):
            assert f'PERF_TEST_{i}' in result['subject']
    
    @pytest.mark.asyncio
    async def test_template_with_special_characters(self):
        """测试包含特殊字符的模板渲染"""
        manager = EmailTemplateManager()
        
        # 包含特殊字符的测试数据
        test_data = {
            'tracker_id': 'SPECIAL_测试_123',
            'filename': '特殊字符文档_@#$%^&*().pdf',
            'file_size': 1024,
            'recipient_email': 'special@测试.com'
        }
        
        result = await manager.get_tracker_confirmation_email(**test_data)
        
        # 验证特殊字符被正确处理
        assert test_data['tracker_id'] in result['html_body']
        assert test_data['filename'] in result['html_body']
        assert test_data['recipient_email'] in result['html_body']
    
    @pytest.mark.asyncio
    async def test_template_with_empty_values(self):
        """测试包含空值的模板渲染"""
        manager = EmailTemplateManager()
        
        # 包含空值的测试数据
        test_data = {
            'tracker_id': 'EMPTY_TEST_123',
            'filename': '',
            'file_size': 0,
            'recipient_email': 'empty@example.com'
        }
        
        result = await manager.get_tracker_confirmation_email(**test_data)
        
        # 验证空值被正确处理
        assert test_data['tracker_id'] in result['html_body']
        assert '0 B' in result['html_body']  # 文件大小为0
    
    @pytest.mark.asyncio
    async def test_template_reload_functionality(self):
        """测试模板重新加载功能"""
        manager = EmailTemplateManager()
        
        # 初始渲染
        result1 = await manager.get_tracker_confirmation_email(
            tracker_id='RELOAD_TEST_1',
            filename='reload_test.pdf',
            file_size=1024,
            recipient_email='reload@example.com'
        )
        
        # 重新加载模板
        await manager.reload_templates()
        
        # 再次渲染
        result2 = await manager.get_tracker_confirmation_email(
            tracker_id='RELOAD_TEST_2',
            filename='reload_test.pdf',
            file_size=1024,
            recipient_email='reload@example.com'
        )
        
        # 验证重新加载后仍然正常工作
        assert 'RELOAD_TEST_1' in result1['subject']
        assert 'RELOAD_TEST_2' in result2['subject']
    
    @pytest.mark.asyncio
    async def test_global_template_manager_instance(self):
        """测试全局模板管理器实例"""
        # 使用全局实例
        result = await email_template_manager.get_tracker_confirmation_email(
            tracker_id='GLOBAL_TEST_123',
            filename='global_test.pdf',
            file_size=2048,
            recipient_email='global@example.com'
        )
        
        assert 'GLOBAL_TEST_123' in result['subject']
        assert 'global_test.pdf' in result['html_body']
        assert '2.0 KB' in result['html_body']
    
    @pytest.mark.asyncio
    async def test_template_with_configuration_values(self):
        """测试模板中配置值的使用"""
        manager = EmailTemplateManager()
        
        result = await manager.get_tracker_confirmation_email(
            tracker_id='CONFIG_TEST_123',
            filename='config_test.pdf',
            file_size=1024,
            recipient_email='config@example.com'
        )
        
        # 验证配置值被正确使用
        assert settings.SYSTEM_NAME in result['html_body']
        assert settings.SUPPORT_EMAIL in result['html_body']
        assert settings.FRONTEND_URL in result['html_body']
    
    @pytest.mark.asyncio
    async def test_concurrent_template_access(self):
        """测试并发模板访问"""
        manager = EmailTemplateManager()
        
        # 创建多个不同类型的并发任务
        tasks = []
        
        # Tracker确认邮件任务
        for i in range(3):
            task = manager.get_tracker_confirmation_email(
                tracker_id=f'CONCURRENT_TRACKER_{i}',
                filename=f'concurrent_{i}.pdf',
                file_size=1024 * (i + 1),
                recipient_email=f'concurrent{i}@example.com'
            )
            tasks.append(task)
        
        # 状态更新邮件任务
        for i in range(3):
            task = manager.get_upload_status_email(
                tracker_id=f'CONCURRENT_STATUS_{i}',
                status='completed' if i % 2 == 0 else 'failed',
                filename=f'status_{i}.pdf',
                recipient_email=f'status{i}@example.com',
                error_message='测试错误' if i % 2 == 1 else None
            )
            tasks.append(task)
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks)
        
        # 验证所有结果
        assert len(results) == 6
        
        # 验证Tracker确认邮件结果
        for i in range(3):
            assert f'CONCURRENT_TRACKER_{i}' in results[i]['subject']
        
        # 验证状态更新邮件结果
        for i in range(3, 6):
            status_index = i - 3
            assert f'CONCURRENT_STATUS_{status_index}' in results[i]['html_body']


class TestEmailTemplateErrorHandling:
    """邮件模板错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_template_file_corruption_handling(self):
        """测试模板文件损坏的处理"""
        manager = EmailTemplateManager()
        
        # 模拟模板文件损坏
        with patch.object(manager, '_load_template_file', side_effect=EmailTemplateError("文件损坏")):
            with pytest.raises(EmailTemplateError) as exc_info:
                await manager.get_tracker_confirmation_email(
                    tracker_id='CORRUPT_TEST',
                    filename='corrupt_test.pdf',
                    file_size=1024,
                    recipient_email='corrupt@example.com'
                )
            
            assert "文件损坏" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_jinja_template_syntax_error_handling(self):
        """测试Jinja2模板语法错误处理"""
        manager = EmailTemplateManager()
        
        # 创建临时目录和损坏的模板文件
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.template_dir = Path(temp_dir)
            
            # 创建语法错误的模板
            broken_html = "{{ broken_syntax"
            Path(temp_dir, 'tracker_confirmation.html').write_text(broken_html, encoding='utf-8')
            Path(temp_dir, 'tracker_confirmation.txt').write_text("正常文本", encoding='utf-8')
            Path(temp_dir, 'upload_success.html').write_text("<html>正常</html>", encoding='utf-8')
            Path(temp_dir, 'upload_success.txt').write_text("正常文本", encoding='utf-8')
            Path(temp_dir, 'upload_failed.html').write_text("<html>正常</html>", encoding='utf-8')
            Path(temp_dir, 'upload_failed.txt').write_text("正常文本", encoding='utf-8')
            
            with pytest.raises(EmailTemplateError):
                await manager.get_tracker_confirmation_email(
                    tracker_id='SYNTAX_ERROR_TEST',
                    filename='syntax_error.pdf',
                    file_size=1024,
                    recipient_email='syntax@example.com'
                )
    
    @pytest.mark.asyncio
    async def test_network_timeout_simulation(self):
        """模拟网络超时情况"""
        manager = EmailTemplateManager()
        
        # 模拟异步操作超时
        with patch('asyncio.gather', side_effect=asyncio.TimeoutError("操作超时")):
            with pytest.raises(asyncio.TimeoutError):
                await manager.get_tracker_confirmation_email(
                    tracker_id='TIMEOUT_TEST',
                    filename='timeout_test.pdf',
                    file_size=1024,
                    recipient_email='timeout@example.com'
                )
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """测试内存压力下的处理"""
        manager = EmailTemplateManager()
        
        # 创建大量并发任务来模拟内存压力
        tasks = []
        for i in range(50):  # 创建50个并发任务
            task = manager.get_tracker_confirmation_email(
                tracker_id=f'MEMORY_TEST_{i}',
                filename=f'memory_test_{i}.pdf',
                file_size=1024 * 1024,  # 1MB
                recipient_email=f'memory{i}@example.com'
            )
            tasks.append(task)
        
        # 应该能够处理大量并发请求而不崩溃
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 检查是否有异常
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"发现异常: {exceptions}"
        
        # 验证所有结果都正确
        valid_results = [r for r in results if isinstance(r, dict)]
        assert len(valid_results) == 50


class TestEmailTemplatePerformance:
    """邮件模板性能测试"""
    
    @pytest.mark.asyncio
    async def test_template_caching_performance(self):
        """测试模板缓存性能"""
        manager = EmailTemplateManager()
        
        import time
        
        # 第一次渲染（冷启动）
        start_time = time.time()
        await manager.get_tracker_confirmation_email(
            tracker_id='CACHE_TEST_1',
            filename='cache_test.pdf',
            file_size=1024,
            recipient_email='cache@example.com'
        )
        cold_start_time = time.time() - start_time
        
        # 后续渲染（缓存命中）
        start_time = time.time()
        for i in range(10):
            await manager.get_tracker_confirmation_email(
                tracker_id=f'CACHE_TEST_{i+2}',
                filename='cache_test.pdf',
                file_size=1024,
                recipient_email='cache@example.com'
            )
        cached_time = (time.time() - start_time) / 10
        
        # 缓存命中应该比冷启动快
        assert cached_time < cold_start_time, f"缓存性能不佳: 冷启动{cold_start_time:.3f}s, 缓存{cached_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_large_file_size_handling(self):
        """测试大文件大小的处理"""
        manager = EmailTemplateManager()
        
        # 测试各种大小的文件
        file_sizes = [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            1024 * 1024 * 100,  # 100MB
            1024 * 1024 * 1024,  # 1GB
            1024 * 1024 * 1024 * 10,  # 10GB
        ]
        
        for size in file_sizes:
            result = await manager.get_tracker_confirmation_email(
                tracker_id=f'SIZE_TEST_{size}',
                filename=f'large_file_{size}.pdf',
                file_size=size,
                recipient_email='size@example.com'
            )
            
            # 验证文件大小格式化正确
            assert 'SIZE_TEST_' in result['subject']
            # 文件大小应该被正确格式化
            size_str = manager._format_file_size(size)
            assert size_str in result['html_body']
    
    @pytest.mark.asyncio
    async def test_unicode_handling_performance(self):
        """测试Unicode字符处理性能"""
        manager = EmailTemplateManager()
        
        # 包含各种Unicode字符的测试数据
        unicode_test_cases = [
            ('中文测试', '测试文档.pdf'),
            ('日本語テスト', 'テストファイル.pdf'),
            ('한국어 테스트', '테스트 파일.pdf'),
            ('العربية اختبار', 'ملف اختبار.pdf'),
            ('Русский тест', 'тестовый файл.pdf'),
            ('🚀🎉📁', 'emoji_file_📄.pdf'),
        ]
        
        import time
        start_time = time.time()
        
        for i, (tracker_suffix, filename) in enumerate(unicode_test_cases):
            result = await manager.get_tracker_confirmation_email(
                tracker_id=f'UNICODE_TEST_{i}_{tracker_suffix}',
                filename=filename,
                file_size=1024,
                recipient_email='unicode@example.com'
            )
            
            # 验证Unicode字符被正确处理
            assert tracker_suffix in result['html_body']
            assert filename in result['html_body']
        
        duration = time.time() - start_time
        
        # Unicode处理应该在合理时间内完成
        assert duration < 1.0, f"Unicode处理性能不佳，耗时: {duration:.3f}秒"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
