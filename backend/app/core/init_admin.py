"""
管理员用户初始化模块
从环境变量读取管理员信息并创建管理员用户
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def create_admin_user():
    """创建管理员用户"""
    try:
        # 获取数据库会话
        async for session in get_db():
            # 检查管理员是否已存在
            result = await session.execute(
                select(User).where(User.email == settings.ADMIN_EMAIL)
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info(f"管理员用户已存在: {settings.ADMIN_EMAIL}")
                # 更新管理员密码（如果需要）
                existing_admin.set_password(settings.ADMIN_PASSWORD)
                existing_admin.role = UserRole.ADMIN
                existing_admin.status = UserStatus.ACTIVE
                await session.commit()
                logger.info("管理员用户信息已更新")
                return existing_admin
            
            # 创建新的管理员用户
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                name=settings.ADMIN_NAME,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE
            )
            admin_user.set_password(settings.ADMIN_PASSWORD)
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            logger.info(f"管理员用户创建成功: {settings.ADMIN_EMAIL}")
            return admin_user
            
    except Exception as e:
        logger.error(f"创建管理员用户失败: {str(e)}")
        raise


async def init_admin():
    """初始化管理员用户的主函数"""
    logger.info("开始初始化管理员用户...")
    admin_user = await create_admin_user()
    logger.info(f"管理员用户初始化完成: {admin_user.email}")
    return admin_user


if __name__ == "__main__":
    # 直接运行此脚本来初始化管理员
    asyncio.run(init_admin())