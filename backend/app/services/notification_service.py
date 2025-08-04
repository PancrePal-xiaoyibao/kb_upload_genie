"""
通知服务
处理邮件通知、超限提醒等功能
"""

import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional, Dict, Any, List
from jinja2 import Template

from app.core.config import settings
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务类"""
    
    def __init__(self):
        self.smtp_connection = None
        self.email_templates = {
            'rate_limit': self._get_rate_limit_template(),
            'file_rejected': self._get_file_rejected_template(),
            'domain_blocked': self._get_domain_blocked_template(),
            'upload_success': self._get_upload_success_template()
        }
    
    def _get_rate_limit_template(self) -> str:
        """获取频率限制邮件模板"""
        return """
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .content { background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .footer { margin-top: 20px; padding: 10px; font-size: 12px; color: #666; }
                .warning { color: #856404; background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; }
                .button { display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📧 邮件发送频率限制通知</h2>
                </div>
                <div class="content">
                    <p>您好，</p>
                    
                    <div class="warning">
                        <strong>⚠️ 发送频率限制</strong><br>
                        您的邮箱地址已达到发送频率限制：
                        <ul>
                            <li><strong>限制类型：</strong>{{ limit_type }}</li>
                            <li><strong>当前计数：</strong>{{ current_count }}</li>
                            <li><strong>限制数量：</strong>{{ limit_count }}</li>
                            <li><strong>重置时间：</strong>{{ reset_time }}</li>
                        </ul>
                    </div>
                    
                    <p>为了继续上传文件，您可以：</p>
                    <ol>
                        <li>等待限制重置后再次发送邮件</li>
                        <li>使用我们的网页版本直接上传文件</li>
                    </ol>
                    
                    <a href="{{ web_upload_url }}" class="button">🌐 访问网页版上传</a>
                    
                    <p>如有疑问，请联系我们的技术支持。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。<br>
                    发送时间：{{ send_time }}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_file_rejected_template(self) -> str:
        """获取文件拒绝邮件模板"""
        return """
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .content { background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .footer { margin-top: 20px; padding: 10px; font-size: 12px; color: #666; }
                .error { color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; }
                .button { display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>❌ 文件上传失败通知</h2>
                </div>
                <div class="content">
                    <p>您好，</p>
                    
                    <div class="error">
                        <strong>文件上传失败</strong><br>
                        您发送的邮件中的附件无法处理：
                        <ul>
                            <li><strong>文件名：</strong>{{ filename }}</li>
                            <li><strong>失败原因：</strong>{{ reason }}</li>
                            <li><strong>邮件主题：</strong>{{ subject }}</li>
                        </ul>
                    </div>
                    
                    <p><strong>常见问题解决方案：</strong></p>
                    <ul>
                        <li>文件大小超限：请确保单个文件不超过 {{ max_file_size }}MB</li>
                        <li>文件类型不支持：支持的文件类型包括 {{ allowed_types }}</li>
                        <li>文件数量超限：每封邮件最多包含 {{ max_file_count }} 个附件</li>
                    </ul>
                    
                    <a href="{{ web_upload_url }}" class="button">🌐 使用网页版上传</a>
                    
                    <p>如需帮助，请联系技术支持。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。<br>
                    发送时间：{{ send_time }}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_domain_blocked_template(self) -> str:
        """获取域名被阻止邮件模板"""
        return """
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .content { background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .footer { margin-top: 20px; padding: 10px; font-size: 12px; color: #666; }
                .warning { color: #856404; background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🚫 域名访问限制通知</h2>
                </div>
                <div class="content">
                    <p>您好，</p>
                    
                    <div class="warning">
                        <strong>域名访问受限</strong><br>
                        您的邮箱域名当前不在允许列表中：
                        <ul>
                            <li><strong>邮箱域名：</strong>{{ domain }}</li>
                            <li><strong>限制原因：</strong>{{ reason }}</li>
                        </ul>
                    </div>
                    
                    <p>如果您认为这是一个错误，请联系管理员申请将您的域名添加到白名单中。</p>
                    
                    <p>联系方式：{{ contact_email }}</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。<br>
                    发送时间：{{ send_time }}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_upload_success_template(self) -> str:
        """获取上传成功邮件模板"""
        return """
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .content { background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .footer { margin-top: 20px; padding: 10px; font-size: 12px; color: #666; }
                .success { color: #155724; background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 4px; }
                .file-list { background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✅ 文件上传成功通知</h2>
                </div>
                <div class="content">
                    <p>您好，</p>
                    
                    <div class="success">
                        <strong>文件上传成功！</strong><br>
                        您的邮件附件已成功接收并处理。
                    </div>
                    
                    <div class="file-list">
                        <strong>上传的文件：</strong>
                        <ul>
                        {% for file in files %}
                            <li>{{ file.filename }} ({{ file.size_mb }}MB)</li>
                        {% endfor %}
                        </ul>
                    </div>
                    
                    <p><strong>处理状态：</strong>{{ status }}</p>
                    <p><strong>上传时间：</strong>{{ upload_time }}</p>
                    
                    <p>您的文件正在审核中，审核完成后会有进一步通知。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。<br>
                    发送时间：{{ send_time }}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def _connect_smtp(self) -> bool:
        """连接SMTP服务器"""
        try:
            if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
                logger.error("SMTP配置不完整")
                return False
            
            self.smtp_connection = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            
            if settings.SMTP_TLS:
                self.smtp_connection.starttls()
            
            self.smtp_connection.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            logger.info("SMTP连接成功")
            return True
            
        except Exception as e:
            logger.error(f"SMTP连接失败: {e}")
            return False
    
    async def _disconnect_smtp(self):
        """断开SMTP连接"""
        try:
            if self.smtp_connection:
                self.smtp_connection.quit()
                self.smtp_connection = None
        except Exception as e:
            logger.error(f"断开SMTP连接失败: {e}")
    
    async def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """发送邮件"""
        try:
            if not await self._connect_smtp():
                return False
            
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加文本内容
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            self.smtp_connection.send_message(msg)
            logger.info(f"邮件发送成功: {to_email}")
            
            await self._disconnect_smtp()
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            await self._disconnect_smtp()
            return False
    
    async def send_rate_limit_notification(
        self, 
        to_email: str, 
        limit_type: str,
        current_count: int,
        limit_count: int,
        reset_time: str
    ) -> bool:
        """发送频率限制通知"""
        try:
            # 检查是否已经发送过通知（避免重复发送）
            cache_key = f"rate_limit_notification:{to_email}:{limit_type}"
            if await redis_service.cache_get(cache_key):
                logger.info(f"频率限制通知已发送过: {to_email}")
                return True
            
            # 准备模板数据
            template_data = {
                'limit_type': '每小时' if limit_type == 'hourly' else '每日',
                'current_count': current_count,
                'limit_count': limit_count,
                'reset_time': reset_time,
                'web_upload_url': f"http://{settings.HOST}:{settings.PORT}",
                'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 渲染邮件内容
            template = Template(self.email_templates['rate_limit'])
            html_content = template.render(**template_data)
            
            # 发送邮件
            subject = f"📧 邮件发送频率限制通知 - {template_data['limit_type']}"
            success = await self._send_email(to_email, subject, html_content)
            
            if success:
                # 缓存通知记录，避免重复发送（1小时内）
                await redis_service.cache_set(cache_key, "sent", 3600)
            
            return success
            
        except Exception as e:
            logger.error(f"发送频率限制通知失败: {e}")
            return False
    
    async def send_file_rejected_notification(
        self, 
        to_email: str, 
        filename: str,
        reason: str,
        subject: str = ""
    ) -> bool:
        """发送文件拒绝通知"""
        try:
            # 准备模板数据
            template_data = {
                'filename': filename,
                'reason': reason,
                'subject': subject,
                'max_file_size': settings.EMAIL_MAX_ATTACHMENT_SIZE // (1024 * 1024),
                'allowed_types': ', '.join(settings.EMAIL_ALLOWED_EXTENSIONS),
                'max_file_count': settings.EMAIL_MAX_ATTACHMENT_COUNT,
                'web_upload_url': f"http://{settings.HOST}:{settings.PORT}",
                'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 渲染邮件内容
            template = Template(self.email_templates['file_rejected'])
            html_content = template.render(**template_data)
            
            # 发送邮件
            email_subject = f"❌ 文件上传失败通知 - {filename}"
            return await self._send_email(to_email, email_subject, html_content)
            
        except Exception as e:
            logger.error(f"发送文件拒绝通知失败: {e}")
            return False
    
    async def send_domain_blocked_notification(
        self, 
        to_email: str, 
        domain: str,
        reason: str
    ) -> bool:
        """发送域名阻止通知"""
        try:
            # 准备模板数据
            template_data = {
                'domain': domain,
                'reason': reason,
                'contact_email': settings.SMTP_USER,
                'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 渲染邮件内容
            template = Template(self.email_templates['domain_blocked'])
            html_content = template.render(**template_data)
            
            # 发送邮件
            subject = f"🚫 域名访问限制通知 - {domain}"
            return await self._send_email(to_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"发送域名阻止通知失败: {e}")
            return False
    
    async def send_upload_success_notification(
        self, 
        to_email: str, 
        files: List[Dict[str, Any]],
        status: str = "待审核"
    ) -> bool:
        """发送上传成功通知"""
        try:
            # 准备文件信息
            file_list = []
            for file_info in files:
                file_list.append({
                    'filename': file_info.get('filename', ''),
                    'size_mb': round(file_info.get('size', 0) / (1024 * 1024), 2)
                })
            
            # 准备模板数据
            template_data = {
                'files': file_list,
                'status': status,
                'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 渲染邮件内容
            template = Template(self.email_templates['upload_success'])
            html_content = template.render(**template_data)
            
            # 发送邮件
            subject = f"✅ 文件上传成功通知 - {len(files)}个文件"
            return await self._send_email(to_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"发送上传成功通知失败: {e}")
            return False
    
    async def send_custom_notification(
        self, 
        to_email: str, 
        subject: str,
        content: str,
        is_html: bool = False
    ) -> bool:
        """发送自定义通知"""
        try:
            if is_html:
                return await self._send_email(to_email, subject, content)
            else:
                # 简单的文本转HTML
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{content}</pre>
                        <hr style="margin: 20px 0;">
                        <p style="font-size: 12px; color: #666;">
                            此邮件由系统发送，发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </body>
                </html>
                """
                return await self._send_email(to_email, subject, html_content, content)
            
        except Exception as e:
            logger.error(f"发送自定义通知失败: {e}")
            return False
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """获取通知统计信息"""
        try:
            # 这里可以从Redis或数据库获取统计信息
            # 简单实现，返回基本配置信息
            return {
                'smtp_configured': bool(settings.SMTP_HOST and settings.SMTP_USER),
                'smtp_host': settings.SMTP_HOST,
                'smtp_port': settings.SMTP_PORT,
                'smtp_tls': settings.SMTP_TLS,
                'from_email': settings.SMTP_USER,
                'templates_count': len(self.email_templates)
            }
            
        except Exception as e:
            logger.error(f"获取通知统计失败: {e}")
            return {}


# 创建全局通知服务实例
notification_service = NotificationService()