"""
邮件模板管理
处理各种邮件模板的生成和格式化
支持异步操作和Jinja2模板引擎
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from pathlib import Path
from functools import lru_cache
import aiofiles
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound, Template
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateError(Exception):
    """邮件模板相关异常"""
    pass


class EmailTemplateManager:
    """邮件模板管理器 - 支持异步操作和Jinja2模板引擎"""
    
    def __init__(self):
        # 模板文件目录
        self.template_dir = Path(__file__).parent / "email"
        
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 模板配置
        self.templates = {
            'tracker_confirmation': {
                'subject_template': '文件上传确认 - Tracker ID: {{ tracker_id }}',
                'html_template': 'tracker_confirmation.html',
                'text_template': 'tracker_confirmation.txt'
            },
            'upload_success': {
                'subject_template': '文件处理完成通知 - {{ filename }}',
                'html_template': 'upload_success.html',
                'text_template': 'upload_success.txt'
            },
            'upload_failed': {
                'subject_template': '文件处理失败通知 - {{ filename }}',
                'html_template': 'upload_failed.html',
                'text_template': 'upload_failed.txt'
            }
        }
        
        # 缓存已加载的模板
        self._template_cache: Dict[str, Template] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """异步初始化模板管理器"""
        if not self._initialized:
            await self._validate_template_files()
            self._initialized = True
    
    async def _validate_template_files(self) -> None:
        """异步验证模板文件是否存在"""
        missing_files = []
        
        for template_name, config in self.templates.items():
            html_path = self.template_dir / config['html_template']
            text_path = self.template_dir / config['text_template']
            
            if not html_path.exists():
                missing_files.append(str(html_path))
            if not text_path.exists():
                missing_files.append(str(text_path))
        
        if missing_files:
            error_msg = f"邮件模板文件缺失: {missing_files}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
        
        logger.info(f"邮件模板文件验证完成，模板目录: {self.template_dir}")
    
    async def _load_template_file(self, filename: str) -> str:
        """异步加载模板文件内容"""
        try:
            template_path = self.template_dir / filename
            async with aiofiles.open(template_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except FileNotFoundError:
            error_msg = f"模板文件不存在: {filename}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
        except Exception as e:
            error_msg = f"加载模板文件失败 {filename}: {e}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
    
    @lru_cache(maxsize=32)
    def _get_jinja_template(self, template_name: str) -> Template:
        """获取Jinja2模板对象（带缓存）"""
        try:
            return self.jinja_env.get_template(template_name)
        except TemplateNotFound:
            error_msg = f"Jinja2模板不存在: {template_name}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
        except Exception as e:
            error_msg = f"获取Jinja2模板失败 {template_name}: {e}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
    
    async def _render_template_async(self, template_name: str, variables: Dict[str, Any]) -> str:
        """异步渲染Jinja2模板"""
        try:
            template = self._get_jinja_template(template_name)
            return await template.render_async(**variables)
        except Exception as e:
            error_msg = f"异步模板渲染失败 {template_name}: {e}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
    
    def _render_subject_template(self, subject_template: str, variables: Dict[str, Any]) -> str:
        """渲染主题模板（同步）"""
        try:
            template = Template(subject_template)
            return template.render(**variables)
        except Exception as e:
            error_msg = f"主题模板渲染失败: {e}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
    
    async def get_tracker_confirmation_email(
        self, 
        tracker_id: str, 
        filename: str, 
        file_size: int,
        recipient_email: str
    ) -> Dict[str, str]:
        """
        异步生成Tracker ID确认邮件
        
        Args:
            tracker_id: 跟踪ID
            filename: 文件名
            file_size: 文件大小
            recipient_email: 收件人邮箱
            
        Returns:
            Dict[str, str]: 包含subject, html_body, text_body的字典
        """
        await self.initialize()
        
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
        
        try:
            # 并发渲染HTML和文本模板
            html_task = self._render_template_async(template_config['html_template'], template_data)
            text_task = self._render_template_async(template_config['text_template'], template_data)
            
            html_body, text_body = await asyncio.gather(html_task, text_task)
            
            return {
                'subject': self._render_subject_template(template_config['subject_template'], template_data),
                'html_body': html_body,
                'text_body': text_body
            }
        except Exception as e:
            error_msg = f"生成Tracker确认邮件失败: {e}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
    
    async def get_upload_status_email(
        self, 
        tracker_id: str, 
        status: str, 
        filename: str,
        recipient_email: str,
        error_message: Optional[str] = None
    ) -> Dict[str, str]:
        """
        异步生成上传状态更新邮件
        
        Args:
            tracker_id: 跟踪ID
            status: 处理状态
            filename: 文件名
            recipient_email: 收件人邮箱
            error_message: 错误信息（可选）
            
        Returns:
            Dict[str, str]: 包含subject, html_body, text_body的字典
        """
        await self.initialize()
        
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
        
        try:
            # 并发渲染HTML和文本模板
            html_task = self._render_template_async(template_config['html_template'], template_data)
            text_task = self._render_template_async(template_config['text_template'], template_data)
            
            html_body, text_body = await asyncio.gather(html_task, text_task)
            
            return {
                'subject': self._render_subject_template(template_config['subject_template'], template_data),
                'html_body': html_body,
                'text_body': text_body
            }
        except Exception as e:
            error_msg = f"生成状态更新邮件失败: {e}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_mapping = {
            'pending': '待处理',
            'processing': '处理中',
            'completed': '处理完成',
            'rejected': '处理失败',
            'failed': '处理失败',
            'error': '处理错误'
        }
        return status_mapping.get(status.lower(), status)
    
    async def reload_templates(self) -> None:
        """异步重新加载模板文件（用于开发和调试）"""
        try:
            # 清除缓存
            self._template_cache.clear()
            self._get_jinja_template.cache_clear()
            
            # 重新验证模板文件
            await self._validate_template_files()
            
            # 重新创建Jinja2环境
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml']),
                enable_async=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            logger.info("邮件模板重新加载成功")
        except Exception as e:
            error_msg = f"邮件模板重新加载失败: {e}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg)
    
    def get_available_templates(self) -> Dict[str, Dict[str, str]]:
        """获取可用的模板列表"""
        return {
            name: {
                'subject_template': config['subject_template'],
                'html_template': config['html_template'],
                'text_template': config['text_template']
            }
            for name, config in self.templates.items()
        }
    
    async def validate_template_syntax(self, template_name: str) -> Dict[str, Union[bool, str]]:
        """验证模板语法"""
        result = {'valid': True, 'errors': []}
        
        if template_name not in self.templates:
            return {'valid': False, 'errors': [f'模板不存在: {template_name}']}
        
        config = self.templates[template_name]
        
        try:
            # 验证HTML模板
            self._get_jinja_template(config['html_template'])
            
            # 验证文本模板
            self._get_jinja_template(config['text_template'])
            
            # 验证主题模板
            Template(config['subject_template'])
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(str(e))
        
        return result


# 创建全局邮件模板管理器实例
email_template_manager = EmailTemplateManager()