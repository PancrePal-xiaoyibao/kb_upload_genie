"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建用户表
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('real_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.Enum('user', 'reviewer', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('github_username', sa.String(length=100), nullable=True),
        sa.Column('github_token', sa.String(length=255), nullable=True),
        sa.Column('preferred_language', sa.String(length=10), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='用户表'
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_github_username'), 'users', ['github_username'], unique=False)

    # 创建分类表
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('github_path', sa.String(length=500), nullable=True),
        sa.Column('github_repo', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('auto_sync', sa.Boolean(), nullable=False),
        sa.Column('ai_keywords', sa.JSON(), nullable=True),
        sa.Column('ai_description', sa.Text(), nullable=True),
        sa.Column('article_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='分类表'
    )
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)
    op.create_index(op.f('ix_categories_level'), 'categories', ['level'], unique=False)

    # 创建文章表
    op.create_table('articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('keywords', sa.String(length=500), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'pending', 'published', 'rejected', 'archived', name='articlestatus'), nullable=False),
        sa.Column('copyright_status', sa.Enum('unknown', 'clear', 'suspected', 'confirmed', name='copyrightstatus'), nullable=False),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('github_repo', sa.String(length=200), nullable=True),
        sa.Column('github_path', sa.String(length=500), nullable=True),
        sa.Column('github_branch', sa.String(length=100), nullable=True),
        sa.Column('github_commit', sa.String(length=100), nullable=True),
        sa.Column('file_type', sa.Enum('markdown', 'text', 'code', 'jupyter', 'pdf', 'other', name='filetype'), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('ai_tags', sa.JSON(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_category_suggestion', sa.JSON(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('download_count', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='文章表'
    )
    op.create_index(op.f('ix_articles_category_id'), 'articles', ['category_id'], unique=False)
    op.create_index(op.f('ix_articles_user_id'), 'articles', ['user_id'], unique=False)
    op.create_index(op.f('ix_articles_status'), 'articles', ['status'], unique=False)
    op.create_index(op.f('ix_articles_github_url'), 'articles', ['github_url'], unique=False)

    # 创建审核记录表
    op.create_table('reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=True),
        sa.Column('review_type', sa.Enum('ai', 'human', 'system', name='reviewtype'), nullable=False),
        sa.Column('review_category', sa.Enum('content_quality', 'copyright', 'classification', 'compliance', 'technical', name='reviewcategory'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'needs_revision', name='reviewstatus'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('ai_model_version', sa.String(length=50), nullable=True),
        sa.Column('ai_response_time', sa.Float(), nullable=True),
        sa.Column('ai_raw_response', sa.JSON(), nullable=True),
        sa.Column('issues_found', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=False),
        sa.Column('requires_human_review', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.String(length=50), nullable=True),
        sa.Column('completed_at', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='审核记录表'
    )
    op.create_index(op.f('ix_reviews_article_id'), 'reviews', ['article_id'], unique=False)

    # 创建版权记录表
    op.create_table('copyright_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('reporter_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('checking', 'clear', 'suspected', 'confirmed', 'disputed', 'resolved', name='copyrightstatus'), nullable=False),
        sa.Column('source', sa.Enum('ai_detection', 'manual_report', 'system_scan', 'external_api', 'dmca_notice', name='copyrightsource'), nullable=False),
        sa.Column('original_url', sa.String(length=500), nullable=True),
        sa.Column('original_title', sa.String(length=200), nullable=True),
        sa.Column('original_author', sa.String(length=100), nullable=True),
        sa.Column('original_publish_date', sa.String(length=50), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('similarity_level', sa.Enum('low', 'medium', 'high', 'very_high', name='similaritylevel'), nullable=True),
        sa.Column('matched_segments', sa.JSON(), nullable=True),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_analysis', sa.JSON(), nullable=True),
        sa.Column('check_method', sa.String(length=100), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.String(length=200), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('dmca_notice_id', sa.String(length=100), nullable=True),
        sa.Column('legal_status', sa.String(length=50), nullable=True),
        sa.Column('detected_at', sa.String(length=50), nullable=True),
        sa.Column('resolved_at', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='版权记录表'
    )
    op.create_index(op.f('ix_copyright_records_article_id'), 'copyright_records', ['article_id'], unique=False)


def downgrade() -> None:
    # 删除表（按依赖关系逆序）
    op.drop_table('copyright_records')
    op.drop_table('reviews')
    op.drop_table('articles')
    op.drop_table('categories')
    op.drop_table('users')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS articlestatus')
    op.execute('DROP TYPE IF EXISTS copyrightstatus')
    op.execute('DROP TYPE IF EXISTS filetype')
    op.execute('DROP TYPE IF EXISTS reviewtype')
    op.execute('DROP TYPE IF EXISTS reviewcategory')
    op.execute('DROP TYPE IF EXISTS reviewstatus')
    op.execute('DROP TYPE IF EXISTS copyrightsource')
    op.execute('DROP TYPE IF EXISTS similaritylevel')