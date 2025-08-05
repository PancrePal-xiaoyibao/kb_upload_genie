"""
邮件上传功能测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.email_service import EmailService
from app.models.email_upload import EmailUpload, EmailUploadStatus, EmailRateLimit
from app.core.config import settings


class TestEmailService:
    """邮件服务测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.email_service = EmailService()
    
    def test_hash_email(self):
        """测试邮箱哈希功能"""
        email1 = "test@example.com"
        email2 = "TEST@EXAMPLE.COM"
        
        hash1 = self.email_service._hash_email(email1)
        hash2 = self.email_service._hash_email(email2)
        
        # 应该产生相同的哈希（不区分大小写）
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256哈希长度
    
    def test_is_allowed_domain(self):
        """测试域名白名单功能"""
        # 模拟配置
        with patch.object(settings, 'ALLOWED_EMAIL_DOMAINS', ['gmail.com', 'outlook.com']):
            assert self.email_service._is_allowed_domain('user@gmail.com') == True
            assert self.email_service._is_allowed_domain('user@outlook.com') == True
            assert self.email_service._is_allowed_domain('user@yahoo.com') == False
            assert self.email_service._is_allowed_domain('user@GMAIL.COM') == True  # 不区分大小写
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_new_user(self):
        """测试新用户的频率限制"""
        with patch('app.core.database.AsyncSessionLocal') as mock_session:
            # 模拟数据库会话
            mock_db = Mock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await self.email_service.check_rate_limit('test@example.com')
            
            assert result['allowed'] == True
            assert result['hourly_count'] == 1
            assert result['daily_count'] == 1
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """测试频率限制超出"""
        with patch('app.core.database.AsyncSessionLocal') as mock_session:
            # 模拟已存在的限制记录
            mock_rate_limit = Mock()
            mock_rate_limit.hourly_count = 5  # 已达到小时限制
            mock_rate_limit.daily_count = 10
            mock_rate_limit.last_hourly_reset = datetime.utcnow()
            mock_rate_limit.last_daily_reset = datetime.utcnow()
            
            mock_db = Mock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_rate_limit
            
            with patch.object(settings, 'EMAIL_RATE_LIMIT_HOURLY', 5):
                result = await self.email_service.check_rate_limit('test@example.com')
                
                assert result['allowed'] == False
                assert result['reason'] == 'hourly_limit'
    
    @pytest.mark.asyncio
    async def test_process_email_attachment_success(self):
        """测试成功处理邮件附件"""
        with patch('app.core.database.AsyncSessionLocal') as mock_session, \
             patch('aiofiles.open') as mock_file, \
             patch('os.makedirs'), \
             patch.object(self.email_service, '_is_allowed_domain', return_value=True), \
             patch.object(self.email_service, 'check_rate_limit', return_value={'allowed': True, 'hourly_count': 1, 'daily_count': 1}):
            
            mock_db = Mock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # 模拟文件数据
            attachment_data = b"test file content"
            filename = "test.pdf"
            
            with patch.object(settings, 'ALLOWED_FILE_TYPES', ['.pdf']), \
                 patch.object(settings, 'MAX_ATTACHMENT_SIZE', 1024):
                
                result = await self.email_service.process_email_attachment(
                    sender_email='test@gmail.com',
                    subject='Test Subject',
                    body='Test Body',
                    attachment_data=attachment_data,
                    filename=filename
                )
                
                assert result is not None  # 应该返回上传ID
    
    @pytest.mark.asyncio
    async def test_process_email_attachment_invalid_domain(self):
        """测试不允许的域名"""
        with patch.object(self.email_service, '_is_allowed_domain', return_value=False):
            result = await self.email_service.process_email_attachment(
                sender_email='test@invalid.com',
                subject='Test Subject',
                body='Test Body',
                attachment_data=b"test",
                filename='test.pdf'
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_process_email_attachment_rate_limited(self):
        """测试频率限制"""
        with patch.object(self.email_service, '_is_allowed_domain', return_value=True), \
             patch.object(self.email_service, 'check_rate_limit', return_value={'allowed': False, 'reason': 'hourly_limit'}), \
             patch.object(self.email_service, 'send_limit_notification') as mock_notify:
            
            result = await self.email_service.process_email_attachment(
                sender_email='test@gmail.com',
                subject='Test Subject',
                body='Test Body',
                attachment_data=b"test",
                filename='test.pdf'
            )
            
            assert result is None
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_email_attachment_file_too_large(self):
        """测试文件过大"""
        with patch.object(self.email_service, '_is_allowed_domain', return_value=True), \
             patch.object(self.email_service, 'check_rate_limit', return_value={'allowed': True}), \
             patch.object(settings, 'MAX_ATTACHMENT_SIZE', 10):  # 设置很小的限制
            
            large_data = b"x" * 100  # 100字节，超过10字节限制
            
            result = await self.email_service.process_email_attachment(
                sender_email='test@gmail.com',
                subject='Test Subject',
                body='Test Body',
                attachment_data=large_data,
                filename='test.pdf'
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_process_email_attachment_invalid_file_type(self):
        """测试不支持的文件类型"""
        with patch.object(self.email_service, '_is_allowed_domain', return_value=True), \
             patch.object(self.email_service, 'check_rate_limit', return_value={'allowed': True}), \
             patch.object(settings, 'ALLOWED_FILE_TYPES', ['.pdf']):
            
            result = await self.email_service.process_email_attachment(
                sender_email='test@gmail.com',
                subject='Test Subject',
                body='Test Body',
                attachment_data=b"test",
                filename='test.exe'  # 不支持的文件类型
            )
            
            assert result is None


class TestEmailUploadModels:
    """邮件上传模型测试"""
    
    def test_email_upload_status_enum(self):
        """测试邮件上传状态枚举"""
        assert EmailUploadStatus.PENDING == "pending"
        assert EmailUploadStatus.APPROVED == "approved"
        assert EmailUploadStatus.REJECTED == "rejected"
        assert EmailUploadStatus.PROCESSING == "processing"
    
    def test_email_upload_model_creation(self):
        """测试邮件上传模型创建"""
        upload = EmailUpload(
            sender_email_hash="test_hash",
            original_filename="test.pdf",
            stored_filename="stored_test.pdf",
            file_size=1024,
            file_type=".pdf",
            email_subject="Test Subject",
            email_body="Test Body",
            received_at=datetime.utcnow()
        )
        
        assert upload.sender_email_hash == "test_hash"
        assert upload.original_filename == "test.pdf"
        assert upload.status == EmailUploadStatus.PENDING  # 默认状态


if __name__ == '__main__':
    pytest.main([__file__])