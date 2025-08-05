"""
增强版邮件上传API
提供完整的邮件附件上传管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json

from app.core.database import get_db
from app.api.deps import get_admin_user, get_current_user, get_optional_current_user
from app.models.email_upload import (
    EmailUpload, 
    EmailUploadStatus, 
    EmailRateLimit, 
    EmailDomainRule,
    EmailConfig,
    AttachmentRule
)
from app.schemas.email_upload import (
    EmailUploadResponse,
    EmailUploadListResponse,
    EmailUploadStatsResponse,
    EmailUploadCreateRequest,
    EmailUploadUpdateRequest,
    DomainRuleResponse,
    RateLimitStatsResponse
)
from app.services.email_service import email_service
from app.services.attachment_service import attachment_service
from app.services.domain_service import domain_service
from app.services.notification_service import notification_service
from app.services.redis_service import redis_service
from app.core.config import settings

router = APIRouter()


@router.get("/uploads", response_model=EmailUploadListResponse)
async def get_email_uploads(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[EmailUploadStatus] = Query(None, description="状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取邮件上传文件列表（公开接口，不显示敏感信息）
    支持分页、筛选和搜索
    """
    try:
        # 构建查询条件
        conditions = []
        if status:
            conditions.append(EmailUpload.status == status)
        if start_date:
            conditions.append(EmailUpload.received_at >= start_date)
        if end_date:
            conditions.append(EmailUpload.received_at <= end_date)
        if search:
            conditions.append(
                or_(
                    EmailUpload.original_filename.ilike(f"%{search}%"),
                    EmailUpload.email_subject.ilike(f"%{search}%"),
                    EmailUpload.file_type.ilike(f"%{search}%")
                )
            )
        
        # 查询总数
        count_stmt = select(func.count(EmailUpload.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 查询数据
        stmt = select(EmailUpload).order_by(desc(EmailUpload.received_at))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await db.execute(stmt)
        uploads = result.scalars().all()
        
        # 转换为响应格式（公开版本，隐藏敏感信息）
        items = []
        for upload in uploads:
            # 从哈希中提取域名（如果可能）或显示通用信息
            sender_info = "匿名用户"
            if upload.email_subject:
                # 可以显示邮件主题的前几个字符
                subject_preview = upload.email_subject[:50] + "..." if len(upload.email_subject) > 50 else upload.email_subject
            else:
                subject_preview = "无主题"
            
            items.append(EmailUploadResponse(
                id=upload.id,
                original_filename=upload.original_filename,
                file_size=upload.file_size,
                file_type=upload.file_type,
                email_subject=subject_preview,
                email_body=None,  # 不显示邮件正文
                status=upload.status,
                received_at=upload.received_at,
                processed_at=upload.processed_at,
                reviewer_id=None,  # 不显示审核员ID
                review_comment=upload.review_comment if upload.status == EmailUploadStatus.REJECTED else None,
                extra_metadata=None  # 不显示额外元数据
            ))
        
        return EmailUploadListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size if total > 0 else 0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上传列表失败: {str(e)}")


@router.get("/stats/public")
async def get_public_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开的基础统计信息（不需要管理员权限）
    """
    try:
        # 只返回基础的统计信息，不涉及敏感数据
        
        # 总上传数
        total_stmt = select(func.count(EmailUpload.id))
        total_result = await db.execute(total_stmt)
        total_uploads = total_result.scalar()
        
        # 成功处理的文件数
        approved_stmt = select(func.count(EmailUpload.id)).where(
            EmailUpload.status == EmailUploadStatus.APPROVED
        )
        approved_result = await db.execute(approved_stmt)
        approved_count = approved_result.scalar()
        
        # 文件类型分布（只显示前5种）
        type_stmt = select(
            EmailUpload.file_type,
            func.count(EmailUpload.id).label('count')
        ).group_by(EmailUpload.file_type).order_by(func.count(EmailUpload.id).desc()).limit(5)
        
        type_result = await db.execute(type_stmt)
        file_types = [{"type": row.file_type, "count": row.count} for row in type_result]
        
        return {
            "total_uploads": total_uploads,
            "approved_uploads": approved_count,
            "success_rate": round((approved_count / total_uploads * 100), 2) if total_uploads > 0 else 0,
            "popular_file_types": file_types,
            "system_status": "运行中" if settings.EMAIL_UPLOAD_ENABLED else "暂停服务"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/uploads/{upload_id}")
async def get_email_upload_detail(
    upload_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个邮件上传文件详情（公开版本，隐藏敏感信息）
    """
    try:
        stmt = select(EmailUpload).where(EmailUpload.id == upload_id)
        result = await db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "id": upload.id,
            "original_filename": upload.original_filename,
            "file_size": upload.file_size,
            "file_type": upload.file_type,
            "email_subject": upload.email_subject[:100] + "..." if upload.email_subject and len(upload.email_subject) > 100 else upload.email_subject,
            "status": upload.status.value,
            "received_at": upload.received_at.isoformat(),
            "processed_at": upload.processed_at.isoformat() if upload.processed_at else None,
            "review_comment": upload.review_comment if upload.status == EmailUploadStatus .REJECTED else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件详情失败: {str(e)}")


@router.get("/uploads/{upload_id}/download")
async def download_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    下载邮件上传的文件
    """
    try:
        stmt = select(EmailUpload).where(EmailUpload.id == upload_id)
        result = await db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件路径
        file_path = await attachment_service.get_attachment_path(upload.stored_filename)
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在于服务器")
        
        return FileResponse(
            path=str(file_path),
            filename=upload.original_filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")


@router.get("/config")
async def get_email_config():
    """
    获取邮件上传配置信息
    """
    try:
        return {
            "email_upload_enabled": settings.EMAIL_UPLOAD_ENABLED,
            "max_attachment_size": settings.EMAIL_MAX_ATTACHMENT_SIZE,
            "max_attachment_size_mb": settings.EMAIL_MAX_ATTACHMENT_SIZE / (1024 * 1024),
            "max_attachment_count": settings.EMAIL_MAX_ATTACHMENT_COUNT,
            "allowed_extensions": settings.EMAIL_ALLOWED_EXTENSIONS,
            "hourly_limit": settings.EMAIL_HOURLY_LIMIT,
            "daily_limit": settings.EMAIL_DAILY_LIMIT,
            "domain_whitelist_enabled": settings.EMAIL_DOMAIN_WHITELIST_ENABLED,
            "allowed_domains": settings.EMAIL_ALLOWED_DOMAINS,
            "check_interval": settings.EMAIL_CHECK_INTERVAL
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置信息失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    try:
        # 检查各个服务状态
        redis_status = await redis_service.is_connected()
        
        # 检查邮件服务配置
        email_configured = bool(
            settings.SMTP_HOST and 
            settings.SMTP_USER and 
            settings.IMAP_HOST and 
            settings.IMAP_USER
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": "connected" if redis_status else "disconnected",
                "email": "configured" if email_configured else "not_configured",
                "upload_enabled": settings.EMAIL_UPLOAD_ENABLED
            },
            "config": {
                "max_file_size_mb": settings.EMAIL_MAX_ATTACHMENT_SIZE / (1024 * 1024),
                "max_file_count": settings.EMAIL_MAX_ATTACHMENT_COUNT,
                "hourly_limit": settings.EMAIL_HOURLY_LIMIT,
                "daily_limit": settings.EMAIL_DAILY_LIMIT
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# 以下是需要管理员权限的接口

@router.get("/admin/uploads", response_model=EmailUploadListResponse)
async def get_email_uploads_admin(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[EmailUploadStatus] = Query(None, description="状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    获取邮件上传文件列表（管理员版本，显示完整信息）
    支持分页、筛选和搜索
    """
    try:
        # 构建查询条件
        conditions = []
        if status:
            conditions.append(EmailUpload.status == status)
        if start_date:
            conditions.append(EmailUpload.received_at >= start_date)
        if end_date:
            conditions.append(EmailUpload.received_at <= end_date)
        if search:
            conditions.append(
                or_(
                    EmailUpload.original_filename.ilike(f"%{search}%"),
                    EmailUpload.email_subject.ilike(f"%{search}%"),
                    EmailUpload.file_type.ilike(f"%{search}%"),
                    EmailUpload.sender_email_hash.ilike(f"%{search}%")
                )
            )
        
        # 查询总数
        count_stmt = select(func.count(EmailUpload.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 查询数据
        stmt = select(EmailUpload).order_by(desc(EmailUpload.received_at))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await db.execute(stmt)
        uploads = result.scalars().all()
        
        # 转换为响应格式（管理员版本，显示完整信息）
        items = []
        for upload in uploads:
            items.append(EmailUploadResponse(
                id=upload.id,
                original_filename=upload.original_filename,
                file_size=upload.file_size,
                file_type=upload.file_type,
                email_subject=upload.email_subject,
                email_body=upload.email_body,
                status=upload.status,
                received_at=upload.received_at,
                processed_at=upload.processed_at,
                reviewer_id=upload.reviewer_id,
                review_comment=upload.review_comment,
                extra_metadata=json.loads(upload.extra_metadata) if upload.extra_metadata else None
            ))
        
        return EmailUploadListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size if total > 0 else 0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上传列表失败: {str(e)}")


@router.get("/admin/uploads/{upload_id}")
async def get_email_upload_detail_admin(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    获取单个邮件上传文件详情（管理员版本，显示完整信息）
    """
    try:
        stmt = select(EmailUpload).where(EmailUpload.id == upload_id)
        result = await db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "id": upload.id,
            "original_filename": upload.original_filename,
            "stored_filename": upload.stored_filename,
            "sender_email_hash": upload.sender_email_hash,
            "file_size": upload.file_size,
            "file_type": upload.file_type,
            "email_subject": upload.email_subject,
            "email_body": upload.email_body,
            "status": upload.status.value,
            "received_at": upload.received_at.isoformat(),
            "processed_at": upload.processed_at.isoformat() if upload.processed_at else None,
            "reviewer_id": upload.reviewer_id,
            "review_comment": upload.review_comment,
            "extra_metadata": json.loads(upload.extra_metadata) if upload.extra_metadata else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件详情失败: {str(e)}")


@router.put("/admin/uploads/{upload_id}/status")
async def update_upload_status(
    upload_id: str,
    status: EmailUploadStatus,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    更新邮件上传文件状态（需要管理员权限）
    """
    try:
        stmt = select(EmailUpload).where(EmailUpload.id == upload_id)
        result = await db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 更新状态
        old_status = upload.status
        upload.status = status
        upload.processed_at = datetime.now()
        upload.reviewer_id = current_user["user_id"]  # 记录审核员ID
        if comment:
            upload.review_comment = comment
        
        await db.commit()
        
        return {
            "message": "状态更新成功",
            "old_status": old_status.value,
            "new_status": status.value,
            "updated_at": upload.processed_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")


@router.delete("/admin/uploads/{upload_id}")
async def delete_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    删除邮件上传文件（需要管理员权限）
    """
    try:
        stmt = select(EmailUpload).where(EmailUpload.id == upload_id)
        result = await db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除物理文件
        if upload.stored_filename:
            await attachment_service.delete_attachment(upload.stored_filename)
        
        # 删除数据库记录
        await db.delete(upload)
        await db.commit()
        
        return {"message": "文件删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


@router.get("/admin/stats")
async def get_upload_stats_admin(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    获取邮件上传统计信息（需要管理员权限）
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # 总数统计
        total_stmt = select(func.count(EmailUpload.id)).where(
            EmailUpload.received_at >= start_date
        )
        total_result = await db.execute(total_stmt)
        total_uploads = total_result.scalar()
        
        # 按状态统计
        status_stats = {}
        for status in EmailUploadStatus:
            stmt = select(func.count(EmailUpload.id)).where(
                and_(
                    EmailUpload.received_at >= start_date,
                    EmailUpload.status == status
                )
            )
            result = await db.execute(stmt)
            status_stats[status.value] = result.scalar()
        
        # 文件大小统计
        size_stmt = select(func.sum(EmailUpload.file_size)).where(
            EmailUpload.received_at >= start_date
        )
        size_result = await db.execute(size_stmt)
        total_size = size_result.scalar() or 0
        
        # 文件类型统计
        type_stmt = select(
            EmailUpload.file_type,
            func.count(EmailUpload.id).label('count')
        ).where(
            EmailUpload.received_at >= start_date
        ).group_by(EmailUpload.file_type)
        
        type_result = await db.execute(type_stmt)
        file_type_stats = {row.file_type: row.count for row in type_result}
        
        # 按日期统计
        daily_stats = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            stmt = select(func.count(EmailUpload.id)).where(
                and_(
                    EmailUpload.received_at >= day_start,
                    EmailUpload.received_at < day_end
                )
            )
            result = await db.execute(stmt)
            count = result.scalar()
            
            daily_stats.append({
                "date": day_start.date().isoformat(),
                "count": count
            })
        
        return {
            "total_uploads": total_uploads,
            "status_stats": status_stats,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_type_stats": file_type_stats,
            "daily_stats": daily_stats,
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/admin/manual-check")
async def manual_email_check(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    手动触发邮件检查（需要管理员权限）
    """
    try:
        # 获取新邮件
        email_records = await email_service.fetch_new_emails(db)
        
        if email_records:
            # 保存邮件记录
            await email_service.save_email_records(email_records, db)
            
            return {
                "message": f"成功处理 {len(email_records)} 封邮件",
                "processed_count": len(email_records)
            }
        else:
            return {
                "message": "没有新邮件",
                "processed_count": 0
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"手动检查邮件失败: {str(e)}")


@router.post("/admin/test-email")
async def test_email_connection(
    current_user: dict = Depends(get_admin_user)
):
    """
    测试邮件服务连接（需要管理员权限）
    """
    try:
        # 测试SMTP连接
        smtp_success = await email_service.connect_smtp()
        if smtp_success:
            await email_service.disconnect_smtp()
        
        # 测试IMAP连接
        imap_success = await email_service.connect_imap()
        if imap_success:
            await email_service.disconnect_imap()
        
        return {
            "smtp_connection": smtp_success,
            "imap_connection": imap_success,
            "overall_status": smtp_success and imap_success
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试邮件连接失败: {str(e)}")
