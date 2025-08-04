"""
简化邮件附件管理系统启动脚本
"""

import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.simple_email_upload import router as simple_email_router
from app.tasks.simple_email_tasks import start_background_tasks, stop_background_tasks

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="简化邮件附件管理系统",
    description="通过邮件上传附件的简化管理系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(simple_email_router, tags=["简化邮件上传"])


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("启动简化邮件附件管理系统")
    
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 启动后台邮件监控任务
    asyncio.create_task(start_background_tasks())


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("关闭简化邮件附件管理系统")
    await stop_background_tasks()


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "简化邮件附件管理系统",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    # 运行应用
    uvicorn.run(
        "simple_email_system:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )