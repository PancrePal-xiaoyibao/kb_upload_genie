"""
数据库初始化脚本
用于创建表结构和初始数据
"""
import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine, get_db, Base
from app.core.seed_data import create_initial_data
from app.models import *  # 导入所有模型以确保表被创建

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """创建所有数据库表"""
    try:
        logger.info("开始创建数据库表...")
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        return False


async def check_database_connection():
    """检查数据库连接"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


async def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    # 检查数据库连接
    if not await check_database_connection():
        logger.error("数据库连接失败，初始化中止")
        return False
    
    # 创建表结构
    if not await create_tables():
        logger.error("创建表结构失败，初始化中止")
        return False
    
    # 创建初始数据
    try:
        async for db in get_db():
            await create_initial_data(db)
            break
        logger.info("初始数据创建成功")
    except Exception as e:
        logger.error(f"创建初始数据失败: {e}")
        return False
    
    logger.info("数据库初始化完成")
    return True


async def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    logger.warning("开始重置数据库...")
    
    try:
        # 删除所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("已删除所有表")
        
        # 重新初始化
        return await init_database()
    except Exception as e:
        logger.error(f"重置数据库失败: {e}")
        return False


async def check_tables_exist():
    """检查表是否存在"""
    try:
        async with engine.begin() as conn:
            # 检查主要表是否存在
            tables_to_check = ['users', 'categories', 'articles', 'reviews', 'copyright_records']
            existing_tables = []
            
            for table in tables_to_check:
                result = await conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """))
                exists = (await result.fetchone())[0]
                if exists:
                    existing_tables.append(table)
            
            logger.info(f"已存在的表: {existing_tables}")
            return len(existing_tables) == len(tables_to_check)
    except Exception as e:
        logger.error(f"检查表存在性失败: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            if command == "reset":
                success = await reset_database()
            elif command == "check":
                success = await check_tables_exist()
            else:
                success = await init_database()
        else:
            success = await init_database()
        
        if not success:
            sys.exit(1)
    
    # 运行主函数
    asyncio.run(main())