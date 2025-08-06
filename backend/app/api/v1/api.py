"""
API v1 主路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import shutil
from pathlib import Path
import uuid
import logging
from datetime import datetime

from app.core.config import settings
from app.core.turnstile import verify_turnstile
from app.models.article import Article, UploadMethod, ProcessingStatus, FileType
from app.utils.tracker_utils import generate_tracker_id
from app.core.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

# 设置日志
logger = logging.getLogger(__name__)

# 导入子路由
from app.api.v1.email_upload import router as email_upload_router
from app.api.v1.email_upload_enhanced import router as email_upload_enhanced_router
from app.api.v1.email_config import router as email_config_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.tracker import router as tracker_router

# 创建API路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(
    email_upload_router,
    prefix="/email-upload",
    tags=["邮件上传"]
)

api_router.include_router(
    email_upload_enhanced_router,
    prefix="/email-upload-enhanced",
    tags=["邮件上传增强版"]
)

api_router.include_router(
    email_config_router,
    prefix="/email-config",
    tags=["邮件配置管理"]
)

api_router.include_router(
    auth_router,
    tags=["认证"]
)

api_router.include_router(
    admin_router,
    tags=["管理员"]
)

api_router.include_router(
    tracker_router,
    prefix="/tracker",
    tags=["上传跟踪"]
)

# 基本健康检查端点
@api_router.get("/health")
async def api_health():
    """API健康检查"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "message": "KB Upload Genie API v1 is running"
    }

# Turnstile配置端点
@api_router.get("/turnstile/config")
async def get_turnstile_config():
    """获取Turnstile配置"""
    return {
        "enabled": settings.TURNSTILE_ENABLED,
        "site_key": settings.TURNSTILE_SITE_KEY if settings.TURNSTILE_ENABLED else None
    }

# 用户相关路由
@api_router.get("/users")
async def get_users():
    """获取用户列表"""
    return {"message": "用户列表功能开发中"}

# 文章相关路由
@api_router.get("/articles")
async def get_articles():
    """获取文章列表"""
    return {"message": "文章列表功能开发中"}

# 分类相关路由
@api_router.get("/categories")
async def get_categories():
    """获取分类列表"""
    return {"message": "分类列表功能开发中"}

# 版权记录相关路由
@api_router.get("/copyright-records")
async def get_copyright_records():
    """获取版权记录列表"""
    return {"message": "版权记录列表功能开发中"}

# 审核相关路由
@api_router.get("/reviews")
async def get_reviews():
    """获取审核列表"""
    return {"message": "审核列表功能开发中"}


# 文件上传相关路由
@api_router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    turnstile_token: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    单文件上传接口 (包含Turnstile验证)
    """
    # print(f"[Upload] 接收到上传请求:")
    # print(f"  文件名: {file.filename}")
    # print(f"  文件大小: {file.size if hasattr(file, 'size') else '未知'}")
    # print(f"  Turnstile令牌: {turnstile_token[:20] + '...' if turnstile_token else 'None'}")
    # print(f"  Turnstile启用: {settings.TURNSTILE_ENABLED}")
    
    try:
        # Turnstile验证
        if settings.TURNSTILE_ENABLED:
            client_ip = request.client.host if request.client else None
            await verify_turnstile(turnstile_token, client_ip)
        
        # 检查文件大小
        # 注意：FastAPI的UploadFile没有直接的size属性，需要读取文件内容来确定大小
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)  # 重置文件指针位置
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
            )
        
        # 检查文件类型
        file_extension = Path(file.filename).suffix.lower()
        allowed_types = settings.ALLOWED_FILE_TYPES
        if isinstance(allowed_types, str):
            allowed_types = [ext.strip() for ext in allowed_types.split(',')]
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_extension}。支持的类型: {', '.join(allowed_types)}"
            )
        
        # 创建上传目录
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}_{file.filename}"
        file_path = upload_dir / file_name
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 生成tracker_id并保存到articles表
        tracker_id = generate_tracker_id("WEB")
        
        try:
            # 获取文件类型枚举
            def get_file_type_enum(extension: str):
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
                return ext_mapping.get(extension.lower(), FileType.OTHER)
            
            # 保存到articles表以支持跟踪
            # 保存到articles表以支持跟踪
            article = Article(
                title=f"网页上传: {file.filename}",
                description=f"通过网页上传的文件: {file.filename}",
                github_url=f"web_upload://{file_id}",  # 使用唯一的URL避免冲突
                github_owner="web_upload",
                github_repo="files",
                file_type=get_file_type_enum(file_extension),
                file_size=file_size,
                user_id="anonymous",  # 匿名用户
                method=UploadMethod.WEB_UPLOAD,
                tracker_id=tracker_id,
                processing_status=ProcessingStatus.COMPLETED,  # 网页上传直接标记为完成
                extra_metadata={
                    "file_id": file_id,
                    "original_filename": file.filename,
                    "saved_filename": file_name,
                    "file_path": str(file_path),
                    "upload_method": "web_form"
                }
            )
            
            db.add(article)
            db.add(article)
            db.add(article)
            await db.commit()
            
        except Exception as e:
            logger.error(f"保存文章记录失败: {e}")
            # 即使保存文章记录失败，文件上传仍然成功
        
        # 返回上传结果
        return {
            "success": True,
            "message": "文件上传成功",
            "data": {
                "file_id": file_id,
                "tracker_id": tracker_id,
                "original_name": file.filename,
                "saved_name": file_name,
                "file_size": file_size,
                "file_type": file_extension,
                "upload_time": datetime.now().isoformat(),
                "file_path": str(file_path)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@api_router.post("/upload/multiple")
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...),
    turnstile_token: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    多文件上传接口 (包含Turnstile验证)
    """
    try:
        # Turnstile验证
        if settings.TURNSTILE_ENABLED:
            client_ip = request.client.host if request.client else None
            await verify_turnstile(turnstile_token, client_ip)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"验证失败: {str(e)}")
    
    if len(files) > 10:  # 限制最多10个文件
        raise HTTPException(status_code=400, detail="一次最多上传10个文件")
    
    results = []
    errors = []
    
    for file in files:
        try:
            # 为每个文件创建单独的上传处理
            # 检查文件大小
            file_content = await file.read()
            file_size = len(file_content)
            await file.seek(0)  # 重置文件指针位置
            
            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
                )
            
            # 检查文件类型
            file_extension = Path(file.filename).suffix.lower()
            allowed_types = settings.ALLOWED_FILE_TYPES
            if isinstance(allowed_types, str):
                allowed_types = [ext.strip() for ext in allowed_types.split(',')]
            
            if file_extension not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {file_extension}"
                )
            
            # 创建上传目录
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            file_name = f"{file_id}_{file.filename}"
            file_path = upload_dir / file_name
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 生成tracker_id
            tracker_id = generate_tracker_id("WEB")
            
            # 保存到数据库
            def get_file_type_enum(extension: str):
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
                return ext_mapping.get(extension.lower(), FileType.OTHER)
            
            article = Article(
                title=f"网页上传: {file.filename}",
                description=f"通过网页上传的文件: {file.filename}",
                github_url=f"web_upload://{file_id}",
                github_owner="web_upload",
                github_repo="files",
                file_type=get_file_type_enum(file_extension),
                file_size=file_size,
                user_id="anonymous",
                method=UploadMethod.WEB_UPLOAD,
                tracker_id=tracker_id,
                processing_status=ProcessingStatus.COMPLETED,
                extra_metadata={
                    "file_id": file_id,
                    "original_filename": file.filename,
                    "saved_filename": file_name,
                    "file_path": str(file_path),
                    "upload_method": "web_form"
                }
            )
            
            db.add(article)
            await db.commit()
            
            results.append({
                "file_id": file_id,
                "tracker_id": tracker_id,
                "original_name": file.filename,
                "saved_name": file_name,
                "file_size": file_size,
                "file_type": file_extension,
                "upload_time": datetime.now().isoformat(),
                "file_path": str(file_path)
            })
            
        except HTTPException as e:
            errors.append({
                "filename": file.filename,
                "error": e.detail
            })
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "success": len(errors) == 0,
        "message": f"上传完成，成功: {len(results)}，失败: {len(errors)}",
        "data": {
            "successful_uploads": results,
            "failed_uploads": errors,
            "total_files": len(files),
            "success_count": len(results),
            "error_count": len(errors)
        }
    }