"""
测试配置文件
提供测试所需的fixtures和配置
"""

import sys
from pathlib import Path

# 将项目根目录添加到sys.path
# 这确保了测试可以像应用一样找到模块
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from app.core.database import Base, get_db
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    # 使用内存SQLite数据库进行测试
    test_database_url = "sqlite+aiosqlite:///:memory:"
    
    engine = create_async_engine(
        test_database_url,
        echo=False,
        future=True
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine):
    """创建测试数据库会话"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
def override_get_db(test_db_session):
    """覆盖数据库依赖"""
    def _override_get_db():
        return test_db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def temp_upload_dir():
    """创建临时上传目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = temp_dir
        yield temp_dir
        settings.UPLOAD_DIR = original_upload_dir


@pytest.fixture
def mock_redis():
    """模拟Redis连接"""
    with patch('app.services.redis_service.redis_service') as mock_redis:
        mock_redis.is_connected.return_value = True
        mock_redis.cache_get.return_value = None
        mock_redis.cache_set.return_value = None
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = None
        yield mock_redis


@pytest.fixture
def mock_email_settings():
    """模拟邮件配置"""
    with patch.multiple(
        settings,
        EMAIL_UPLOAD_ENABLED=True,
        SMTP_HOST="smtp.test.com",
        SMTP_PORT=587,
        SMTP_USER="test@test.com",
        SMTP_PASSWORD="password",
        SMTP_TLS=True,
        IMAP_HOST="imap.test.com",
        IMAP_PORT=993,
        IMAP_USER="test@test.com",
        IMAP_PASSWORD="password",
        IMAP_USE_SSL=True,
        EMAIL_MAX_ATTACHMENT_SIZE=10*1024*1024,
        EMAIL_MAX_ATTACHMENT_COUNT=5,
        EMAIL_ALLOWED_EXTENSIONS=['.pdf', '.docx', '.txt'],
        EMAIL_HOURLY_LIMIT=5,
        EMAIL_DAILY_LIMIT=20,
        EMAIL_ALLOWED_DOMAINS=['test.com', 'example.com']
    ):
        yield


@pytest.fixture
def sample_email_data():
    """示例邮件数据"""
    return {
        'sender_email': 'user@test.com',
        'subject': '测试邮件主题',
        'body': '这是一封测试邮件的正文内容',
        'attachments': [
            {
                'filename': 'test_document.pdf',
                'data': b'PDF file content here',
                'size': 1024
            }
        ]
    }


@pytest.fixture
def sample_attachment_data():
    """示例附件数据"""
    return {
        'filename': 'test.pdf',
        'data': b'This is test file content for attachment testing',
        'size': 47,
        'mime_type': 'application/pdf'
    }


# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 标记单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 标记性能测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )


# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试项目"""
    for item in items:
        # 为异步测试添加asyncio标记
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # 根据测试名称自动添加标记
        if "test_performance" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.performance)
        
        if "test_integration" in item.name or "integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)