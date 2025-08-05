"""
权限装饰器和工具函数
提供基于角色的访问控制
"""

from functools import wraps
from typing import Callable, List, Optional
from fastapi import HTTPException, status
from app.models.user import User, UserRole


def require_roles(allowed_roles: List[UserRole]):
    """
    角色权限装饰器
    
    Args:
        allowed_roles: 允许的角色列表
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user参数
            current_user = kwargs.get('current_user')
            if not current_user or not isinstance(current_user, User):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要身份验证"
                )
            
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {[role.value for role in allowed_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin_role(func: Callable):
    """管理员角色装饰器"""
    return require_roles([UserRole.ADMIN])(func)


def require_moderator_role(func: Callable):
    """审核员或管理员角色装饰器"""
    return require_roles([UserRole.MODERATOR, UserRole.ADMIN])(func)


class PermissionChecker:
    """权限检查器类"""
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """检查是否可以管理用户"""
        return user.is_admin and user.is_active and not user.is_locked
    
    @staticmethod
    def can_moderate_content(user: User) -> bool:
        """检查是否可以审核内容"""
        return user.is_moderator and user.is_active and not user.is_locked
    
    @staticmethod
    def can_access_admin_panel(user: User) -> bool:
        """检查是否可以访问管理面板"""
        return user.can_manage_system()
    
    @staticmethod
    def can_view_user_data(current_user: User, target_user: User) -> bool:
        """检查是否可以查看用户数据"""
        # 用户可以查看自己的数据，管理员可以查看所有用户数据
        return (current_user.id == target_user.id or 
                PermissionChecker.can_manage_users(current_user))
    
    @staticmethod
    def can_edit_user_data(current_user: User, target_user: User) -> bool:
        """检查是否可以编辑用户数据"""
        # 用户可以编辑自己的基本信息，管理员可以编辑所有用户数据
        if current_user.id == target_user.id:
            return True
        return PermissionChecker.can_manage_users(current_user)
    
    @staticmethod
    def can_delete_user(current_user: User, target_user: User) -> bool:
        """检查是否可以删除用户"""
        # 只有管理员可以删除用户，且不能删除自己
        return (PermissionChecker.can_manage_users(current_user) and 
                current_user.id != target_user.id)
    
    @staticmethod
    def can_change_user_role(current_user: User, target_user: User, new_role: UserRole) -> bool:
        """检查是否可以修改用户角色"""
        # 只有管理员可以修改角色，且不能修改自己的角色
        if not PermissionChecker.can_manage_users(current_user):
            return False
        
        if current_user.id == target_user.id:
            return False
        
        # 不能将用户提升为管理员（除非当前用户是超级管理员）
        if new_role == UserRole.ADMIN:
            # 这里可以添加超级管理员的逻辑
            return True
        
        return True


def check_permission(permission_func: Callable[[User], bool]):
    """
    通用权限检查装饰器
    
    Args:
        permission_func: 权限检查函数，接收User对象，返回bool
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or not isinstance(current_user, User):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要身份验证"
                )
            
            if not permission_func(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 常用权限装饰器
require_admin_permission = check_permission(PermissionChecker.can_manage_users)
require_moderator_permission = check_permission(PermissionChecker.can_moderate_content)
require_admin_panel_access = check_permission(PermissionChecker.can_access_admin_panel)