"""
初始数据种子文件
用于创建系统初始数据
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.core.database import get_db, init_db
from app.models import User, Category, UserRole


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)


async def create_admin_user(db: AsyncSession) -> None:
    """创建管理员用户"""
    # 检查是否已存在管理员
    result = await db.execute(
        select(User).where(User.role == UserRole.ADMIN)
    )
    admin_user = result.scalar_one_or_none()
    
    if admin_user:
        print("管理员用户已存在，跳过创建")
        return
    
    # 创建管理员用户
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        real_name="系统管理员",
        role=UserRole.ADMIN,
        is_active=True,
        preferred_language="zh-CN",
        timezone="Asia/Shanghai"
    )
    
    db.add(admin)
    await db.commit()
    print("管理员用户创建成功: admin / admin123")


async def create_default_categories(db: AsyncSession) -> None:
    """创建默认分类"""
    # 检查是否已存在分类
    result = await db.execute(select(Category))
    existing_categories = result.scalars().all()
    
    if existing_categories:
        print("分类已存在，跳过创建")
        return
    
    # 创建根分类
    categories = [
        # 编程语言类
        {
            "name": "编程语言",
            "slug": "programming-languages",
            "description": "各种编程语言相关的代码和文档",
            "level": 0,
            "sort_order": 1,
            "children": [
                {"name": "Python", "slug": "python", "description": "Python编程语言"},
                {"name": "JavaScript", "slug": "javascript", "description": "JavaScript编程语言"},
                {"name": "Java", "slug": "java", "description": "Java编程语言"},
                {"name": "Go", "slug": "go", "description": "Go编程语言"},
                {"name": "Rust", "slug": "rust", "description": "Rust编程语言"},
                {"name": "C++", "slug": "cpp", "description": "C++编程语言"},
            ]
        },
        
        # 框架和库
        {
            "name": "框架和库",
            "slug": "frameworks-libraries",
            "description": "各种开发框架和库",
            "level": 0,
            "sort_order": 2,
            "children": [
                {"name": "React", "slug": "react", "description": "React前端框架"},
                {"name": "Vue.js", "slug": "vuejs", "description": "Vue.js前端框架"},
                {"name": "Django", "slug": "django", "description": "Django Web框架"},
                {"name": "FastAPI", "slug": "fastapi", "description": "FastAPI Web框架"},
                {"name": "Spring", "slug": "spring", "description": "Spring框架"},
            ]
        },
        
        # 工具和配置
        {
            "name": "工具和配置",
            "slug": "tools-config",
            "description": "开发工具和配置文件",
            "level": 0,
            "sort_order": 3,
            "children": [
                {"name": "Docker", "slug": "docker", "description": "Docker容器化"},
                {"name": "Git", "slug": "git", "description": "Git版本控制"},
                {"name": "CI/CD", "slug": "cicd", "description": "持续集成和部署"},
                {"name": "配置文件", "slug": "config", "description": "各种配置文件"},
            ]
        },
        
        # 数据库
        {
            "name": "数据库",
            "slug": "database",
            "description": "数据库相关代码和脚本",
            "level": 0,
            "sort_order": 4,
            "children": [
                {"name": "SQL", "slug": "sql", "description": "SQL脚本和查询"},
                {"name": "PostgreSQL", "slug": "postgresql", "description": "PostgreSQL数据库"},
                {"name": "MySQL", "slug": "mysql", "description": "MySQL数据库"},
                {"name": "MongoDB", "slug": "mongodb", "description": "MongoDB数据库"},
                {"name": "Redis", "slug": "redis", "description": "Redis缓存"},
            ]
        },
        
        # 文档和教程
        {
            "name": "文档和教程",
            "slug": "docs-tutorials",
            "description": "技术文档和教程",
            "level": 0,
            "sort_order": 5,
            "children": [
                {"name": "API文档", "slug": "api-docs", "description": "API接口文档"},
                {"name": "使用指南", "slug": "user-guide", "description": "使用指南和教程"},
                {"name": "技术博客", "slug": "tech-blog", "description": "技术博客文章"},
                {"name": "README", "slug": "readme", "description": "项目说明文档"},
            ]
        },
        
        # 其他
        {
            "name": "其他",
            "slug": "others",
            "description": "其他类型的文件",
            "level": 0,
            "sort_order": 6,
            "children": [
                {"name": "脚本", "slug": "scripts", "description": "各种脚本文件"},
                {"name": "测试", "slug": "tests", "description": "测试代码和用例"},
                {"name": "示例", "slug": "examples", "description": "示例代码"},
                {"name": "未分类", "slug": "uncategorized", "description": "未分类的文件"},
            ]
        }
    ]
    
    # 创建分类
    for cat_data in categories:
        # 创建父分类
        parent_category = Category(
            name=cat_data["name"],
            slug=cat_data["slug"],
            description=cat_data["description"],
            level=cat_data["level"],
            sort_order=cat_data["sort_order"],
            is_active=True
        )
        db.add(parent_category)
        await db.flush()  # 获取ID
        
        # 创建子分类
        for i, child_data in enumerate(cat_data.get("children", [])):
            child_category = Category(
                name=child_data["name"],
                slug=child_data["slug"],
                description=child_data["description"],
                parent_id=parent_category.id,
                level=1,
                sort_order=i + 1,
                is_active=True
            )
            db.add(child_category)
    
    await db.commit()
    print("默认分类创建成功")


async def create_test_user(db: AsyncSession) -> None:
    """创建测试用户"""
    # 检查是否已存在测试用户
    result = await db.execute(
        select(User).where(User.username == "testuser")
    )
    test_user = result.scalar_one_or_none()
    
    if test_user:
        print("测试用户已存在，跳过创建")
        return
    
    # 创建测试用户
    test_user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("test123"),
        real_name="测试用户",
        role=UserRole.USER,
        is_active=True,
        preferred_language="zh-CN",
        timezone="Asia/Shanghai"
    )
    
    db.add(test_user)
    await db.commit()
    print("测试用户创建成功: testuser / test123")


async def create_reviewer_user(db: AsyncSession) -> None:
    """创建审核员用户"""
    # 检查是否已存在审核员
    result = await db.execute(
        select(User).where(User.username == "reviewer")
    )
    reviewer = result.scalar_one_or_none()
    
    if reviewer:
        print("审核员用户已存在，跳过创建")
        return
    
    # 创建审核员用户
    reviewer = User(
        username="reviewer",
        email="reviewer@example.com",
        password_hash=hash_password("reviewer123"),
        real_name="内容审核员",
        role=UserRole.REVIEWER,
        is_active=True,
        preferred_language="zh-CN",
        timezone="Asia/Shanghai"
    )
    
    db.add(reviewer)
    await db.commit()
    print("审核员用户创建成功: reviewer / reviewer123")


async def seed_database():
    """执行数据库种子数据创建"""
    print("开始创建初始数据...")
    
    # 初始化数据库
    await init_db()
    
    # 获取数据库会话
    async for db in get_db():
        try:
            # 创建管理员用户
            await create_admin_user(db)
            
            # 创建默认分类
            await create_default_categories(db)
            
            # 创建测试用户
            await create_test_user(db)
            
            # 创建审核员用户
            await create_reviewer_user(db)
            
            print("初始数据创建完成！")
            
        except Exception as e:
            print(f"创建初始数据时出错: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(seed_database())