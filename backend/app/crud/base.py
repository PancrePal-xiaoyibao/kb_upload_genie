"""
基础CRUD操作类
提供通用的数据库操作方法
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础CRUD操作类"""
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD对象
        
        Args:
            model: SQLAlchemy模型类
        """
        self.model = model
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        根据ID获取单个记录
        
        Args:
            db: 数据库会话
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        **filters
    ) -> List[ModelType]:
        """
        获取多个记录
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            order_by: 排序字段
            **filters: 过滤条件
            
        Returns:
            模型实例列表
        """
        query = select(self.model)
        
        # 添加过滤条件
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        
        # 添加排序
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at.desc())
        
        # 添加分页
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count(self, db: AsyncSession, **filters) -> int:
        """
        统计记录数量
        
        Args:
            db: 数据库会话
            **filters: 过滤条件
            
        Returns:
            记录数量
        """
        query = select(func.count(self.model.id))
        
        # 添加过滤条件
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        
        result = await db.execute(query)
        return result.scalar()
    
    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建新记录
        
        Args:
            db: 数据库会话
            obj_in: 创建数据
            
        Returns:
            创建的模型实例
        """
        obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新记录
        
        Args:
            db: 数据库会话
            db_obj: 数据库对象
            obj_in: 更新数据
            
        Returns:
            更新后的模型实例
        """
        obj_data = db_obj.__dict__.copy()
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        删除记录
        
        Args:
            db: 数据库会话
            id: 记录ID
            
        Returns:
            删除的模型实例或None
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def get_by_field(
        self,
        db: AsyncSession,
        field: str,
        value: Any
    ) -> Optional[ModelType]:
        """
        根据字段值获取记录
        
        Args:
            db: 数据库会话
            field: 字段名
            value: 字段值
            
        Returns:
            模型实例或None
        """
        if not hasattr(self.model, field):
            return None
        
        result = await db.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()
    
    async def exists(self, db: AsyncSession, **filters) -> bool:
        """
        检查记录是否存在
        
        Args:
            db: 数据库会话
            **filters: 过滤条件
            
        Returns:
            是否存在
        """
        query = select(self.model.id)
        
        # 添加过滤条件
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        
        result = await db.execute(query.limit(1))
        return result.scalar_one_or_none() is not None
    
    async def bulk_create(
        self,
        db: AsyncSession,
        *,
        objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        """
        批量创建记录
        
        Args:
            db: 数据库会话
            objs_in: 创建数据列表
            
        Returns:
            创建的模型实例列表
        """
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        await db.commit()
        
        # 刷新所有对象
        for db_obj in db_objs:
            await db.refresh(db_obj)
        
        return db_objs
    
    async def bulk_update(
        self,
        db: AsyncSession,
        *,
        updates: List[Dict[str, Any]]
    ) -> int:
        """
        批量更新记录
        
        Args:
            db: 数据库会话
            updates: 更新数据列表，每个字典必须包含id字段
            
        Returns:
            更新的记录数量
        """
        if not updates:
            return 0
        
        # 构建批量更新语句
        stmt = update(self.model)
        
        # 执行批量更新
        result = await db.execute(stmt, updates)
        await db.commit()
        
        return result.rowcount