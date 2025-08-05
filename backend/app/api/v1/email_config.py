"""
邮件配置管理API
提供邮件服务配置的管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging

from app.api.deps import get_db, require_admin_user
from app.models.user import User
from app.models.email_upload import EmailConfig, EmailDomainRule, AttachmentRule
from app.core.config import settings
from app.services.email_service import email_service
from app.services.redis_service import redis_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/config")
async def get_email_config(
    current_user: User = Depends(require_admin_user)
):
    """
    获取当前邮件配置
    需要管理员权限
    """
    try:
        config = {
            # 基本配置
            "email_upload_enabled": settings.EMAIL_UPLOAD_ENABLED,
            "email_check_interval": settings.EMAIL_CHECK_INTERVAL,
            "email_mark_as_read": settings.EMAIL_MARK_AS_READ,
            
            # SMTP配置
            "smtp_host": settings.SMTP_HOST,
            "smtp_port": settings.SMTP_PORT,
            "smtp_user": settings.SMTP_USER,
            "smtp_tls": settings.SMTP_TLS,
            "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD),
            
            # IMAP配置
            "imap_host": settings.IMAP_HOST,
            "imap_port": settings.IMAP_PORT,
            "imap_user": settings.IMAP_USER,
            "imap_use_ssl": settings.IMAP_USE_SSL,
            "imap_mailbox": settings.IMAP_MAILBOX,
            "imap_configured": bool(settings.IMAP_HOST and settings.IMAP_USER and settings.IMAP_PASSWORD),
            
            # 附件限制配置
            "max_attachment_size": settings.EMAIL_MAX_ATTACHMENT_SIZE,
            "max_attachment_size_mb": round(settings.EMAIL_MAX_ATTACHMENT_SIZE / (1024 * 1024), 2),
            "max_attachment_count": settings.EMAIL_MAX_ATTACHMENT_COUNT,
            "allowed_extensions": settings.EMAIL_ALLOWED_EXTENSIONS,
            
            # 频率限制配置
            "hourly_limit": settings.EMAIL_HOURLY_LIMIT,
            "daily_limit": settings.EMAIL_DAILY_LIMIT,
            
            # 域名限制配置
            "domain_whitelist_enabled": settings.EMAIL_DOMAIN_WHITELIST_ENABLED,
            "allowed_domains": settings.EMAIL_ALLOWED_DOMAINS,
            
            # Redis配置
            "redis_url": settings.REDIS_URL,
            "redis_host": settings.REDIS_HOST,
            "redis_port": settings.REDIS_PORT,
            "redis_db": settings.REDIS_DB,
            "redis_enabled": settings.REDIS_ENABLED,
            "redis_connected": await redis_service.is_connected()
        }
        
        return {
            "success": True,
            "data": config
        }
        
    except Exception as e:
        logger.error(f"获取邮件配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/test-connection")
async def test_email_connection(
    current_user: User = Depends(require_admin_user)
):
    """
    测试邮件服务连接
    需要管理员权限
    """
    try:
        results = {
            "smtp_connection": False,
            "imap_connection": False,
            "redis_connection": False,
            "overall_status": False,
            "errors": []
        }
        
        # 测试SMTP连接
        try:
            smtp_success = await email_service.connect_smtp()
            if smtp_success:
                await email_service.disconnect_smtp()
                results["smtp_connection"] = True
            else:
                results["errors"].append("SMTP连接失败")
        except Exception as e:
            results["errors"].append(f"SMTP连接错误: {str(e)}")
        
        # 测试IMAP连接
        try:
            imap_success = await email_service.connect_imap()
            if imap_success:
                await email_service.disconnect_imap()
                results["imap_connection"] = True
            else:
                results["errors"].append("IMAP连接失败")
        except Exception as e:
            results["errors"].append(f"IMAP连接错误: {str(e)}")
        
        # 测试Redis连接
        try:
            redis_success = await redis_service.is_connected()
            results["redis_connection"] = redis_success
            if not redis_success:
                results["errors"].append("Redis连接失败")
        except Exception as e:
            results["errors"].append(f"Redis连接错误: {str(e)}")
        
        # 计算总体状态
        results["overall_status"] = (
            results["smtp_connection"] and 
            results["imap_connection"] and 
            results["redis_connection"]
        )
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        logger.error(f"测试邮件连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"连接测试失败: {str(e)}")


@router.get("/attachment-rules")
async def get_attachment_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    获取附件规则配置
    需要管理员权限
    """
    try:
        stmt = select(AttachmentRule).where(AttachmentRule.is_active == True)
        result = await db.execute(stmt)
        rules = result.scalars().all()
        
        rules_data = []
        for rule in rules:
            allowed_extensions = []
            blocked_extensions = []
            
            if rule.allowed_extensions:
                try:
                    allowed_extensions = json.loads(rule.allowed_extensions)
                except json.JSONDecodeError:
                    pass
            
            if rule.blocked_extensions:
                try:
                    blocked_extensions = json.loads(rule.blocked_extensions)
                except json.JSONDecodeError:
                    pass
            
            rules_data.append({
                "id": rule.id,
                "rule_name": rule.rule_name,
                "max_file_size": rule.max_file_size,
                "max_file_size_mb": round(rule.max_file_size / (1024 * 1024), 2),
                "max_file_count": rule.max_file_count,
                "allowed_extensions": allowed_extensions,
                "blocked_extensions": blocked_extensions,
                "is_active": rule.is_active,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": rules_data
        }
        
    except Exception as e:
        logger.error(f"获取附件规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取附件规则失败: {str(e)}")


@router.post("/attachment-rules")
async def create_attachment_rule(
    rule_name: str = Form(..., description="规则名称"),
    max_file_size: int = Form(..., description="最大文件大小（字节）"),
    max_file_count: int = Form(..., description="最大文件数量"),
    allowed_extensions: Optional[str] = Form(None, description="允许的扩展名（JSON数组）"),
    blocked_extensions: Optional[str] = Form(None, description="禁止的扩展名（JSON数组）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    创建附件规则
    需要管理员权限
    """
    try:
        # 验证JSON格式
        if allowed_extensions:
            try:
                json.loads(allowed_extensions)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="允许的扩展名格式错误，应为JSON数组")
        
        if blocked_extensions:
            try:
                json.loads(blocked_extensions)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="禁止的扩展名格式错误，应为JSON数组")
        
        # 检查规则名称是否已存在
        stmt = select(AttachmentRule).where(AttachmentRule.rule_name == rule_name)
        result = await db.execute(stmt)
        existing_rule = result.scalar_one_or_none()
        
        if existing_rule:
            raise HTTPException(status_code=400, detail=f"规则名称 {rule_name} 已存在")
        
        # 创建新规则
        new_rule = AttachmentRule(
            rule_name=rule_name,
            max_file_size=max_file_size,
            max_file_count=max_file_count,
            allowed_extensions=allowed_extensions,
            blocked_extensions=blocked_extensions,
            is_active=True
        )
        
        db.add(new_rule)
        await db.commit()
        
        return {
            "success": True,
            "message": f"附件规则 {rule_name} 创建成功",
            "rule_id": new_rule.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建附件规则失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建附件规则失败: {str(e)}")


@router.put("/attachment-rules/{rule_id}")
async def update_attachment_rule(
    rule_id: str,
    rule_name: Optional[str] = Form(None, description="规则名称"),
    max_file_size: Optional[int] = Form(None, description="最大文件大小（字节）"),
    max_file_count: Optional[int] = Form(None, description="最大文件数量"),
    allowed_extensions: Optional[str] = Form(None, description="允许的扩展名（JSON数组）"),
    blocked_extensions: Optional[str] = Form(None, description="禁止的扩展名（JSON数组）"),
    is_active: Optional[bool] = Form(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    更新附件规则
    需要管理员权限
    """
    try:
        # 查找规则
        stmt = select(AttachmentRule).where(AttachmentRule.id == rule_id)
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="附件规则不存在")
        
        # 验证JSON格式
        if allowed_extensions:
            try:
                json.loads(allowed_extensions)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="允许的扩展名格式错误，应为JSON数组")
        
        if blocked_extensions:
            try:
                json.loads(blocked_extensions)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="禁止的扩展名格式错误，应为JSON数组")
        
        # 更新字段
        if rule_name is not None:
            rule.rule_name = rule_name
        if max_file_size is not None:
            rule.max_file_size = max_file_size
        if max_file_count is not None:
            rule.max_file_count = max_file_count
        if allowed_extensions is not None:
            rule.allowed_extensions = allowed_extensions
        if blocked_extensions is not None:
            rule.blocked_extensions = blocked_extensions
        if is_active is not None:
            rule.is_active = is_active
        
        rule.updated_at = datetime.now()
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"附件规则 {rule.rule_name} 更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新附件规则失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新附件规则失败: {str(e)}")


@router.delete("/attachment-rules/{rule_id}")
async def delete_attachment_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    删除附件规则
    需要管理员权限
    """
    try:
        stmt = select(AttachmentRule).where(AttachmentRule.id == rule_id)
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="附件规则不存在")
        
        await db.delete(rule)
        await db.commit()
        
        return {
            "success": True,
            "message": f"附件规则 {rule.rule_name} 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除附件规则失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除附件规则失败: {str(e)}")


@router.get("/system-status")
async def get_system_status(
    current_user: User = Depends(require_admin_user)
):
    """
    获取邮件系统状态
    需要管理员权限
    """
    try:
        # 检查各个组件状态
        redis_connected = await redis_service.is_connected()
        
        # 检查邮件服务配置
        smtp_configured = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
        imap_configured = bool(settings.IMAP_HOST and settings.IMAP_USER and settings.IMAP_PASSWORD)
        
        # 获取通知服务统计
        notification_stats = await notification_service.get_notification_stats()
        
        status = {
            "system_health": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "redis": {
                    "status": "connected" if redis_connected else "disconnected",
                    "enabled": settings.REDIS_ENABLED
                },
                "smtp": {
                    "status": "configured" if smtp_configured else "not_configured",
                    "host": settings.SMTP_HOST,
                    "port": settings.SMTP_PORT,
                    "tls": settings.SMTP_TLS
                },
                "imap": {
                    "status": "configured" if imap_configured else "not_configured",
                    "host": settings.IMAP_HOST,
                    "port": settings.IMAP_PORT,
                    "ssl": settings.IMAP_USE_SSL
                },
                "email_upload": {
                    "enabled": settings.EMAIL_UPLOAD_ENABLED,
                    "check_interval": settings.EMAIL_CHECK_INTERVAL
                },
                "notification": notification_stats
            },
            "limits": {
                "max_attachment_size_mb": round(settings.EMAIL_MAX_ATTACHMENT_SIZE / (1024 * 1024), 2),
                "max_attachment_count": settings.EMAIL_MAX_ATTACHMENT_COUNT,
                "hourly_limit": settings.EMAIL_HOURLY_LIMIT,
                "daily_limit": settings.EMAIL_DAILY_LIMIT
            }
        }
        
        # 判断整体健康状态
        if not (redis_connected and smtp_configured and imap_configured):
            status["system_health"] = "degraded"
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {
            "success": False,
            "data": {
                "system_health": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        }


@router.post("/system/restart-services")
async def restart_email_services(
    current_user: User = Depends(require_admin_user)
):
    """
    重启邮件服务
    需要管理员权限
    """
    try:
        # 断开现有连接
        await email_service.disconnect_smtp()
        await email_service.disconnect_imap()
        
        # 重新连接
        smtp_success = await email_service.connect_smtp()
        imap_success = await email_service.connect_imap()
        
        if smtp_success:
            await email_service.disconnect_smtp()
        if imap_success:
            await email_service.disconnect_imap()
        
        return {
            "success": True,
            "message": "邮件服务重启完成",
            "data": {
                "smtp_reconnected": smtp_success,
                "imap_reconnected": imap_success
            }
        }
        
    except Exception as e:
        logger.error(f"重启邮件服务失败: {e}")
        raise HTTPException(status_code=500, detail=f"重启服务失败: {str(e)}")


@router.post("/system/clear-cache")
async def clear_system_cache(
    current_user: User = Depends(require_admin_user)
):
    """
    清理系统缓存
    需要管理员权限
    """
    try:
        # 清理域名缓存
        from app.services.domain_service import domain_service
        await domain_service.clear_all_domain_cache()
        
        return {
            "success": True,
            "message": "系统缓存清理完成"
        }
        
    except Exception as e:
        logger.error(f"清理系统缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.get("/logs/recent")
async def get_recent_logs(
    lines: int = 100,
    level: str = "INFO",
    current_user: User = Depends(require_admin_user)
):
    """
    获取最近的系统日志
    需要管理员权限
    """
    try:
        # 这里可以实现日志读取逻辑
        # 简单实现，返回模拟数据
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "邮件系统运行正常",
                "module": "email_service"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "logs": logs,
                "total": len(logs),
                "level": level,
                "lines": lines
            }
        }
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")