"""
数据库迁移脚本：添加跟踪字段
为articles表添加method和tracker_id字段
"""

import asyncio
from sqlalchemy import text
from app.core.database import get_db_session

async def add_tracker_fields():
    """添加跟踪相关字段到articles表"""
    
    # SQL语句添加新字段
    add_method_field = """
    ALTER TABLE articles 
    ADD COLUMN IF NOT EXISTS method VARCHAR(50) DEFAULT 'unknown';
    """
    
    add_tracker_id_field = """
    ALTER TABLE articles 
    ADD COLUMN IF NOT EXISTS tracker_id VARCHAR(100) UNIQUE;
    """
    
    # 创建索引以提高查询性能
    create_tracker_index = """
    CREATE INDEX IF NOT EXISTS idx_articles_tracker_id 
    ON articles(tracker_id);
    """
    
    create_method_index = """
    CREATE INDEX IF NOT EXISTS idx_articles_method 
    ON articles(method);
    """
    
    # 添加处理状态字段（如果不存在）
    add_processing_status_field = """
    ALTER TABLE articles 
    ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending';
    """
    
    create_processing_status_index = """
    CREATE INDEX IF NOT EXISTS idx_articles_processing_status 
    ON articles(processing_status);
    """
    
    try:
        async with get_db_session() as db:
            print("开始添加跟踪字段...")
            
            # 执行字段添加
            await db.execute(text(add_method_field))
            print("✓ 添加method字段")
            
            await db.execute(text(add_tracker_id_field))
            print("✓ 添加tracker_id字段")
            
            await db.execute(text(add_processing_status_field))
            print("✓ 添加processing_status字段")
            
            # 创建索引
            await db.execute(text(create_tracker_index))
            print("✓ 创建tracker_id索引")
            
            await db.execute(text(create_method_index))
            print("✓ 创建method索引")
            
            await db.execute(text(create_processing_status_index))
            print("✓ 创建processing_status索引")
            
            await db.commit()
            print("✅ 数据库迁移完成")
            
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        raise

async def rollback_tracker_fields():
    """回滚跟踪字段（仅在必要时使用）"""
    
    rollback_sql = """
    ALTER TABLE articles 
    DROP COLUMN IF EXISTS method,
    DROP COLUMN IF EXISTS tracker_id,
    DROP COLUMN IF EXISTS processing_status;
    
    DROP INDEX IF EXISTS idx_articles_tracker_id;
    DROP INDEX IF EXISTS idx_articles_method;
    DROP INDEX IF EXISTS idx_articles_processing_status;
    """
    
    try:
        async with get_db_session() as db:
            print("开始回滚跟踪字段...")
            await db.execute(text(rollback_sql))
            await db.commit()
            print("✅ 回滚完成")
            
    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        raise

async def update_existing_records():
    """更新现有记录，为它们生成tracker_id"""
    
    from app.utils.tracker_utils import generate_tracker_id
    
    try:
        async with get_db_session() as db:
            print("开始更新现有记录...")
            
            # 查询没有tracker_id的记录
            result = await db.execute(text("""
                SELECT id FROM articles 
                WHERE tracker_id IS NULL 
                LIMIT 1000
            """))
            
            records = result.fetchall()
            
            if not records:
                print("✓ 没有需要更新的记录")
                return
            
            print(f"找到 {len(records)} 条需要更新的记录")
            
            # 批量更新
            for record in records:
                tracker_id = generate_tracker_id("LEGACY")
                await db.execute(text("""
                    UPDATE articles 
                    SET tracker_id = :tracker_id, 
                        method = 'legacy_import',
                        processing_status = 'completed'
                    WHERE id = :id
                """), {
                    "tracker_id": tracker_id,
                    "id": record.id
                })
            
            await db.commit()
            print(f"✅ 成功更新 {len(records)} 条记录")
            
    except Exception as e:
        print(f"❌ 更新现有记录失败: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            asyncio.run(add_tracker_fields())
        elif command == "rollback":
            asyncio.run(rollback_tracker_fields())
        elif command == "update":
            asyncio.run(update_existing_records())
        elif command == "full":
            # 完整迁移：添加字段 + 更新现有记录
            asyncio.run(add_tracker_fields())
            asyncio.run(update_existing_records())
        else:
            print("用法:")
            print("  python add_tracker_fields.py migrate   # 添加字段")
            print("  python add_tracker_fields.py rollback  # 回滚字段")
            print("  python add_tracker_fields.py update    # 更新现有记录")
            print("  python add_tracker_fields.py full      # 完整迁移")
    else:
        print("请指定操作: migrate, rollback, update, 或 full")