#!/usr/bin/env python3
"""
测试所有数据模式的导入
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['SECRET_KEY'] = 'test-secret-key-for-schemas'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test_schemas.db'

def test_schema_imports():
    """测试所有数据模式的导入"""
    print("开始测试数据模式导入...")
    
    try:
        # 测试用户模式
        print("测试用户模式...")
        from app.schemas.user import (
            User, UserCreate, UserUpdate, UserPasswordUpdate,
            UserLogin, UserProfile, UserStats, UserInDB
        )
        print("✓ 用户模式导入成功")
        
        # 测试分类模式
        print("测试分类模式...")
        from app.schemas.category import (
            Category, CategoryCreate, CategoryUpdate, CategoryWithChildren,
            CategoryWithParent, CategoryTree, CategoryStats, CategoryMove, CategorySearch
        )
        print("✓ 分类模式导入成功")
        
        # 测试文章模式
        print("测试文章模式...")
        from app.schemas.article import (
            Article, ArticleCreate, ArticleUpdate, ArticleInDB, ArticleDetail,
            ArticleList, ArticleSearch, ArticleStats, ArticleSync, ArticleSyncResult,
            ArticleBatch, ArticleBatchResult
        )
        print("✓ 文章模式导入成功")
        
        # 测试审核模式
        print("测试审核模式...")
        from app.schemas.review import (
            Review, ReviewCreate, ReviewUpdate, ReviewInDB, ReviewDetail,
            ReviewList, ReviewSearch, ReviewStats, ReviewAssign,
            ReviewBatch, ReviewBatchResult
        )
        print("✓ 审核模式导入成功")
        
        # 测试版权记录模式
        print("测试版权记录模式...")
        from app.schemas.copyright_record import (
            CopyrightRecord, CopyrightRecordCreate, CopyrightRecordUpdate, CopyrightRecordInDB,
            CopyrightRecordDetail, CopyrightRecordList, CopyrightSearch, CopyrightStats,
            CopyrightCheck, CopyrightCheckResult, CopyrightBatch, CopyrightBatchResult
        )
        print("✓ 版权记录模式导入成功")
        
        # 测试统一导入
        print("测试统一导入...")
        from app.schemas import (
            User, UserCreate, Category, CategoryCreate, Article, ArticleCreate,
            Review, ReviewCreate, CopyrightRecord, CopyrightRecordCreate
        )
        print("✓ 统一导入成功")
        
        print("\n所有数据模式测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据模式导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_validation():
    """测试数据模式验证"""
    print("\n开始测试数据模式验证...")
    
    try:
        from app.schemas.user import UserCreate
        from app.schemas.category import CategoryCreate
        from app.schemas.article import ArticleCreate
        
        # 测试用户创建验证
        print("测试用户创建验证...")
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        user = UserCreate(**user_data)
        print(f"✓ 用户创建验证成功: {user.username}")
        
        # 测试分类创建验证
        print("测试分类创建验证...")
        category_data = {
            "name": "测试分类",
            "slug": "test-category",
            "description": "这是一个测试分类"
        }
        category = CategoryCreate(**category_data)
        print(f"✓ 分类创建验证成功: {category.name}")
        
        # 测试文章创建验证
        print("测试文章创建验证...")
        from app.models.article import FileType
        article_data = {
            "title": "测试文章",
            "description": "这是一个测试文章",
            "github_url": "https://github.com/test/repo",
            "github_owner": "test",
            "github_repo": "repo",
            "file_type": FileType.MARKDOWN,
            "category_id": 1,
            "user_id": 1
        }
        article = ArticleCreate(**article_data)
        print(f"✓ 文章创建验证成功: {article.title}")
        
        print("\n所有数据模式验证测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据模式验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = True
    
    # 测试导入
    if not test_schema_imports():
        success = False
    
    # 测试验证
    if not test_schema_validation():
        success = False
    
    if success:
        print("\n🎉 所有测试通过！数据模式层构建完成。")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)