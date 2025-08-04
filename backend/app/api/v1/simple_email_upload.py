"""
简化的邮件上传API
提供公开的附件列表查询接口
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.simple_email_upload import SimpleEmailUpload

router = APIRouter()


class SimpleEmailUploadResponse(BaseModel):
    """简化的邮件上传响应模型"""
    id: str = Field(..., description="上传记录ID")
    sender_email: str = Field(..., description="发送者邮箱")
    original_filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    email_subject: str = Field(None, description="邮件主题")
    uploaded_at: datetime = Field(..., description="上传时间")

    class Config:
        from_attributes = True


class SimpleEmailUploadListResponse(BaseModel):
    """简化的邮件上传列表响应模型"""
    items: List[SimpleEmailUploadResponse] = Field(..., description="上传记录列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


@router.get("/api/uploads", response_model=SimpleEmailUploadListResponse)
async def get_public_uploads(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开的邮件上传文件列表
    显示上传时间、发送者邮箱和附件名
    无需认证，完全公开
    """
    try:
        # 查询总数
        count_stmt = select(func.count(SimpleEmailUpload.id))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 分页查询数据
        stmt = select(SimpleEmailUpload).order_by(
            SimpleEmailUpload.uploaded_at.desc()
        ).offset((page - 1) * size).limit(size)
        
        result = await db.execute(stmt)
        uploads = result.scalars().all()
        
        # 转换为响应格式
        items = []
        for upload in uploads:
            items.append(SimpleEmailUploadResponse(
                id=upload.id,
                sender_email=upload.sender_email,
                original_filename=upload.original_filename,
                file_size=upload.file_size,
                file_type=upload.file_type,
                email_subject=upload.email_subject,
                uploaded_at=upload.uploaded_at
            ))
        
        return SimpleEmailUploadListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/api/uploads/{upload_id}", response_model=SimpleEmailUploadResponse)
async def get_upload_detail(
    upload_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个上传文件的详细信息
    """
    try:
        stmt = select(SimpleEmailUpload).where(SimpleEmailUpload.id == upload_id)
        result = await db.execute(stmt)
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return SimpleEmailUploadResponse(
            id=upload.id,
            sender_email=upload.sender_email,
            original_filename=upload.original_filename,
            file_size=upload.file_size,
            file_type=upload.file_type,
            email_subject=upload.email_subject,
            uploaded_at=upload.uploaded_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/api/stats")
async def get_upload_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    获取上传统计信息
    """
    try:
        # 总文件数
        total_stmt = select(func.count(SimpleEmailUpload.id))
        total_result = await db.execute(total_stmt)
        total_files = total_result.scalar()
        
        # 总文件大小
        size_stmt = select(func.sum(SimpleEmailUpload.file_size))
        size_result = await db.execute(size_stmt)
        total_size = size_result.scalar() or 0
        
        # 最新上传时间
        latest_stmt = select(func.max(SimpleEmailUpload.uploaded_at))
        latest_result = await db.execute(latest_stmt)
        latest_upload = latest_result.scalar()
        
        # 按文件类型统计
        type_stmt = select(
            SimpleEmailUpload.file_type,
            func.count(SimpleEmailUpload.id).label('count')
        ).group_by(SimpleEmailUpload.file_type)
        type_result = await db.execute(type_stmt)
        file_types = {row.file_type: row.count for row in type_result}
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "latest_upload": latest_upload,
            "file_types": file_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(),
        "service": "简化邮件附件管理系统"
    }