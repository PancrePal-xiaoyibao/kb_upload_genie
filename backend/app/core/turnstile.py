"""
Cloudflare Turnstile验证模块
"""

import httpx
from typing import Optional
from fastapi import HTTPException
from app.core.config import settings


class TurnstileVerifier:
    """Cloudflare Turnstile验证器"""
    
    VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    
    @classmethod
    async def verify_token(cls, token: str, remote_ip: Optional[str] = None) -> bool:
        """
        验证Turnstile令牌
        
        Args:
            token: 客户端获得的Turnstile令牌
            remote_ip: 客户端IP地址 (可选)
            
        Returns:
            bool: 验证是否成功
            
        Raises:
            HTTPException: 验证失败时抛出异常
        """
        if not settings.TURNSTILE_ENABLED:
            # 如果未启用Turnstile，则跳过验证
            return True
            
        if not settings.TURNSTILE_SECRET_KEY:
            raise HTTPException(
                status_code=500, 
                detail="Turnstile配置错误：缺少密钥"
            )
        
        if not token:
            # 检查是否允许在开发环境跳过验证
            is_dev_env = settings.DEBUG or "localhost" in str(settings.ALLOWED_HOSTS)
            
            if is_dev_env and settings.TURNSTILE_ALLOW_SKIP_IN_DEV:
                print("[Turnstile] 开发环境：允许跳过验证（TURNSTILE_ALLOW_SKIP_IN_DEV=true）")
                return True
            else:
                print(f"[Turnstile] 验证失败：缺少令牌（开发环境: {is_dev_env}, 允许跳过: {settings.TURNSTILE_ALLOW_SKIP_IN_DEV}）")
                raise HTTPException(
                    status_code=400,
                    detail="缺少Turnstile验证令牌，请先完成安全验证"
                )
        
        payload = {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": token,
        }
        
        if remote_ip:
            payload["remoteip"] = remote_ip
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    cls.VERIFY_URL,
                    data=payload,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail="Turnstile验证服务不可用"
                    )
                
                result = response.json()
                
                if not result.get("success", False):
                    error_codes = result.get("error-codes", [])
                    raise HTTPException(
                        status_code=400,
                        detail=f"Turnstile验证失败: {', '.join(error_codes)}"
                    )
                
                return True
                
        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="Turnstile验证服务连接失败"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Turnstile验证过程中发生错误: {str(e)}"
            )


async def verify_turnstile(token: str, remote_ip: Optional[str] = None) -> bool:
    """
    验证Turnstile令牌的便捷函数
    
    Args:
        token: Turnstile令牌
        remote_ip: 客户端IP地址
        
    Returns:
        bool: 验证是否成功
    """
    return await TurnstileVerifier.verify_token(token, remote_ip)
