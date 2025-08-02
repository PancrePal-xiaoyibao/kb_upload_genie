"""
用户CRUD操作
提供用户相关的数据库操作方法
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from passlib.context import CryptContext

from app.crud.base import CRUDBase
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户CRUD操作类"""
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码
            
        Returns:
            密码是否正确
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        获取密码哈希值
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码
        """
        return pwd_context.hash(password)
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            db: 数据库会话
            email: 用户邮箱
            
        Returns:
            用户实例或None
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户实例或None
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_by_username_or_email(
        self, 
        db: AsyncSession, 
        *, 
        identifier: str
    ) -> Optional[User]:
        """
        根据用户名或邮箱获取用户
        
        Args:
            db: 数据库会话
            identifier: 用户名或邮箱
            
        Returns:
            用户实例或None
        """
        result = await db.execute(
            select(User).where(
                or_(User.username == identifier, User.email == identifier)
            )
        )
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        创建用户
        
        Args:
            db: 数据库会话
            obj_in: 用户创建数据
            
        Returns:
            创建的用户实例
        """
        # 加密密码
        hashed_password = self.get_password_hash(obj_in.password)
        
        # 创建用户对象
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            password_hash=hashed_password,
            real_name=obj_in.real_name,
            role=obj_in.role or UserRole.USER,
            is_active=obj_in.is_active if obj_in.is_active is not None else True,
            github_username=obj_in.github_username,
            preferred_language=obj_in.preferred_language or "zh-CN",
            timezone=obj_in.timezone or "Asia/Shanghai"
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_password(
        self, 
        db: AsyncSession, 
        *, 
        user: User, 
        new_password: str
    ) -> User:
        """
        更新用户密码
        
        Args:
            db: 数据库会话
            user: 用户实例
            new_password: 新密码
            
        Returns:
            更新后的用户实例
        """
        hashed_password = self.get_password_hash(new_password)
        user.password_hash = hashed_password
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def authenticate(
        self, 
        db: AsyncSession, 
        *, 
        identifier: str, 
        password: str
    ) -> Optional[User]:
        """
        用户认证
        
        Args:
            db: 数据库会话
            identifier: 用户名或邮箱
            password: 密码
            
        Returns:
            认证成功的用户实例或None
        """
        user = await self.get_by_username_or_email(db, identifier=identifier)
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def is_active(self, user: User) -> bool:
        """
        检查用户是否激活
        
        Args:
            user: 用户实例
            
        Returns:
            用户是否激活
        """
        return user.is_active
    
    async def is_admin(self, user: User) -> bool:
        """
        检查用户是否为管理员
        
        Args:
            user: 用户实例
            
        Returns:
            用户是否为管理员
        """
        return user.role == UserRole.ADMIN
    
    async def is_reviewer(self, user: User) -> bool:
        """
        检查用户是否为审核员
        
        Args:
            user: 用户实例
            
        Returns:
            用户是否为审核员
        """
        return user.role in (UserRole.REVIEWER, UserRole.ADMIN)
    
    async def get_active_users(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """
        获取激活的用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            激活用户列表
        """
        result = await db.execute(
            select(User)
            .where(User.is_active == True)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_users_by_role(
        self, 
        db: AsyncSession, 
        *, 
        role: UserRole,
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """
        根据角色获取用户列表
        
        Args:
            db: 数据库会话
            role: 用户角色
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            指定角色的用户列表
        """
        result = await db.execute(
            select(User)
            .where(User.role == role)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def activate_user(self, db: AsyncSession, *, user: User) -> User:
        """
        激活用户
        
        Args:
            db: 数据库会话
            user: 用户实例
            
        Returns:
            激活后的用户实例
        """
        user.is_active = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def deactivate_user(self, db: AsyncSession, *, user: User) -> User:
        """
        停用用户
        
        Args:
            db: 数据库会话
            user: 用户实例
            
        Returns:
            停用后的用户实例
        """
        user.is_active = False
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


# 创建用户CRUD实例
user = CRUDUser(User)