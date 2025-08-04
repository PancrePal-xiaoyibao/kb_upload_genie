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
from datetime import datetime

from app.core.config import settings
from app.core.turnstile import verify_turnstile

# 创建API路由器
api_router = APIRouter()

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
    turnstile_token: Optional[str] = Form(None)
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
        
        # 返回上传结果
        return {
            "success": True,
            "message": "文件上传成功",
            "data": {
                "file_id": file_id,
                "original_name": file.filename,
                "saved_name": file_name,
                "file_size": file.size,
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
    turnstile_token: Optional[str] = Form(None)
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
            # 重用单文件上传逻辑
            result = await upload_file(file)
            results.append(result["data"])
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