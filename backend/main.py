"""
KB Upload Genie - 主应用入口
GitHub上传分类智能前端系统后端API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.services.email_service import email_service
from app.tasks.email_tasks import email_task_manager
from app.core.init_admin import init_admin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动 KB Upload Genie 后端服务...")
    
    # 确保上传目录存在并设置正确权限
    import os
    from pathlib import Path
    
    upload_dir = Path(settings.UPLOAD_DIR)
    email_attachments_dir = upload_dir / "email_attachments"
    
    try:
        # 创建目录
        upload_dir.mkdir(parents=True, exist_ok=True)
        email_attachments_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置目录权限（775 = rwxrwxr-x）
        os.chmod(upload_dir, 0o775)
        os.chmod(email_attachments_dir, 0o775)
        
        logger.info(f"上传目录创建成功: {upload_dir}")
        logger.info(f"邮件附件目录创建成功: {email_attachments_dir}")
        
        # 测试写入权限
        test_file = upload_dir / ".permission_test"
        test_file.write_text("test")
        test_file.unlink()  # 删除测试文件
        logger.info("上传目录写入权限测试通过")
        
    except PermissionError as e:
        logger.error(f"上传目录权限设置失败: {e}")
        logger.warning("将尝试使用当前权限继续运行")
    except Exception as e:
        logger.error(f"上传目录创建失败: {e}")
    
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("数据库初始化完成")
    
    # 初始化管理员用户
    try:
        await init_admin()
        logger.info("管理员用户初始化完成")
    except Exception as e:
        logger.error(f"管理员用户初始化失败: {str(e)}")
    
    # 启动邮件服务
    if settings.EMAIL_UPLOAD_ENABLED:
        await email_service.check_imap_connection()
        logger.info("邮件服务IMAP连接已建立")
        await email_task_manager.start_email_checking()
        logger.info("邮件检查任务已启动")
    else:
        logger.info("邮件上传功能未启用，跳过邮件检查任务")
    
    logger.info("KB Upload Genie 后端服务启动成功!")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭 KB Upload Genie 后端服务...")
    
    # 停止邮件检查任务
    if settings.EMAIL_UPLOAD_ENABLED:
        await email_task_manager.stop_email_checking()
        logger.info("邮件检查任务已停止")
        await email_service.disconnect_imap()
        logger.info("邮件服务IMAP连接已断开")


# 创建FastAPI应用实例
app = FastAPI(
    title="KB Upload Genie API",
    description="GitHub上传分类智能前端系统 - 后端API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    # 修复SwaggerUI静态资源问题
    swagger_ui_parameters={
        "syntaxHighlight.theme": "obsidian",
        "tryItOutEnabled": True,
    }
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在开发环境中允许所有来源，生产环境中应该限制
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type", "X-Process-Time"],
    max_age=600,  # 预检请求缓存10分钟
)

# 添加可信主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间到响应头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "内部服务器错误",
            "error": str(exc) if settings.DEBUG else "服务器内部错误"
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "KB Upload Genie API",
        "version": "1.0.0",
        "timestamp": time.time()
    }


# 根路径
@app.get("/")
async def root():
    """根路径欢迎信息"""
    return {
        "message": "欢迎使用 KB Upload Genie API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }


# 包含API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.DEBUG,
        log_level="info"
    )