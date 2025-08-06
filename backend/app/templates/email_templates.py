"""
邮件模板管理
处理各种邮件模板的生成和格式化
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateManager:
    """邮件模板管理器"""
    
    def __init__(self):
        # 模板文件目录
        self.template_dir = Path(__file__).parent / "email"
        
        # 模板配置
        self.templates = {
            'tracker_confirmation': {
                'subject': '文件上传确认 - Tracker ID: {tracker_id}',
                'html_file': 'tracker_confirmation.html',
                'text_file': 'tracker_confirmation.txt'
            },
            'upload_success': {
                'subject': '文件处理完成通知',
                'html_file': 'upload_success.html',
                'text_file': 'upload_success.txt'
            },
            'upload_failed': {
                'subject': '文件处理失败通知',
                'html_file': 'upload_failed.html',
                'text_file': 'upload_failed.txt'
            }
        }
        
        # 验证模板文件是否存在
        self._validate_template_files()
    
    def _validate_template_files(self):
        """验证模板文件是否存在"""
        missing_files = []
        
        for template_name, config in self.templates.items():
            html_path = self.template_dir / config['html_file']
            text_path = self.template_dir / config['text_file']
            
            if not html_path.exists():
                missing_files.append(str(html_path))
            if not text_path.exists():
                missing_files.append(str(text_path))
        
        if missing_files:
            logger.error(f"邮件模板文件缺失: {missing_files}")
            raise FileNotFoundError(f"邮件模板文件缺失: {missing_files}")
        
        logger.info(f"邮件模板文件验证完成，模板目录: {self.template_dir}")
    
    def _load_template_file(self, filename: str) -> str:
        """加载模板文件内容"""
        try:
            template_path = self.template_dir / filename
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"加载模板文件失败 {filename}: {e}")
            raise
    
    def _render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """渲染模板内容"""
        try:
            # 使用简单的字符串替换进行模板渲染
            rendered_content = template_content
            
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                rendered_content = rendered_content.replace(placeholder, str(value))
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            raise
    
    def get_tracker_confirmation_email(
        self, 
        tracker_id: str, 
        filename: str, 
        file_size: int,
        recipient_email: str
    ) -> Dict[str, str]:
        """
        生成Tracker ID确认邮件
        
        Args:
            tracker_id: 跟踪ID
            filename: 文件名
            file_size: 文件大小
            recipient_email: 收件人邮箱
            
        Returns:
            Dict[str, str]: 包含subject, html_body, text_body的字典
        """
        template_data = {
            'tracker_id': tracker_id,
            'filename': filename,
            'file_size': self._format_file_size(file_size),
            'recipient_email': recipient_email,
            'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'query_url': f"{settings.FRONTEND_URL}/tracker/{tracker_id}",
            'support_email': settings.SUPPORT_EMAIL,
            'system_name': settings.SYSTEM_NAME or "知识库上传系统"
        }
        
        template_config = self.templates['tracker_confirmation']
        
        # 加载并渲染模板
        html_template = self._load_template_file(template_config['html_file'])
        text_template = self._load_template_file(template_config['text_file'])
        
        return {
            'subject': template_config['subject'].format(**template_data),
            'html_body': self._render_template(html_template, template_data),
            'text_body': self._render_template(text_template, template_data)
        }
    
    def get_upload_status_email(
        self, 
        tracker_id: str, 
        status: str, 
        filename: str,
        recipient_email: str,
        error_message: Optional[str] = None
    ) -> Dict[str, str]:
        """
        生成上传状态更新邮件
        
        Args:
            tracker_id: 跟踪ID
            status: 处理状态
            filename: 文件名
            recipient_email: 收件人邮箱
            error_message: 错误信息（可选）
            
        Returns:
            Dict[str, str]: 包含subject, html_body, text_body的字典
        """
        template_key = 'upload_success' if status == 'completed' else 'upload_failed'
        template_config = self.templates[template_key]
        
        status_text = self._get_status_text(status)
        
        template_data = {
            'tracker_id': tracker_id,
            'filename': filename,
            'status': status_text,
            'recipient_email': recipient_email,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'query_url': f"{settings.FRONTEND_URL}/tracker/{tracker_id}",
            'support_email': settings.SUPPORT_EMAIL,
            'system_name': settings.SYSTEM_NAME or "知识库上传系统",
            'error_message': error_message or ""
        }
        
        # 加载并渲染模板
        html_template = self._load_template_file(template_config['html_file'])
        text_template = self._load_template_file(template_config['text_file'])
        
        return {
            'subject': template_config['subject'].format(**template_data),
            'html_body': self._render_template(html_template, template_data),
            'text_body': self._render_template(text_template, template_data)
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_mapping = {
            'pending': '待处理',
            'processing': '处理中',
            'completed': '处理完成',
            'rejected': '处理失败',
            'failed': '处理失败'
        }
        return status_mapping.get(status, status)
    
    def reload_templates(self):
        """重新加载模板文件（用于开发和调试）"""
        try:
            self._validate_template_files()
            logger.info("邮件模板重新加载成功")
        except Exception as e:
            logger.error(f"邮件模板重新加载失败: {e}")
            raise
    
    def get_available_templates(self) -> Dict[str, Dict[str, str]]:
        """获取可用的模板列表"""
        return {
            name: {
                'subject': config['subject'],
                'html_file': config['html_file'],
                'text_file': config['text_file']
            }
            for name, config in self.templates.items()
        }


# 创建全局邮件模板管理器实例
email_template_manager = EmailTemplateManager()
