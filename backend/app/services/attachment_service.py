"""
附件处理服务
处理邮件附件的下载、验证、存储和管理
"""

import os
import hashlib
import mimetypes
import magic
import aiofiles
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import logging

from app.core.config import settings
from app.models.email_upload import AttachmentRule

logger = logging.getLogger(__name__)


class AttachmentService:
    """附件处理服务类"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR) / "email_attachments"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, file_data: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.sha256(file_data).hexdigest()
    
    def _get_file_mime_type(self, file_data: bytes, filename: str) -> str:
        """获取文件MIME类型"""
        try:
            # 使用python-magic检测文件类型
            mime_type = magic.from_buffer(file_data, mime=True)
            return mime_type
        except Exception:
            # 如果magic失败，使用mimetypes作为备选
            mime_type, _ = mimetypes.guess_type(filename)
            return mime_type or "application/octet-stream"
    
    def _is_safe_filename(self, filename: str) -> bool:
        """检查文件名是否安全"""
        # 检查危险字符
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # 检查文件名长度
        if len(filename) > 255:
            return False
        
        # 检查是否为空或只包含空格
        if not filename.strip():
            return False
        
        return True
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        # 移除危险字符
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in '.-_()[]{}':
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        sanitized = ''.join(safe_chars)
        
        # 限制长度
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext
        
        return sanitized
    
    async def validate_attachment(
        self, 
        file_data: bytes, 
        filename: str,
        sender_email: str = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        验证附件
        返回: (是否有效, 错误信息, 文件信息)
        """
        try:
            # 基本文件名检查
            if not self._is_safe_filename(filename):
                return False, "文件名包含不安全字符", {}
            
            # 文件大小检查
            file_size = len(file_data)
            if file_size == 0:
                return False, "文件为空", {}
            
            if file_size > settings.EMAIL_MAX_ATTACHMENT_SIZE:
                max_size_mb = settings.EMAIL_MAX_ATTACHMENT_SIZE / 1024 / 1024
                return False, f"文件大小超过限制 ({max_size_mb:.1f}MB)", {}
            
            # 文件扩展名检查
            file_ext = os.path.splitext(filename)[1].lower()
            if not file_ext:
                return False, "文件没有扩展名", {}
            
            if file_ext not in settings.EMAIL_ALLOWED_EXTENSIONS:
                allowed_exts = ', '.join(settings.EMAIL_ALLOWED_EXTENSIONS)
                return False, f"不支持的文件类型。允许的类型: {allowed_exts}", {}
            
            # MIME类型检查
            mime_type = self._get_file_mime_type(file_data, filename)
            
            # 恶意文件检查
            if await self._is_malicious_file(file_data, filename, mime_type):
                return False, "检测到潜在恶意文件", {}
            
            # 文件信息
            file_info = {
                'size': file_size,
                'mime_type': mime_type,
                'extension': file_ext,
                'hash': self._get_file_hash(file_data),
                'sanitized_filename': self._sanitize_filename(filename)
            }
            
            return True, "", file_info
            
        except Exception as e:
            logger.error(f"验证附件失败: {e}")
            return False, "文件验证过程中出现错误", {}
    
    async def _is_malicious_file(self, file_data: bytes, filename: str, mime_type: str) -> bool:
        """检查是否为恶意文件"""
        try:
            # 检查可执行文件
            executable_mimes = [
                'application/x-executable',
                'application/x-msdos-program',
                'application/x-msdownload',
                'application/x-winexe',
                'application/x-dosexec'
            ]
            
            if mime_type in executable_mimes:
                return True
            
            # 检查脚本文件
            script_extensions = ['.bat', '.cmd', '.com', '.exe', '.scr', '.vbs', '.js']
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in script_extensions:
                return True
            
            # 检查文件头部特征
            if len(file_data) >= 2:
                # PE文件头
                if file_data[:2] == b'MZ':
                    return True
                
                # ELF文件头
                if file_data[:4] == b'\x7fELF':
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"恶意文件检查失败: {e}")
            return False
    
    async def save_attachment(
        self, 
        file_data: bytes, 
        filename: str, 
        sender_email_hash: str,
        file_info: Dict[str, Any]
    ) -> Tuple[bool, str, str]:
        """
        保存附件到本地
        返回: (是否成功, 错误信息, 存储文件名)
        """
        try:
            # 生成唯一的存储文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_ext = file_info['extension']
            stored_filename = f"{timestamp}_{sender_email_hash[:8]}_{file_info['sanitized_filename']}"
            
            # 确保文件名唯一
            file_path = self.upload_dir / stored_filename
            counter = 1
            while file_path.exists():
                name, ext = os.path.splitext(stored_filename)
                stored_filename = f"{name}_{counter}{ext}"
                file_path = self.upload_dir / stored_filename
                counter += 1
            
            # 创建目录结构（按日期分组）
            date_dir = self.upload_dir / datetime.now().strftime("%Y/%m/%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            final_path = date_dir / stored_filename
            
            # 异步保存文件
            async with aiofiles.open(final_path, 'wb') as f:
                await f.write(file_data)
            
            # 验证文件是否正确保存
            if not final_path.exists() or final_path.stat().st_size != len(file_data):
                return False, "文件保存验证失败", ""
            
            # 设置文件权限
            os.chmod(final_path, 0o644)
            
            # 返回相对路径
            relative_path = str(final_path.relative_to(self.upload_dir))
            
            logger.info(f"附件保存成功: {relative_path}")
            return True, "", relative_path
            
        except Exception as e:
            logger.error(f"保存附件失败: {e}")
            return False, f"保存文件时出现错误: {str(e)}", ""
    
    async def get_attachment_path(self, stored_filename: str) -> Optional[Path]:
        """获取附件的完整路径"""
        try:
            file_path = self.upload_dir / stored_filename
            if file_path.exists():
                return file_path
            return None
        except Exception as e:
            logger.error(f"获取附件路径失败: {e}")
            return None
    
    async def delete_attachment(self, stored_filename: str) -> bool:
        """删除附件文件"""
        try:
            file_path = await self.get_attachment_path(stored_filename)
            if file_path and file_path.exists():
                file_path.unlink()
                logger.info(f"附件删除成功: {stored_filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除附件失败: {e}")
            return False
    
    async def get_attachment_info(self, stored_filename: str) -> Optional[Dict[str, Any]]:
        """获取附件信息"""
        try:
            file_path = await self.get_attachment_path(stored_filename)
            if not file_path or not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            return {
                'filename': stored_filename,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'exists': True
            }
        except Exception as e:
            logger.error(f"获取附件信息失败: {e}")
            return None
    
    async def validate_attachment_batch(
        self, 
        attachments: List[Tuple[bytes, str]], 
        sender_email: str = None
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        批量验证附件
        返回: (是否全部有效, 错误信息, 有效附件信息列表)
        """
        try:
            # 检查附件数量
            if len(attachments) > settings.EMAIL_MAX_ATTACHMENT_COUNT:
                return False, f"附件数量超过限制 ({settings.EMAIL_MAX_ATTACHMENT_COUNT}个)", []
            
            valid_attachments = []
            total_size = 0
            
            for file_data, filename in attachments:
                # 验证单个附件
                is_valid, error_msg, file_info = await self.validate_attachment(
                    file_data, filename, sender_email
                )
                
                if not is_valid:
                    return False, f"文件 '{filename}': {error_msg}", []
                
                total_size += file_info['size']
                valid_attachments.append({
                    'data': file_data,
                    'filename': filename,
                    'info': file_info
                })
            
            # 检查总大小限制（可选）
            max_total_size = settings.EMAIL_MAX_ATTACHMENT_SIZE * settings.EMAIL_MAX_ATTACHMENT_COUNT
            if total_size > max_total_size:
                max_total_mb = max_total_size / 1024 / 1024
                return False, f"附件总大小超过限制 ({max_total_mb:.1f}MB)", []
            
            return True, "", valid_attachments
            
        except Exception as e:
            logger.error(f"批量验证附件失败: {e}")
            return False, "批量验证过程中出现错误", []
    
    async def save_attachment_batch(
        self, 
        valid_attachments: List[Dict[str, Any]], 
        sender_email_hash: str
    ) -> List[Dict[str, Any]]:
        """
        批量保存附件
        返回: 保存结果列表
        """
        results = []
        
        for attachment in valid_attachments:
            success, error_msg, stored_filename = await self.save_attachment(
                attachment['data'],
                attachment['filename'],
                sender_email_hash,
                attachment['info']
            )
            
            result = {
                'original_filename': attachment['filename'],
                'success': success,
                'error_message': error_msg,
                'stored_filename': stored_filename if success else None,
                'file_size': attachment['info']['size'],
                'file_type': attachment['info']['extension'],
                'mime_type': attachment['info']['mime_type'],
                'file_hash': attachment['info']['hash']
            }
            
            results.append(result)
        
        return results
    
    async def cleanup_old_attachments(self, days_old: int = 30) -> int:
        """清理旧附件文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            cleaned_count = 0
            
            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            logger.error(f"删除旧文件失败 {file_path}: {e}")
            
            logger.info(f"清理了 {cleaned_count} 个旧附件文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧附件失败: {e}")
            return 0


# 创建全局附件服务实例
attachment_service = AttachmentService()