"""
简化的邮件服务
只处理邮件接收和附件保存功能
"""

import imaplib
import email
import logging
import os
import uuid
from datetime import datetime
from email.header import decode_header
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.simple_email_upload import SimpleEmailUpload
from app.models.article import Article, UploadMethod, ProcessingStatus, FileType
from app.utils.tracker_utils import generate_tracker_id

logger = logging.getLogger(__name__)


class SimpleEmailService:
    """简化的邮件服务类"""
    
    def __init__(self):
        self.imap_connection = None
    
    async def connect_imap(self) -> bool:
        """连接到IMAP服务器"""
        try:
            if not all([settings.IMAP_HOST, settings.IMAP_USER, settings.IMAP_PASSWORD]):
                logger.error("IMAP配置不完整")
                return False
            
            # 创建IMAP连接
            if getattr(settings, 'IMAP_USE_SSL', True):
                self.imap_connection = imaplib.IMAP4_SSL(
                    settings.IMAP_HOST, 
                    getattr(settings, 'IMAP_PORT', 993)
                )
            else:
                self.imap_connection = imaplib.IMAP4(
                    settings.IMAP_HOST, 
                    getattr(settings, 'IMAP_PORT', 143)
                )
            
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
    
    async def _save_attachment(self, attachment_data: bytes, filename: str, sender_email: str) -> tuple[str, str]:
        """保存附件到本地，返回存储文件名和完整路径"""
        try:
            # 创建上传目录
            upload_dir = os.path.join("uploads", "attachments")
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成唯一文件名
            file_ext = os.path.splitext(filename)[1]
            stored_filename = f"{uuid.uuid4()}{file_ext}"
            
            file_path = os.path.join(upload_dir, stored_filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(attachment_data)
            
            logger.info(f"附件已保存: {stored_filename}")
            return stored_filename, file_path
            
        except Exception as e:
            logger.error(f"保存附件失败: {e}")
            raise
    
    async def fetch_new_emails(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """获取新邮件并处理附件"""
        try:
            if not await self.connect_imap():
                return []
            
            # 选择邮箱
            mailbox = getattr(settings, 'IMAP_MAILBOX', 'INBOX')
            self.imap_connection.select(mailbox)
            
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
                    
                    # 提取发送者邮箱地址
                    sender_email = email.utils.parseaddr(sender)[1]
                    
                    if not sender_email:
                        logger.warning(f"无法提取发送者邮箱: {sender}")
                        continue
                    
                    # 处理附件
                    attachments = []
                    
                    for part in email_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            filename = part.get_filename()
                            if filename:
                                filename = self._decode_header(filename)
                                attachment_data = part.get_payload(decode=True)
                                
                                if attachment_data:
                                    # 保存附件
                                    stored_filename, file_path = await self._save_attachment(
                                        attachment_data, filename, sender_email
                                    )
                                    
                                    attachments.append({
                                        'original_filename': filename,
                                        'stored_filename': stored_filename,
                                        'file_path': file_path,
                                        'file_size': len(attachment_data),
                                        'file_type': os.path.splitext(filename)[1].lower()
                                    })
                    
                    if attachments:
                        # 保存邮件记录
                        email_record = {
                            'sender_email': sender_email,
                            'subject': subject,
                            'received_at': datetime.now(),
                            'attachments': attachments
                        }
                        
                        processed_emails.append(email_record)
                        logger.info(f"处理邮件成功: {sender_email}, 附件数量: {len(attachments)}")
                    
                    # 标记为已读
                    self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
                
                except Exception as e:
                    logger.error(f"处理邮件失败 {email_id}: {e}")
                    continue
            
            await self.disconnect_imap()
            return processed_emails
            
        except Exception as e:
            logger.error(f"获取邮件失败: {e}")
            return []
    
    async def save_email_records(self, email_records: List[Dict[str, Any]], db: AsyncSession):
        """保存邮件记录到数据库"""
        try:
            for record in email_records:
                for attachment in record['attachments']:
                    # 生成tracker_id
                    tracker_id = generate_tracker_id("SIMPLE")
                    
                    # 保存到simple_email_upload表
                    email_upload = SimpleEmailUpload(
                        sender_email=record['sender_email'],
                        original_filename=attachment['original_filename'],
                        stored_filename=attachment['stored_filename'],
                        file_path=attachment['file_path'],
                        file_size=attachment['file_size'],
                        file_type=attachment['file_type'],
                        email_subject=record['subject'],
                        uploaded_at=record['received_at']
                    )
                    
                    db.add(email_upload)
                    
                    # 同时保存到articles表以支持跟踪
                    article = Article(
                        title=record['subject'] or f"简单邮件附件: {attachment['original_filename']}",
                        description=f"通过简单邮件上传的附件: {attachment['original_filename']}",
                        github_url="",  # 邮件上传没有GitHub URL
                        github_owner="simple_email",
                        github_repo="attachments",
                        file_type=self._get_file_type_enum(attachment['file_type']),
                        file_size=attachment['file_size'],
                        user_id="system",  # 系统用户ID，需要根据实际情况调整
                        method=UploadMethod.SIMPLE_EMAIL,
                        tracker_id=tracker_id,
                        processing_status=ProcessingStatus.PENDING,
                        extra_metadata={
                            "sender_email": record['sender_email'],
                            "email_subject": record['subject'],
                            "original_filename": attachment['original_filename'],
                            "stored_filename": attachment['stored_filename'],
                            "file_path": attachment['file_path']
                        }
                    )
                    
                    db.add(article)
            
            await db.commit()
            logger.info(f"保存了 {sum(len(r['attachments']) for r in email_records)} 条附件记录和对应的文章记录")
            
        except Exception as e:
            logger.error(f"保存邮件记录失败: {e}")
            await db.rollback()
            raise
    
    def _get_file_type_enum(self, file_extension: str):
        """根据文件扩展名获取FileType枚举"""
        ext_mapping = {
            '.md': FileType.MARKDOWN,
            '.ipynb': FileType.JUPYTER,
            '.py': FileType.CODE,
            '.js': FileType.CODE,
            '.ts': FileType.CODE,
            '.java': FileType.CODE,
            '.cpp': FileType.CODE,
            '.c': FileType.CODE,
            '.txt': FileType.DOCUMENTATION,
            '.doc': FileType.DOCUMENTATION,
            '.docx': FileType.DOCUMENTATION,
            '.pdf': FileType.DOCUMENTATION,
            '.readme': FileType.README
        }
        
        return ext_mapping.get(file_extension.lower(), FileType.OTHER)


# 创建全局邮件服务实例
simple_email_service = SimpleEmailService()