
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from app.services.email_service import EmailService
from app.core.config import settings
from app.models.article import Article
from app.models.email_upload import EmailUpload
from sqlalchemy import select

# 模拟邮件内容
SENDER_EMAIL = "test.sender@ciallo.cv"
EMAIL_SUBJECT = "集成测试邮件"
ATTACHMENT_FILENAME = "test_attachment.txt"
ATTACHMENT_CONTENT = b"This is a test attachment."

def create_mock_email() -> bytes:
    """创建一个模拟的邮件，包含一个附件"""
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["Subject"] = EMAIL_SUBJECT
    msg.attach(MIMEText("这是一封测试邮件正文。"))

    attachment = MIMEApplication(ATTACHMENT_CONTENT)
    attachment.add_header("Content-Disposition", "attachment", filename=ATTACHMENT_FILENAME)
    msg.attach(attachment)
    
    return msg.as_bytes()

@pytest.mark.asyncio
@patch("app.services.email_service.imaplib.IMAP4_SSL")
@patch("app.services.email_service.smtplib.SMTP")
async def test_full_email_processing_flow(mock_smtp, mock_imap, db_session: AsyncSession):
    """
    集成测试：验证从接收邮件、处理附件、保存记录到发送确认邮件的完整流程。
    """
    # --- 1. 配置 Mock ---

    # 配置 IMAP mock
    mock_imap_instance = mock_imap.return_value
    mock_imap_instance.login = AsyncMock()
    mock_imap_instance.select = AsyncMock()
    mock_imap_instance.search.return_value = ("OK", [b"1"])  # 模拟一封未读邮件
    mock_imap_instance.fetch.return_value = ("OK", [(b"1 (RFC822)", create_mock_email())])
    mock_imap_instance.store = AsyncMock()
    mock_imap_instance.close = AsyncMock()
    mock_imap_instance.logout = AsyncMock()

    # 配置 SMTP mock
    mock_smtp_instance = mock_smtp.return_value
    mock_smtp_instance.starttls = MagicMock()
    mock_smtp_instance.login = MagicMock()
    mock_smtp_instance.send_message = MagicMock()
    mock_smtp_instance.quit = MagicMock()

    # --- 2. 执行邮件处理 ---
    
    # 允许测试域名
    original_domains = settings.EMAIL_ALLOWED_DOMAINS
    settings.EMAIL_ALLOWED_DOMAINS = ["ciallo.cv"]

    email_service = EmailService()
    
    # 模拟获取新邮件
    processed_emails = await email_service.fetch_new_emails(db_session)
    
    # 确认获取到邮件
    assert len(processed_emails) == 1
    assert processed_emails[0]["sender_email"] == SENDER_EMAIL
    assert len(processed_emails[0]["attachments"]) == 1
    
    # 保存邮件记录
    await email_service.save_email_records(processed_emails, db_session)

    # --- 3. 验证数据库状态 ---

    # 验证 Article 记录
    stmt_article = select(Article).where(Article.user_id == SENDER_EMAIL)
    result_article = await db_session.execute(stmt_article)
    article = result_article.scalar_one_or_none()
    
    assert article is not None
    assert article.title == EMAIL_SUBJECT
    assert article.user_id == SENDER_EMAIL
    assert article.github_url.startswith("email://")
    assert ATTACHMENT_FILENAME in article.github_url
    tracker_id = article.tracker_id

    # 验证 EmailUpload 记录
    stmt_upload = select(EmailUpload).where(EmailUpload.sender_email == SENDER_EMAIL)
    result_upload = await db_session.execute(stmt_upload)
    email_upload = result_upload.scalar_one_or_none()

    assert email_upload is not None
    assert email_upload.original_filename == ATTACHMENT_FILENAME

    # --- 4. 验证邮件发送 ---

    # 验证 SMTP 连接被调用
    mock_smtp.assert_called_once()
    mock_smtp_instance.login.assert_called_once()

    # 验证 send_message 被调用
    mock_smtp_instance.send_message.assert_called_once()
    
    # 验证发送的邮件内容
    sent_msg_args = mock_smtp_instance.send_message.call_args[0]
    sent_msg = sent_msg_args[0]
    
    assert sent_msg["To"] == SENDER_EMAIL
    assert "确认" in sent_msg["Subject"] or "Confirmation" in sent_msg["Subject"]
    assert tracker_id in str(sent_msg)

    # 验证 SMTP 断开连接被调用
    mock_smtp_instance.quit.assert_called_once()

    # 恢复原始配置
    settings.EMAIL_ALLOWED_DOMAINS = original_domains
