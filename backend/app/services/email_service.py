"""
邮件服务
处理邮件发送和接收功能
"""

import imaplib
import email
import smtplib
import logging
import hashlib
import os
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.email_upload import EmailUpload, EmailUploadStatus, EmailRateLimit, EmailDomainRule
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.imap_connection = None
        self.smtp_connection = None
    
    async def connect_imap(self) -> bool:
        """连接到IMAP服务器"""
        try:
            if not all([settings.IMAP_HOST, settings.IMAP_USER, settings.IMAP_PASSWORD]):
                logger.error("IMAP配置不完整")
                return False
            
            # 创建IMAP连接
            if settings.IMAP_USE_SSL:
                self.imap_connection = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
            else:
                self.imap_connection = imaplib.IMAP4(settings.IMAP_HOST, settings.IMAP_PORT)
            
            # 登录
            self.imap_connection.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
            logger.info("IMAP连接成功")
            return True
            
        except Exception as e:
            logger.error(f"IMAP连接失败: {e}")
            return False
    
    async def disconnect_imap(self):
        """断开IMAP连接"""
        try:
            if self.imap_connection:
                self.imap_connection.close()
                self.imap_connection.logout()
                self.imap_connection = None
                logger.info("IMAP连接已断开")
        except Exception as e:
            logger.error(f"断开IMAP连接时出错: {e}")
    
    async def connect_smtp(self) -> bool:
        """连接到SMTP服务器"""
        try:
            if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
                logger.error("SMTP配置不完整")
                return False
            
            # 创建SMTP连接
            self.smtp_connection = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            
            if settings.SMTP_TLS:
                self.smtp_connection.starttls()
            
            self.smtp_connection.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            logger.info("SMTP连接成功")
            return True
            
        except Exception as e:
            logger.error(f"SMTP连接失败: {e}")
            return False
    
    async def disconnect_smtp(self):
        """断开SMTP连接"""
        try:
            if self.smtp_connection:
                self.smtp_connection.quit()
                self.smtp_connection = None
                logger.info("SMTP连接已断开")
        except Exception as e:
            logger.error(f"断开SMTP连接时出错: {e}")
    
    def _hash_email(self, email_address: str) -> str:
        """对邮箱地址进行哈希处理"""
        return hashlib.sha256(email_address.lower().encode()).hexdigest()
    
    def _decode_header(self, header_value: str) -> str:
        """解码邮件头部信息"""
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            return decoded_string
        except Exception as e:
            logger.error(f"解码邮件头部失败: {e}")
            return str(header_value)
    
    def _extract_domain(self, email_address: str) -> str:
        """提取邮箱域名"""
        return email_address.split('@')[-1].lower()
    
    async def _check_domain_allowed(self, email_address: str, db: AsyncSession) -> bool:
        """检查邮箱域名是否被允许"""
        try:
            domain = self._extract_domain(email_address)
            
            # 如果未启用域名白名单，则检查是否在配置的允许域名中
            if not settings.EMAIL_DOMAIN_WHITELIST_ENABLED:
                return domain in settings.EMAIL_ALLOWED_DOMAINS
            
            # 查询数据库中的域名规则
            from sqlalchemy import select
            result = await db.execute(
                select(EmailDomainRule).where(EmailDomainRule.domain == domain)
            )
            domain_rule = result.scalar_one_or_none()
            
            if domain_rule:
                return domain_rule.is_allowed
            
            # 如果没有找到规则，默认不允许
            return False
            
        except Exception as e:
            logger.error(f"检查域名权限失败: {e}")
            return False
    
    async def _check_rate_limit(self, email_address: str, db: AsyncSession) -> Tuple[bool, str]:
        """检查邮件发送频率限制"""
        try:
            email_hash = self._hash_email(email_address)
            
            # 尝试从Redis获取计数
            redis_key_hourly = f"email_rate:hourly:{email_hash}"
            redis_key_daily = f"email_rate:daily:{email_hash}"
            
            hourly_count = await redis_service.get(redis_key_hourly) or 0
            daily_count = await redis_service.get(redis_key_daily) or 0
            
            hourly_count = int(hourly_count)
            daily_count = int(daily_count)
            
            # 检查限制
            if hourly_count >= settings.EMAIL_HOURLY_LIMIT:
                return False, f"每小时发送限制已达到({settings.EMAIL_HOURLY_LIMIT}封)"
            
            if daily_count >= settings.EMAIL_DAILY_LIMIT:
                return False, f"每日发送限制已达到({settings.EMAIL_DAILY_LIMIT}封)"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"检查频率限制失败: {e}")
            return False, "系统错误"
    
    async def _increment_rate_limit(self, email_address: str):
        """增加频率限制计数"""
        try:
            email_hash = self._hash_email(email_address)
            
            redis_key_hourly = f"email_rate:hourly:{email_hash}"
            redis_key_daily = f"email_rate:daily:{email_hash}"
            
            # 增加计数并设置过期时间
            await redis_service.incr(redis_key_hourly)
            await redis_service.expire(redis_key_hourly, 3600)  # 1小时
            
            await redis_service.incr(redis_key_daily)
            await redis_service.expire(redis_key_daily, 86400)  # 24小时
            
        except Exception as e:
            logger.error(f"更新频率限制计数失败: {e}")
    
    async def _save_attachment(self, attachment_data: bytes, filename: str, sender_email: str) -> str:
        """保存附件到本地"""
        try:
            # 创建上传目录
            upload_dir = os.path.join(settings.UPLOAD_DIR, "email_attachments")
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            email_hash = self._hash_email(sender_email)[:8]
            file_ext = os.path.splitext(filename)[1]
            stored_filename = f"{timestamp}_{email_hash}_{filename}"
            
            file_path = os.path.join(upload_dir, stored_filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(attachment_data)
            
            logger.info(f"附件已保存: {stored_filename}")
            return stored_filename
            
        except Exception as e:
            logger.error(f"保存附件失败: {e}")
            raise
    
    async def _validate_attachment(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """验证附件"""
        try:
            # 检查文件大小
            if file_size > settings.EMAIL_MAX_ATTACHMENT_SIZE:
                return False, f"文件大小超过限制({settings.EMAIL_MAX_ATTACHMENT_SIZE / 1024 / 1024:.1f}MB)"
            
            # 检查文件扩展名
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in settings.EMAIL_ALLOWED_EXTENSIONS:
                return False, f"不支持的文件类型: {file_ext}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"验证附件失败: {e}")
            return False, "验证失败"
    
    async def send_limit_notification(self, to_email: str, limit_type: str):
        """发送限制通知邮件"""
        try:
            if not await self.connect_smtp():
                return False
            
            subject = "邮件发送频率限制通知"
            body = f"""
            您好，
            
            您的邮箱 {to_email} 已达到{limit_type}发送限制。
            
            为了继续上传文件，请访问我们的网页版本：
            {settings.HOST}:{settings.PORT}
            
            感谢您的理解。
            
            此邮件由系统自动发送，请勿回复。
            """
            
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            self.smtp_connection.send_message(msg)
            logger.info(f"限制通知邮件已发送至: {to_email}")
            
            await self.disconnect_smtp()
            return True
            
        except Exception as e:
            logger.error(f"发送限制通知邮件失败: {e}")
            return False
    
    async def fetch_new_emails(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """获取新邮件"""
        try:
            if not await self.connect_imap():
                return []
            
            # 选择邮箱
            self.imap_connection.select(settings.IMAP_MAILBOX)
            
            # 搜索未读邮件
            status, messages = self.imap_connection.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error("搜索邮件失败")
                return []
            
            email_ids = messages[0].split()
            processed_emails = []
            
            for email_id in email_ids:
                try:
                    # 获取邮件
                    status, msg_data = self.imap_connection.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # 解析邮件
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # 提取邮件信息
                    sender = self._decode_header(email_message.get('From', ''))
                    subject = self._decode_header(email_message.get('Subject', ''))
                    date_str = email_message.get('Date', '')
                    
                    # 提取发送者邮箱地址
                    sender_email = email.utils.parseaddr(sender)[1]
                    
                    if not sender_email:
                        logger.warning(f"无法提取发送者邮箱: {sender}")
                        continue
                    
                    # 跳过系统邮件地址
                    system_senders = settings.EMAIL_SYSTEM_SENDERS
                    if isinstance(system_senders, str):
                        system_senders = [s.strip() for s in system_senders.split(',')]
                    
                    is_system_email = any(sender_email.lower().startswith(prefix.lower()) for prefix in system_senders)
                    if is_system_email:
                        logger.info(f"跳过系统邮件: {sender_email}")
                        # 标记为已读但不处理
                        if settings.EMAIL_MARK_AS_READ:
                            self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
                        continue
                    
                    # 检查域名权限
                    if not await self._check_domain_allowed(sender_email, db):
                        logger.warning(f"域名不被允许: {sender_email}")
                        # 标记为已读
                        if settings.EMAIL_MARK_AS_READ:
                            self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
                        continue
                    
                    # 检查频率限制
                    rate_allowed, rate_message = await self._check_rate_limit(sender_email, db)
                    if not rate_allowed:
                        logger.warning(f"频率限制: {sender_email} - {rate_message}")
                        # 发送限制通知
                        await self.send_limit_notification(sender_email, rate_message.split('限制')[0])
                        continue
                    
                    # 处理附件
                    attachments = []
                    attachment_count = 0
                    
                    for part in email_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            attachment_count += 1
                            
                            # 检查附件数量限制
                            if attachment_count > settings.EMAIL_MAX_ATTACHMENT_COUNT:
                                logger.warning(f"附件数量超过限制: {sender_email}")
                                break
                            
                            filename = part.get_filename()
                            if filename:
                                filename = self._decode_header(filename)
                                attachment_data = part.get_payload(decode=True)
                                
                                if attachment_data:
                                    # 验证附件
                                    is_valid, validation_message = await self._validate_attachment(
                                        filename, len(attachment_data)
                                    )
                                    
                                    if not is_valid:
                                        logger.warning(f"附件验证失败: {filename} - {validation_message}")
                                        continue
                                    
                                    # 保存附件
                                    stored_filename = await self._save_attachment(
                                        attachment_data, filename, sender_email
                                    )
                                    
                                    attachments.append({
                                        'original_filename': filename,
                                        'stored_filename': stored_filename,
                                        'file_size': len(attachment_data),
                                        'file_type': os.path.splitext(filename)[1].lower()
                                    })
                    
                    if attachments:
                        # 增加频率限制计数
                        await self._increment_rate_limit(sender_email)
                        
                        # 保存邮件记录
                        email_record = {
                            'sender_email': sender_email,
                            'sender_email_hash': self._hash_email(sender_email),
                            'subject': subject,
                            'received_at': datetime.now(),
                            'attachments': attachments
                        }
                        
                        processed_emails.append(email_record)
                        
                        logger.info(f"处理邮件成功: {sender_email}, 附件数量: {len(attachments)}")
                    
                    # 标记为已读
                    if settings.EMAIL_MARK_AS_READ:
                        self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
                
                except Exception as e:
                    logger.error(f"处理邮件失败 {email_id}: {e}")
                    # 即使处理失败，也标记为已读以避免重复处理
                    try:
                        if settings.EMAIL_MARK_AS_READ:
                            self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
                    except Exception as mark_error:
                        logger.error(f"标记邮件为已读失败 {email_id}: {mark_error}")
                    continue
            
            await self.disconnect_imap()
            return processed_emails
            
        except Exception as e:
            logger.error(f"获取邮件失败: {e}")
            # 确保断开IMAP连接
            try:
                await self.disconnect_imap()
            except Exception as disconnect_error:
                logger.error(f"断开IMAP连接失败: {disconnect_error}")
            return []
    
    async def save_email_records(self, email_records: List[Dict[str, Any]], db: AsyncSession):
        """保存邮件记录到数据库"""
        try:
            for record in email_records:
                for attachment in record['attachments']:
                    email_upload = EmailUpload(
                        sender_email_hash=record['sender_email_hash'],
                        sender_email=record['sender_email'],  # 存储原始邮箱
                        original_filename=attachment['original_filename'],
                        stored_filename=attachment['stored_filename'],
                        file_size=attachment['file_size'],
                        file_type=attachment['file_type'],
                        email_subject=record['subject'],
                        status=EmailUploadStatus.PENDING,
                        received_at=record['received_at']
                    )
                    
                    db.add(email_upload)
            
            await db.commit()
            logger.info(f"保存了 {len(email_records)} 条邮件记录")
            
        except Exception as e:
            logger.error(f"保存邮件记录失败: {e}")
            await db.rollback()
            raise


# 创建全局邮件服务实例
email_service = EmailService()