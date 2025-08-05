"""
域名限制服务
处理邮件域名的白名单和黑名单管理
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.email_upload import EmailDomainRule
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class DomainService:
    """域名限制服务类"""
    
    def __init__(self):
        self.cache_prefix = "domain_rule:"
        self.cache_expire = 3600  # 1小时缓存
    
    def _extract_domain(self, email_address: str) -> Optional[str]:
        """从邮箱地址提取域名"""
        try:
            if '@' not in email_address:
                return None
            
            domain = email_address.split('@')[-1].lower().strip()
            
            # 验证域名格式
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if re.match(domain_pattern, domain):
                return domain
            
            return None
            
        except Exception as e:
            logger.error(f"提取域名失败: {e}")
            return None
    
    def _is_valid_email(self, email_address: str) -> bool:
        """验证邮箱地址格式"""
        try:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(email_pattern, email_address) is not None
        except Exception:
            return False
    
    async def _get_cached_domain_rule(self, domain: str) -> Optional[bool]:
        """从缓存获取域名规则"""
        try:
            cache_key = f"{self.cache_prefix}{domain}"
            cached_result = await redis_service.cache_get(cache_key)
            
            if cached_result is not None:
                return cached_result == "allowed"
            
            return None
            
        except Exception as e:
            logger.error(f"获取域名规则缓存失败: {e}")
            return None
    
    async def _cache_domain_rule(self, domain: str, is_allowed: bool):
        """缓存域名规则"""
        try:
            cache_key = f"{self.cache_prefix}{domain}"
            cache_value = "allowed" if is_allowed else "blocked"
            await redis_service.cache_set(cache_key, cache_value, self.cache_expire)
            
        except Exception as e:
            logger.error(f"缓存域名规则失败: {e}")
    
    async def check_domain_allowed(self, email_address: str, db: AsyncSession) -> Tuple[bool, str]:
        """
        检查邮箱域名是否被允许
        返回: (是否允许, 原因说明)
        """
        try:
            # 验证邮箱格式
            if not self._is_valid_email(email_address):
                return False, "邮箱地址格式无效"
            
            # 提取域名
            domain = self._extract_domain(email_address)
            if not domain:
                return False, "无法提取邮箱域名"
            
            # 检查缓存
            cached_result = await self._get_cached_domain_rule(domain)
            if cached_result is not None:
                reason = "域名被允许" if cached_result else "域名被禁止"
                return cached_result, reason
            
            # 如果启用了域名白名单模式
            if settings.EMAIL_DOMAIN_WHITELIST_ENABLED:
                # 查询数据库中的域名规则
                stmt = select(EmailDomainRule).where(EmailDomainRule.domain == domain)
                result = await db.execute(stmt)
                domain_rule = result.scalar_one_or_none()
                
                if domain_rule:
                    is_allowed = domain_rule.is_allowed
                    reason = "域名在白名单中" if is_allowed else "域名在黑名单中"
                else:
                    # 如果没有找到规则，默认不允许
                    is_allowed = False
                    reason = "域名不在白名单中"
                
                # 缓存结果
                await self._cache_domain_rule(domain, is_allowed)
                return is_allowed, reason
            
            else:
                # 使用配置文件中的允许域名列表
                is_allowed = domain in settings.EMAIL_ALLOWED_DOMAINS
                reason = "域名在允许列表中" if is_allowed else "域名不在允许列表中"
                
                # 缓存结果
                await self._cache_domain_rule(domain, is_allowed)
                return is_allowed, reason
            
        except Exception as e:
            logger.error(f"检查域名权限失败: {e}")
            return False, "域名检查过程中出现错误"
    
    async def add_domain_rule(
        self, 
        domain: str, 
        is_allowed: bool, 
        description: str = None,
        db: AsyncSession = None
    ) -> Tuple[bool, str]:
        """
        添加域名规则
        返回: (是否成功, 消息)
        """
        try:
            # 验证域名格式
            domain = domain.lower().strip()
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if not re.match(domain_pattern, domain):
                return False, "域名格式无效"
            
            # 检查是否已存在
            stmt = select(EmailDomainRule).where(EmailDomainRule.domain == domain)
            result = await db.execute(stmt)
            existing_rule = result.scalar_one_or_none()
            
            if existing_rule:
                # 更新现有规则
                existing_rule.is_allowed = is_allowed
                existing_rule.description = description
                await db.commit()
                
                # 清除缓存
                await self._clear_domain_cache(domain)
                
                action = "允许" if is_allowed else "禁止"
                return True, f"域名规则已更新: {domain} -> {action}"
            
            else:
                # 创建新规则
                new_rule = EmailDomainRule(
                    domain=domain,
                    is_allowed=is_allowed,
                    description=description
                )
                
                db.add(new_rule)
                await db.commit()
                
                # 清除缓存
                await self._clear_domain_cache(domain)
                
                action = "允许" if is_allowed else "禁止"
                return True, f"域名规则已添加: {domain} -> {action}"
            
        except Exception as e:
            logger.error(f"添加域名规则失败: {e}")
            await db.rollback()
            return False, f"添加域名规则时出现错误: {str(e)}"
    
    async def remove_domain_rule(self, domain: str, db: AsyncSession) -> Tuple[bool, str]:
        """
        删除域名规则
        返回: (是否成功, 消息)
        """
        try:
            domain = domain.lower().strip()
            
            stmt = delete(EmailDomainRule).where(EmailDomainRule.domain == domain)
            result = await db.execute(stmt)
            
            if result.rowcount > 0:
                await db.commit()
                
                # 清除缓存
                await self._clear_domain_cache(domain)
                
                return True, f"域名规则已删除: {domain}"
            else:
                return False, f"域名规则不存在: {domain}"
            
        except Exception as e:
            logger.error(f"删除域名规则失败: {e}")
            await db.rollback()
            return False, f"删除域名规则时出现错误: {str(e)}"
    
    async def get_domain_rules(
        self, 
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        is_allowed: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        获取域名规则列表
        返回: 分页的域名规则数据
        """
        try:
            # 构建查询
            stmt = select(EmailDomainRule)
            
            if is_allowed is not None:
                stmt = stmt.where(EmailDomainRule.is_allowed == is_allowed)
            
            # 计算总数
            count_stmt = select(EmailDomainRule)
            if is_allowed is not None:
                count_stmt = count_stmt.where(EmailDomainRule.is_allowed == is_allowed)
            
            total_result = await db.execute(count_stmt)
            total_count = len(total_result.scalars().all())
            
            # 分页查询
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size).order_by(EmailDomainRule.created_at.desc())
            
            result = await db.execute(stmt)
            rules = result.scalars().all()
            
            # 转换为字典格式
            rules_data = []
            for rule in rules:
                rules_data.append({
                    'id': rule.id,
                    'domain': rule.domain,
                    'is_allowed': rule.is_allowed,
                    'description': rule.description,
                    'created_at': rule.created_at.isoformat(),
                    'updated_at': rule.updated_at.isoformat()
                })
            
            return {
                'rules': rules_data,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取域名规则失败: {e}")
            return {
                'rules': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
    
    async def _clear_domain_cache(self, domain: str):
        """清除域名缓存"""
        try:
            cache_key = f"{self.cache_prefix}{domain}"
            await redis_service.cache_delete(cache_key)
        except Exception as e:
            logger.error(f"清除域名缓存失败: {e}")
    
    async def clear_all_domain_cache(self):
        """清除所有域名缓存"""
        try:
            # 这里需要Redis支持模式匹配删除
            # 简单实现：记录所有缓存的域名，然后逐个删除
            logger.info("域名缓存清除功能需要Redis模式匹配支持")
        except Exception as e:
            logger.error(f"清除所有域名缓存失败: {e}")
    
    async def batch_add_domains(
        self, 
        domains: List[Dict[str, Any]], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        批量添加域名规则
        domains: [{'domain': 'example.com', 'is_allowed': True, 'description': '描述'}]
        返回: 批量操作结果
        """
        try:
            success_count = 0
            failed_count = 0
            errors = []
            
            for domain_data in domains:
                domain = domain_data.get('domain', '').lower().strip()
                is_allowed = domain_data.get('is_allowed', True)
                description = domain_data.get('description', '')
                
                success, message = await self.add_domain_rule(
                    domain, is_allowed, description, db
                )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"{domain}: {message}")
            
            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'errors': errors,
                'total': len(domains)
            }
            
        except Exception as e:
            logger.error(f"批量添加域名规则失败: {e}")
            return {
                'success_count': 0,
                'failed_count': len(domains),
                'errors': [f"批量操作失败: {str(e)}"],
                'total': len(domains)
            }
    
    async def get_domain_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """获取域名规则统计信息"""
        try:
            # 查询允许的域名数量
            allowed_stmt = select(EmailDomainRule).where(EmailDomainRule.is_allowed == True)
            allowed_result = await db.execute(allowed_stmt)
            allowed_count = len(allowed_result.scalars().all())
            
            # 查询禁止的域名数量
            blocked_stmt = select(EmailDomainRule).where(EmailDomainRule.is_allowed == False)
            blocked_result = await db.execute(blocked_stmt)
            blocked_count = len(blocked_result.scalars().all())
            
            return {
                'total_rules': allowed_count + blocked_count,
                'allowed_domains': allowed_count,
                'blocked_domains': blocked_count,
                'whitelist_enabled': settings.EMAIL_DOMAIN_WHITELIST_ENABLED,
                'config_allowed_domains': len(settings.EMAIL_ALLOWED_DOMAINS)
            }
            
        except Exception as e:
            logger.error(f"获取域名统计信息失败: {e}")
            return {
                'total_rules': 0,
                'allowed_domains': 0,
                'blocked_domains': 0,
                'whitelist_enabled': settings.EMAIL_DOMAIN_WHITELIST_ENABLED,
                'config_allowed_domains': len(settings.EMAIL_ALLOWED_DOMAINS)
            }


# 创建全局域名服务实例
domain_service = DomainService()
