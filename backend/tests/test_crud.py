#!/usr/bin/env python3
"""
CRUD层测试脚本
用于验证Review和CopyrightRecord CRUD功能的正确性
"""
import asyncio
import sys
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Optional

# 设置必要的环境变量
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-development-only')

# 使用临时数据库进行测试
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db.close()
test_db_url = f'sqlite+aiosqlite:///{temp_db.name}'
os.environ.setdefault('DATABASE_URL', test_db_url)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models import User, Article, Category, Review, CopyrightRecord
    from app.models.review import ReviewType, ReviewStatus, ReviewCategory
    from app.models.copyright_record import CopyrightStatus, CopyrightSource, SimilarityLevel
    from app.models.user import UserRole
    from app.models.article import ArticleStatus, FileType
    from app.crud import CRUDReview, CRUDCopyrightRecord, review, copyright_record
    from app.schemas.review import ReviewCreate, ReviewUpdate
    from app.schemas.copyright_record import CopyrightRecordCreate, CopyrightRecordUpdate
    from app.core.database import Base, engine, AsyncSessionLocal
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


class TestData:
    """测试数据管理类"""
    
    def __init__(self, test_suffix=""):
        self.users = []
        self.categories = []
        self.articles = []
        self.reviews = []
        self.copyright_records = []
        self.test_suffix = test_suffix  # 用于确保数据唯一性
    
    async def create_test_data(self, db: AsyncSession):
        """创建测试数据"""
        print("创建测试数据...")
        
        # 创建测试用户
        test_users = [
            User(
                username=f"user{i}_{self.test_suffix}",
                email=f"user{i}_{self.test_suffix}@test.com",
                password_hash="hashed_password",
                role=UserRole.REVIEWER if i % 2 == 0 else UserRole.USER,
                is_active=True
            )
            for i in range(1, 6)
        ]
        
        for user in test_users:
            db.add(user)
        await db.commit()
        
        for user in test_users:
            await db.refresh(user)
        self.users = test_users
        
        # 创建测试分类
        test_categories = [
            Category(
                name=f"分类{i}_{self.test_suffix}",
                path=f"/category{i}_{self.test_suffix}",
                description=f"测试分类{i}"
            )
            for i in range(1, 4)
        ]
        
        for category in test_categories:
            db.add(category)
        await db.commit()
        
        for category in test_categories:
            await db.refresh(category)
        self.categories = test_categories
        
        # 创建测试文章
        test_articles = [
            Article(
                title=f"测试文章{i}_{self.test_suffix}",
                content=f"这是测试文章{i}的内容",
                summary=f"文章{i}摘要",
                github_url=f"https://github.com/test/repo{i}_{self.test_suffix}",
                github_owner="test",
                github_repo=f"repo{i}_{self.test_suffix}",
                file_type=FileType.CODE,
                user_id=self.users[i % len(self.users)].id,
                category_id=self.categories[i % len(self.categories)].id,
                status=ArticleStatus.PUBLISHED
            )
            for i in range(1, 6)
        ]
        
        for article in test_articles:
            db.add(article)
        await db.commit()
        
        for article in test_articles:
            await db.refresh(article)
        self.articles = test_articles
        
        print(f"✓ 创建了 {len(self.users)} 个用户")
        print(f"✓ 创建了 {len(self.categories)} 个分类")
        print(f"✓ 创建了 {len(self.articles)} 个文章")
    
    async def cleanup(self, db: AsyncSession):
        """清理测试数据"""
        print("清理测试数据...")
        
        # 删除所有测试数据
        for review in self.reviews:
            await db.delete(review)
        
        for copyright_record in self.copyright_records:
            await db.delete(copyright_record)
        
        for article in self.articles:
            await db.delete(article)
        
        for category in self.categories:
            await db.delete(category)
        
        for user in self.users:
            await db.delete(user)
        
        await db.commit()
        print("✓ 测试数据清理完成")


async def setup_database():
    """设置测试数据库"""
    print("设置测试数据库...")
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ 测试数据库设置完成")


async def test_review_crud_basic_operations():
    """测试Review CRUD基础操作"""
    print("\n=== 测试Review CRUD基础操作 ===")
    
    async with AsyncSessionLocal() as db:
        test_data = TestData("review_basic")
        await test_data.create_test_data(db)
        
        try:
            # 测试创建审核记录
            review_data = ReviewCreate(
                article_id=test_data.articles[0].id,
                review_type=ReviewType.AI,
                review_category=ReviewCategory.CONTENT_QUALITY,
                score=85,
                comments="测试审核评论"
            )
            
            created_review = await review.create(db, obj_in=review_data)
            test_data.reviews.append(created_review)
            print(f"✓ 创建审核记录: ID={created_review.id}")
            
            # 测试获取审核记录
            retrieved_review = await review.get(db, id=created_review.id)
            assert retrieved_review is not None
            assert retrieved_review.comments == "测试审核评论"
            print(f"✓ 获取审核记录: ID={retrieved_review.id}")
            
            # 测试更新审核记录
            update_data = ReviewUpdate(
                status=ReviewStatus.APPROVED,
                comments="更新后的评论",
                score=90
            )
            
            updated_review = await review.update(db, db_obj=retrieved_review, obj_in=update_data)
            assert updated_review.status == ReviewStatus.APPROVED
            assert updated_review.score == 85
            print(f"✓ 更新审核记录: 状态={updated_review.status}, 分数={updated_review.score}")
            
            # 测试删除审核记录
            await review.remove(db, id=created_review.id)
            deleted_review = await review.get(db, id=created_review.id)
            assert deleted_review is None
            print("✓ 删除审核记录成功")
            
            return True
            
        except Exception as e:
            print(f"✗ Review CRUD基础操作测试失败: {e}")
            return False
        finally:
            await test_data.cleanup(db)


async def test_review_business_methods():
    """测试Review业务逻辑方法"""
    print("\n=== 测试Review业务逻辑方法 ===")
    
    async with AsyncSessionLocal() as db:
        test_data = TestData("review_business")
        await test_data.create_test_data(db)
        
        try:
            # 创建多个审核记录用于测试
            reviews_data = [
                ReviewCreate(
                    article_id=test_data.articles[i % len(test_data.articles)].id,
                    review_type=ReviewType.AI,
                    review_category=ReviewCategory.CONTENT_QUALITY,
                    score=70 + i * 5,
                    comments=f"测试审核评论{i}"
                )
                for i in range(5)
            ]
            
            created_reviews = []
            for review_data in reviews_data:
                created_review = await review.create(db, obj_in=review_data)
                created_reviews.append(created_review)
                test_data.reviews.append(created_review)
            
            print(f"✓ 创建了 {len(created_reviews)} 个审核记录")
            
            # 测试根据文章ID获取审核记录
            article_reviews = await review.get_by_article_id(
                db, article_id=test_data.articles[0].id
            )
            assert len(article_reviews) > 0
            print(f"✓ 根据文章ID获取审核记录: {len(article_reviews)} 条")
            
            # 测试根据审核员获取审核记录
            reviewer_reviews = await review.get_by_reviewer(
                db, reviewer_id=test_data.users[0].id
            )
            assert len(reviewer_reviews) > 0
            print(f"✓ 根据审核员获取审核记录: {len(reviewer_reviews)} 条")
            
            # 测试根据状态获取审核记录
            pending_reviews = await review.get_by_status(
                db, status=ReviewStatus.PENDING
            )
            assert len(pending_reviews) >= 3
            print(f"✓ 根据状态获取审核记录: {len(pending_reviews)} 条待审核")
            
            # 测试分配审核员
            assigned_review = await review.assign_reviewer(
                db, 
                review_id=created_reviews[0].id,
                reviewer_id=test_data.users[1].id
            )
            assert assigned_review.reviewer_id == test_data.users[1].id
            print("✓ 分配审核员成功")
            
            # 测试获取待审核记录
            pending_reviews = await review.get_pending_reviews(db, limit=10)
            assert len(pending_reviews) > 0
            print(f"✓ 获取待审核记录: {len(pending_reviews)} 条")
            
            # 测试获取审核员工作量
            workload = await review.get_reviewer_workload(
                db, reviewer_id=test_data.users[0].id
            )
            assert workload >= 0
            print(f"✓ 获取审核员工作量: {workload}")
            
            # 测试获取审核统计
            stats = await review.get_review_stats(db)
            assert 'total' in stats
            assert 'by_status' in stats
            print(f"✓ 获取审核统计: 总计={stats['total']}")
            
            return True
            
        except Exception as e:
            print(f"✗ Review业务逻辑方法测试失败: {e}")
            return False
        finally:
            await test_data.cleanup(db)


async def test_copyright_record_crud_basic_operations():
    """测试CopyrightRecord CRUD基础操作"""
    print("\n=== 测试CopyrightRecord CRUD基础操作 ===")
    
    async with AsyncSessionLocal() as db:
        test_data = TestData("copyright_basic")
        await test_data.create_test_data(db)
        
        try:
            # 测试创建版权记录
            copyright_data = CopyrightRecordCreate(
                article_id=test_data.articles[0].id,
                copyright_source=CopyrightSource.GITHUB,
                similarity_level=SimilarityLevel.HIGH,
                similarity_score=0.755,
                source_url="https://example.com/source"
            )
            
            created_record = await copyright_record.create(db, obj_in=copyright_data)
            test_data.copyright_records.append(created_record)
            print(f"✓ 创建版权记录: ID={created_record.id}")
            
            # 测试获取版权记录
            retrieved_record = await copyright_record.get(db, id=created_record.id)
            assert retrieved_record is not None
            assert retrieved_record.similarity_score == 0.755
            print(f"✓ 获取版权记录: ID={retrieved_record.id}")
            
            # 测试更新版权记录
            update_data = CopyrightRecordUpdate(
                status=CopyrightStatus.CONFIRMED,
                similarity_score=0.85
            )
            
            updated_record = await copyright_record.update(
                db, db_obj=retrieved_record, obj_in=update_data
            )
            assert updated_record.status == CopyrightStatus.CONFIRMED
            assert updated_record.similarity_score == 0.85
            print(f"✓ 更新版权记录: 状态={updated_record.status}, 相似度={updated_record.similarity_score}")
            
            # 测试删除版权记录
            await copyright_record.remove(db, id=created_record.id)
            deleted_record = await copyright_record.get(db, id=created_record.id)
            assert deleted_record is None
            print("✓ 删除版权记录成功")
            
            return True
            
        except Exception as e:
            print(f"✗ CopyrightRecord CRUD基础操作测试失败: {e}")
            return False
        finally:
            await test_data.cleanup(db)


async def test_copyright_record_business_methods():
    """测试CopyrightRecord业务逻辑方法"""
    print("\n=== 测试CopyrightRecord业务逻辑方法 ===")
    
    async with AsyncSessionLocal() as db:
        test_data = TestData("copyright_business")
        await test_data.create_test_data(db)
        
        try:
            # 创建多个版权记录用于测试
            records_data = [
                CopyrightRecordCreate(
                    article_id=test_data.articles[i % len(test_data.articles)].id,
                    copyright_source=CopyrightSource.GITHUB,
                    similarity_level=SimilarityLevel.HIGH if i > 2 else SimilarityLevel.MEDIUM,
                    similarity_score=0.6 + i * 0.1,  # 0.6, 0.7, 0.8, 0.9, 1.0
                    source_url=f"https://example{i}.com/source",
                    matched_content=f"匹配内容{i}"
                )
                for i in range(5)
            ]
            
            created_records = []
            for record_data in records_data:
                created_record = await copyright_record.create(db, obj_in=record_data)
                created_records.append(created_record)
                test_data.copyright_records.append(created_record)
            
            print(f"✓ 创建了 {len(created_records)} 个版权记录")
            
            # 测试根据文章ID获取版权记录
            article_records = await copyright_record.get_by_article_id(
                db, article_id=test_data.articles[0].id
            )
            assert len(article_records) > 0
            print(f"✓ 根据文章ID获取版权记录: {len(article_records)} 条")
            
            # 测试根据状态获取版权记录
            pending_records = await copyright_record.get_by_status(
                db, status=CopyrightStatus.PENDING
            )
            assert len(pending_records) >= 2
            print(f"✓ 根据状态获取版权记录: {len(pending_records)} 条待处理")
            
            # 测试获取高风险记录
            high_risk_records = await copyright_record.get_high_risk_records(db)
            assert len(high_risk_records) > 0
            print(f"✓ 获取高风险记录: {len(high_risk_records)} 条")
            
            # 测试根据相似度范围查询
            similarity_records = await copyright_record.get_by_similarity_range(
                db, min_score=70.0, max_score=90.0
            )
            assert len(similarity_records) > 0
            print(f"✓ 根据相似度范围查询: {len(similarity_records)} 条")
            
            # 测试更新相似度分数
            updated_record = await copyright_record.update_similarity_score(
                db, 
                record_id=created_records[0].id,
                new_score=0.95
            )
            assert updated_record.similarity_score == 0.95
            print("✓ 更新相似度分数成功")
            
            # 测试标记误报
            marked_record = await copyright_record.mark_false_positive(
                db, 
                record_id=created_records[1].id,
                is_false_positive=True
            )
            assert marked_record.is_false_positive is True
            print("✓ 标记误报成功")
            
            # 测试获取版权统计
            stats = await copyright_record.get_copyright_stats(db)
            assert 'total' in stats
            assert 'by_status' in stats
            print(f"✓ 获取版权统计: 总计={stats['total']}")
            
            # 测试获取需要审核的记录
            needs_review = await copyright_record.get_needs_review(db)
            assert len(needs_review) >= 0
            print(f"✓ 获取需要审核的记录: {len(needs_review)} 条")
            
            return True
            
        except Exception as e:
            print(f"✗ CopyrightRecord业务逻辑方法测试失败: {e}")
            return False
        finally:
            await test_data.cleanup(db)


async def test_batch_operations():
    """测试批量操作"""
    print("\n=== 测试批量操作 ===")
    
    async with AsyncSessionLocal() as db:
        test_data = TestData("batch_ops")
        await test_data.create_test_data(db)
        
        try:
            # 创建多个审核记录用于批量操作测试
            reviews_data = [
                ReviewCreate(
                    article_id=test_data.articles[i % len(test_data.articles)].id,
                    review_type=ReviewType.AI,
                    review_category=ReviewCategory.CONTENT_QUALITY,
                    score=75 + i * 5,
                    comments=f"批量测试审核{i}"
                )
                for i in range(3)
            ]
            
            created_reviews = []
            for review_data in reviews_data:
                created_review = await review.create(db, obj_in=review_data)
                created_reviews.append(created_review)
                test_data.reviews.append(created_review)
            
            # 测试批量分配审核员
            review_ids = [r.id for r in created_reviews]
            assigned_count = await review.batch_assign(
                db,
                review_ids=review_ids,
                reviewer_id=test_data.users[1].id
            )
            assert assigned_count == len(review_ids)
            print(f"✓ 批量分配审核员: {assigned_count} 条记录")
            
            # 测试批量更新审核状态
            updated_count = await review.batch_update_status(
                db,
                review_ids=review_ids,
                new_status=ReviewStatus.APPROVED
            )
            assert updated_count == len(review_ids)
            print(f"✓ 批量更新审核状态: {updated_count} 条记录")
            
            # 创建版权记录用于批量操作测试
            records_data = [
                CopyrightRecordCreate(
                    article_id=test_data.articles[i % len(test_data.articles)].id,
                    copyright_source=CopyrightSource.GITHUB,
                    similarity_level=SimilarityLevel.HIGH,
                    similarity_score=0.7 + i * 0.05,
                    source_url=f"https://batch{i}.com",
                    matched_content=f"批量匹配内容{i}"
                )
                for i in range(3)
            ]
            
            created_records = []
            for record_data in records_data:
                created_record = await copyright_record.create(db, obj_in=record_data)
                created_records.append(created_record)
                test_data.copyright_records.append(created_record)
            
            # 测试批量版权检查
            article_ids = [test_data.articles[i].id for i in range(2)]
            check_results = await copyright_record.batch_check_copyright(
                db, article_ids=article_ids
            )
            assert len(check_results) == len(article_ids)
            print(f"✓ 批量版权检查: {len(check_results)} 个结果")
            
            # 测试批量更新版权状态
            record_ids = [r.id for r in created_records]
            updated_count = await copyright_record.batch_update_status(
                db,
                record_ids=record_ids,
                new_status=CopyrightStatus.CLEAR
            )
            assert updated_count == len(record_ids)
            print(f"✓ 批量更新版权状态: {updated_count} 条记录")
            
            return True
            
        except Exception as e:
            print(f"✗ 批量操作测试失败: {e}")
            return False
        finally:
            await test_data.cleanup(db)


async def test_search_and_filter():
    """测试搜索和过滤功能"""
    print("\n=== 测试搜索和过滤功能 ===")
    
    async with AsyncSessionLocal() as db:
        test_data = TestData("search_filter")
        await test_data.create_test_data(db)
        
        try:
            # 创建带有特定关键词的审核记录
            review_data = ReviewCreate(
                article_id=test_data.articles[0].id,
                review_type=ReviewType.AI,
                review_category=ReviewCategory.CONTENT_QUALITY,
                score=80,
                comments="这是一个包含搜索关键词的审核评论"
            )
            
            created_review = await review.create(db, obj_in=review_data)
            test_data.reviews.append(created_review)
            
            # 测试审核记录搜索
            from app.schemas.review import ReviewSearch
            search_params = ReviewSearch(
                review_type=ReviewType.AI,
                page=1,
                size=10
            )
            search_results = await review.search_reviews(
                db, 
                search_params=search_params
            )
            assert len(search_results) >= 0
            print(f"✓ 审核记录搜索: 找到 {len(search_results)} 条结果")
            
            # 创建版权记录用于搜索测试
            copyright_data = CopyrightRecordCreate(
                article_id=test_data.articles[0].id,
                copyright_source=CopyrightSource.GITHUB,
                similarity_level=SimilarityLevel.HIGH,
                similarity_score=0.8,
                source_url="https://search-test.com",
                matched_content="这是搜索测试的匹配内容"
            )
            
            created_record = await copyright_record.create(db, obj_in=copyright_data)
            test_data.copyright_records.append(created_record)
            
            # 测试版权记录搜索
            from app.schemas.copyright_record import CopyrightSearch
            search_params = CopyrightSearch(
                copyright_source=CopyrightSource.GITHUB,
                page=1,
                size=10
            )
            search_results, total_count = await copyright_record.search_records(
                db,
                search_params=search_params
            )
            assert len(search_results) >= 0
            print(f"✓ 版权记录搜索: 找到 {len(search_results)} 条结果，总计 {total_count} 条")
            
            return True
            
        except Exception as e:
            print(f"✗ 搜索和过滤功能测试失败: {e}")
            return False
        finally:
            await test_data.cleanup(db)


async def run_all_tests():
    """运行所有测试"""
    print("开始CRUD层测试...\n")
    
    # 设置测试数据库
    await setup_database()
    
    tests = [
        test_review_crud_basic_operations,
        test_review_business_methods,
        test_copyright_record_crud_basic_operations,
        test_copyright_record_business_methods,
        test_batch_operations,
        test_search_and_filter,
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
    print("\n" + "="*60)
    print("CRUD层测试总结:")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有CRUD测试通过！")
        print("✓ Review和CopyrightRecord CRUD功能验证成功")
        return True
    else:
        print("✗ 部分CRUD测试失败，请检查上述错误信息")
        return False


async def cleanup_test_database():
    """清理测试数据库"""
    try:
        # 关闭数据库连接
        await engine.dispose()
        
        # 删除临时数据库文件
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)
        
        print("✓ 测试数据库清理完成")
    except Exception as e:
        print(f"清理测试数据库时出错: {e}")


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        asyncio.run(cleanup_test_database())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        asyncio.run(cleanup_test_database())
        sys.exit(1)
    except Exception as e:
        print(f"测试执行出错: {e}")
        asyncio.run(cleanup_test_database())
        sys.exit(1)