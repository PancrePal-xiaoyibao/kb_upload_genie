#!/usr/bin/env python3
"""
数据库模型测试脚本
用于验证模型定义和关系是否正确
"""
import asyncio
import sys
import os

# 设置必要的环境变量
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-development-only')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./test.db')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models import *
    from app.core.database import Base
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


async def test_model_imports():
    """测试模型导入"""
    print("=== 测试模型导入 ===")
    
    try:
        # 测试模型类是否正确导入
        models = [User, Category, Article, Review, CopyrightRecord]
        enums = [UserRole, ArticleStatus, FileType, 
                ReviewType, ReviewStatus, ReviewCategory, CopyrightStatus, 
                CopyrightSource, SimilarityLevel]
        
        print("✓ 模型类导入成功:")
        for model in models:
            print(f"  - {model.__name__}")
        
        print("✓ 枚举类型导入成功:")
        for enum in enums:
            print(f"  - {enum.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ 模型导入失败: {e}")
        return False


async def test_model_relationships():
    """测试模型关系"""
    print("\n=== 测试模型关系 ===")
    
    try:
        # 检查User模型关系
        user_relationships = ['articles', 'reviews']
        for rel in user_relationships:
            if hasattr(User, rel):
                print(f"✓ User.{rel} 关系存在")
            else:
                print(f"✗ User.{rel} 关系缺失")
        
        # 检查Category模型关系
        category_relationships = ['parent', 'children', 'articles']
        for rel in category_relationships:
            if hasattr(Category, rel):
                print(f"✓ Category.{rel} 关系存在")
            else:
                print(f"✗ Category.{rel} 关系缺失")
        
        # 检查Article模型关系
        article_relationships = ['user', 'category', 'reviews', 'copyright_records']
        for rel in article_relationships:
            if hasattr(Article, rel):
                print(f"✓ Article.{rel} 关系存在")
            else:
                print(f"✗ Article.{rel} 关系缺失")
        
        return True
    except Exception as e:
        print(f"✗ 模型关系测试失败: {e}")
        return False


async def test_model_properties():
    """测试模型属性方法"""
    print("\n=== 测试模型属性方法 ===")
    
    try:
        # 测试User模型属性
        user_properties = ['is_admin', 'is_reviewer', 'is_active_user']
        for prop in user_properties:
            if hasattr(User, prop):
                print(f"✓ User.{prop} 属性存在")
            else:
                print(f"✗ User.{prop} 属性缺失")
        
        # 测试Category模型属性
        category_properties = ['is_root', 'is_leaf', 'full_path']
        for prop in category_properties:
            if hasattr(Category, prop):
                print(f"✓ Category.{prop} 属性存在")
            else:
                print(f"✗ Category.{prop} 属性缺失")
        
        # 测试Article模型属性
        article_properties = ['is_published', 'has_copyright_issues']
        for prop in article_properties:
            if hasattr(Article, prop):
                print(f"✓ Article.{prop} 属性存在")
            else:
                print(f"✗ Article.{prop} 属性缺失")
        
        return True
    except Exception as e:
        print(f"✗ 模型属性测试失败: {e}")
        return False


async def test_crud_imports():
    """测试CRUD操作导入"""
    print("\n=== 测试CRUD操作导入 ===")
    
    try:
        from app.crud import CRUDBase, CRUDUser, user, CRUDCategory, category, CRUDArticle, article
        
        print("✓ CRUD基类导入成功:")
        print(f"  - CRUDBase: {CRUDBase}")
        
        print("✓ CRUD操作类导入成功:")
        crud_classes = [
            ("CRUDUser", CRUDUser),
            ("CRUDCategory", CRUDCategory), 
            ("CRUDArticle", CRUDArticle)
        ]
        
        for name, cls in crud_classes:
            print(f"  - {name}: {cls}")
        
        print("✓ CRUD实例导入成功:")
        crud_instances = [
            ("user", user),
            ("category", category),
            ("article", article)
        ]
        
        for name, instance in crud_instances:
            print(f"  - {name}: {instance}")
        
        return True
    except Exception as e:
        print(f"✗ CRUD操作导入失败: {e}")
        return False


async def test_schema_imports():
    """测试数据模式导入"""
    print("\n=== 测试数据模式导入 ===")
    
    try:
        from app.schemas import (
            User, UserCreate, UserUpdate,
            Category, CategoryCreate, CategoryUpdate,
            Article, ArticleCreate, ArticleUpdate
        )
        
        print("✓ 用户模式导入成功:")
        user_schemas = [User, UserCreate, UserUpdate]
        for schema in user_schemas:
            print(f"  - {schema.__name__}")
        
        print("✓ 分类模式导入成功:")
        category_schemas = [Category, CategoryCreate, CategoryUpdate]
        for schema in category_schemas:
            print(f"  - {schema.__name__}")
        
        print("✓ 文章模式导入成功:")
        article_schemas = [Article, ArticleCreate, ArticleUpdate]
        for schema in article_schemas:
            print(f"  - {schema.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ 数据模式导入失败: {e}")
        return False


async def test_table_definitions():
    """测试表定义"""
    print("\n=== 测试表定义 ===")
    
    try:
        # 检查表是否在Base.metadata中注册
        tables = Base.metadata.tables
        expected_tables = ['users', 'categories', 'articles', 'reviews', 'copyright_records']
        
        print("已注册的表:")
        for table_name in tables:
            print(f"  - {table_name}")
        
        print("\n检查期望的表:")
        for table_name in expected_tables:
            if table_name in tables:
                table = tables[table_name]
                print(f"✓ {table_name} - {len(table.columns)} 个字段")
            else:
                print(f"✗ {table_name} - 未找到")
        
        return True
    except Exception as e:
        print(f"✗ 表定义测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("开始数据库模型测试...\n")
    
    tests = [
        test_model_imports,
        test_model_relationships,
        test_model_properties,
        test_crud_imports,
        test_schema_imports,
        test_table_definitions,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"测试 {test.__name__} 执行失败: {e}")
            results.append(False)
    
    # 总结
    print("\n" + "="*50)
    print("测试总结:")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 部分测试失败，请检查上述错误信息")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)