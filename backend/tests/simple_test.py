#!/usr/bin/env python3
"""简单的模型导入测试"""

import os
import sys

# 设置环境变量
os.environ['SECRET_KEY'] = 'test-key'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///test.db'

# 添加路径
sys.path.insert(0, 'app')

def test_imports():
    """测试模型导入"""
    try:
        print("开始测试模型导入...")
        
        # 测试基础模型导入
        from app.models import User, Category, Article, Review, CopyrightRecord
        print("✓ 基础模型导入成功")
        
        # 测试枚举导入
        from app.models import UserRole, ArticleStatus, ReviewType, CopyrightStatus
        print("✓ 枚举类型导入成功")
        
        # 测试表名
        print(f"User表名: {User.__tablename__}")
        print(f"Category表名: {Category.__tablename__}")
        print(f"Article表名: {Article.__tablename__}")
        print(f"Review表名: {Review.__tablename__}")
        print(f"CopyrightRecord表名: {CopyrightRecord.__tablename__}")
        
        # 测试枚举值
        print(f"UserRole枚举: {[role.value for role in UserRole]}")
        print(f"ArticleStatus枚举: {[status.value for status in ArticleStatus]}")
        
        print("✓ 所有测试通过!")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)