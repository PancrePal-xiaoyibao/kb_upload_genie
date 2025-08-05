"""
Redis服务
用于缓存和限流管理
"""

import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from typing import Optional, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis服务类"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        if settings.REDIS_ENABLED and settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                self.redis_client = None
    
    async def is_connected(self) -> bool:
        """检查Redis连接状态"""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    async def set_rate_limit(self, key: str, count: int, expire_seconds: int):
        """设置限流计数"""
        if not await self.is_connected():
            return
        
        try:
            await self.redis_client.setex(key, expire_seconds, count)
        except Exception as e:
            logger.error(f"设置Redis限流失败: {e}")
    
    async def get_rate_limit(self, key: str) -> Optional[int]:
        """获取限流计数"""
        if not await self.is_connected():
            return None
        
        try:
            value = await self.redis_client.get(key)
            return int(value) if value else None
        except Exception as e:
            logger.error(f"获取Redis限流失败: {e}")
            return None
    
    async def increment_rate_limit(self, key: str, expire_seconds: int) -> int:
        """增加限流计数"""
        if not await self.is_connected():
            return 0
        
        try:
            # 使用管道确保原子性
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, expire_seconds)
            results = await pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"增加Redis限流失败: {e}")
            return 0
    
    async def check_email_rate_limit(self, email_hash: str) -> dict:
        """检查邮件发送频率限制"""
        if not await self.is_connected():
            # 如果Redis不可用，返回允许状态
            return {"allowed": True, "hourly_count": 0, "daily_count": 0}
        
        try:
            hourly_key = f"email_rate_hourly:{email_hash}"
            daily_key = f"email_rate_daily:{email_hash}"
            
            # 获取当前计数
            hourly_count = await self.get_rate_limit(hourly_key) or 0
            daily_count = await self.get_rate_limit(daily_key) or 0
            
            # 检查限制
            if hourly_count >= settings.EMAIL_HOURLY_LIMIT:
                return {
                    "allowed": False,
                    "reason": "hourly_limit",
                    "hourly_count": hourly_count,
                    "daily_count": daily_count
                }
            
            if daily_count >= settings.EMAIL_DAILY_LIMIT:
                return {
                    "allowed": False,
                    "reason": "daily_limit",
                    "hourly_count": hourly_count,
                    "daily_count": daily_count
                }
            
            # 增加计数
            new_hourly = await self.increment_rate_limit(hourly_key, 3600)  # 1小时
            new_daily = await self.increment_rate_limit(daily_key, 86400)   # 24小时
            
            return {
                "allowed": True,
                "hourly_count": new_hourly,
                "daily_count": new_daily
            }
            
        except Exception as e:
            logger.error(f"检查邮件限流失败: {e}")
            # 出错时允许通过
            return {"allowed": True, "hourly_count": 0, "daily_count": 0}
    
    async def get_email_rate_stats(self, email_hash: str) -> dict:
        """获取邮件发送频率统计"""
        if not await self.is_connected():
            return {"hourly_count": 0, "daily_count": 0, "hourly_remaining": settings.EMAIL_HOURLY_LIMIT, "daily_remaining": settings.EMAIL_DAILY_LIMIT}
        
        try:
            hourly_key = f"email_rate_hourly:{email_hash}"
            daily_key = f"email_rate_daily:{email_hash}"
            
            hourly_count = await self.get_rate_limit(hourly_key) or 0
            daily_count = await self.get_rate_limit(daily_key) or 0
            
            return {
                "hourly_count": hourly_count,
                "daily_count": daily_count,
                "hourly_remaining": max(0, settings.EMAIL_HOURLY_LIMIT - hourly_count),
                "daily_remaining": max(0, settings.EMAIL_DAILY_LIMIT - daily_count)
            }
            
        except Exception as e:
            logger.error(f"获取邮件频率统计失败: {e}")
            return {"hourly_count": 0, "daily_count": 0, "hourly_remaining": settings.EMAIL_HOURLY_LIMIT, "daily_remaining": settings.EMAIL_DAILY_LIMIT}
    
    async def reset_email_rate_limit(self, email_hash: str, limit_type: str = "all"):
        """重置邮件频率限制"""
        if not await self.is_connected():
            return
        
        try:
            if limit_type in ["hourly", "all"]:
                hourly_key = f"email_rate_hourly:{email_hash}"
                await self.cache_delete(hourly_key)
            
            if limit_type in ["daily", "all"]:
                daily_key = f"email_rate_daily:{email_hash}"
                await self.cache_delete(daily_key)
                
            logger.info(f"重置邮件频率限制: {email_hash}, 类型: {limit_type}")
            
        except Exception as e:
            logger.error(f"重置邮件频率限制失败: {e}")
    
    async def set_email_blocked(self, email_hash: str, block_duration_seconds: int = 3600):
        """设置邮箱临时阻止状态"""
        if not await self.is_connected():
            return
        
        try:
            block_key = f"email_blocked:{email_hash}"
            await self.redis_client.setex(block_key, block_duration_seconds, "blocked")
            logger.info(f"设置邮箱阻止状态: {email_hash}, 持续时间: {block_duration_seconds}秒")
            
        except Exception as e:
            logger.error(f"设置邮箱阻止状态失败: {e}")
    
    async def is_email_blocked(self, email_hash: str) -> bool:
        """检查邮箱是否被阻止"""
        if not await self.is_connected():
            return False
        
        try:
            block_key = f"email_blocked:{email_hash}"
            result = await self.redis_client.get(block_key)
            return result is not None
            
        except Exception as e:
            logger.error(f"检查邮箱阻止状态失败: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """获取Redis值"""
        if not await self.is_connected():
            return None
        
        try:
            result = await self.redis_client.get(key)
            return result.decode() if isinstance(result, bytes) else result
        except Exception as e:
            logger.error(f"获取Redis值失败: {e}")
            return None
    
    async def incr(self, key: str) -> int:
        """递增Redis值"""
        if not await self.is_connected():
            return 0
        
        try:
            return await self.redis_client.incr(key)
        except Exception as e:
            logger.error(f"递增Redis值失败: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int):
        """设置Redis键过期时间"""
        if not await self.is_connected():
            return
        
        try:
            await self.redis_client.expire(key, seconds)
        except Exception as e:
            logger.error(f"设置Redis过期时间失败: {e}")
    
    async def cache_set(self, key: str, value: Any, expire_seconds: int = 3600):
        """设置缓存"""
        if not await self.is_connected():
            return
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            await self.redis_client.setex(key, expire_seconds, value)
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not await self.is_connected():
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value.decode() if isinstance(value, bytes) else value
            return None
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    async def cache_delete(self, key: str):
        """删除缓存"""
        if not await self.is_connected():
            return
        
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()


# 全局Redis服务实例
redis_service = RedisService()