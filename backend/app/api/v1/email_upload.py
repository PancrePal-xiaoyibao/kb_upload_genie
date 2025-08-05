"""
邮件上传API
提供邮件上传文件的查询和管理接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.api.deps import get_db, require_admin_user
from app.models.email_upload import EmailUpload, EmailUploadStatus
from app.models.user import User
from app.schemas.email_upload import (
    EmailUploadResponse,
    EmailUploadListResponse,
    EmailUploadPublicResponse,
    EmailUploadPublicListResponse,
    EmailUploadStatsResponse
)
from app.utils.email_utils import mask_email

router = APIRouter()


@router.get("/uploads", response_model=EmailUploadListResponse)
async def get_email_uploads(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[EmailUploadStatus] = Query(None, description="状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    获取邮件上传文件列表
    需要管理员权限
    """
    
    # 构建查询条件
    conditions = []
    if status:
        conditions.append(EmailUpload.status == status)
    if start_date:
        conditions.append(EmailUpload.received_at >= start_date)
    if end_date:
        conditions.append(EmailUpload.received_at <= end_date)
    
    # 查询总数
    count_stmt = select(func.count(EmailUpload.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()
    
    # 查询数据
    stmt = select(EmailUpload).order_by(EmailUpload.received_at.desc())
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    uploads = result.scalars().all()
    
    # 转换为响应格式
    items = []
    for upload in uploads:
        items.append(EmailUploadResponse(
            id=upload.id,
            original_filename=upload.original_filename,
            file_size=upload.file_size,
            file_type=upload.file_type,
            email_subject=upload.email_subject,
            sender_email=upload.sender_email,  # 管理员可以看到真实邮箱
            status=upload.status,
            received_at=upload.received_at,
            processed_at=upload.processed_at,
            review_comment=upload.review_comment
        ))
    
    return EmailUploadListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/uploads/{upload_id}", response_model=EmailUploadResponse)
async def get_email_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    获取单个邮件上传文件详情
    需要管理员权限
    """
    stmt = select(EmailUpload).where(EmailUpload.id == upload_id)
    result = await db.execute(stmt)
    upload = result.scalar_one_or_none()
    
    if not upload:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return EmailUploadResponse(
        id=upload.id,
        original_filename=upload.original_filename,
        file_size=upload.file_size,
        file_type=upload.file_type,
        email_subject=upload.email_subject,
        email_body=upload.email_body,
        sender_email=upload.sender_email,  # 管理员可以看到真实邮箱
        status=upload.status,
        received_at=upload.received_at,
        processed_at=upload.processed_at,
        reviewer_id=upload.reviewer_id,
        review_comment=upload.review_comment,
        extra_metadata=upload.extra_metadata
    )


@router.put("/uploads/{upload_id}/status")
async def update_upload_status(
    upload_id: str,
    status: EmailUploadStatus,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    更新邮件上传文件状态
    需要管理员权限
    """
    stmt = select(EmailUpload).where(EmailUpload.id == upload_id)
    result = await db.execute(stmt)
    upload = result.scalar_one_or_none()
    
    if not upload:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 更新状态
    upload.status = status
    upload.processed_at = datetime.utcnow()
    upload.reviewer_id = current_user.id
    if comment:
        upload.review_comment = comment
    
    await db.commit()
    
    return {"message": "状态更新成功"}


@router.get("/stats", response_model=EmailUploadStatsResponse)
async def get_email_upload_stats(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    获取邮件上传统计信息
    需要管理员权限
    """
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
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
    
    return EmailUploadStatsResponse(
        total_uploads=total_uploads,
        status_stats=status_stats,
        total_size=total_size,
        daily_stats=daily_stats,
        period_days=days
    )


@router.get("/public/uploads", response_model=EmailUploadPublicListResponse)
async def get_public_email_uploads(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开的邮件上传文件列表（不显示敏感信息）
    无需认证，用于展示上传的文件
    显示所有状态的文件，但对用户邮箱进行脱敏处理
    """
    # 显示所有状态的文件
    stmt = select(EmailUpload).order_by(EmailUpload.received_at.desc())
    
    # 查询总数
    count_stmt = select(func.count(EmailUpload.id))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()
    
    # 分页查询
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    uploads = result.scalars().all()
    
    # 转换为公开响应格式（隐藏敏感信息）
    items = []
    for upload in uploads:
        # 对邮箱进行脱敏处理
        masked_email = mask_email(upload.sender_email) if upload.sender_email else "匿名用户"
        
        items.append(EmailUploadPublicResponse(
            id=upload.id,
            original_filename=upload.original_filename,
            file_size=upload.file_size,
            file_type=upload.file_type,
            email_subject=upload.email_subject,
            sender_email_masked=masked_email,
            status=upload.status,
            received_at=upload.received_at,
            processed_at=upload.processed_at,
            review_comment=upload.review_comment if upload.status == EmailUploadStatus.REJECTED else None,  # 只有被拒绝时才显示原因
        ))
    
    return EmailUploadPublicListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )