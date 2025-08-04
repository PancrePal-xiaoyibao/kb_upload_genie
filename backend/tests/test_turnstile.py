"""
测试Turnstile集成的脚本
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.turnstile import verify_turnstile


async def test_turnstile_config():
    """测试Turnstile配置"""
    print("=== Turnstile配置测试 ===")
    print(f"TURNSTILE_ENABLED: {settings.TURNSTILE_ENABLED}")
    print(f"TURNSTILE_SITE_KEY: {settings.TURNSTILE_SITE_KEY}")
    print(f"TURNSTILE_SECRET_KEY: {'***' if settings.TURNSTILE_SECRET_KEY else None}")
    print()


async def test_turnstile_verification():
    """测试Turnstile验证功能"""
    print("=== Turnstile验证测试 ===")
    
    if not settings.TURNSTILE_ENABLED:
        print("Turnstile未启用，跳过验证测试")
        result = await verify_turnstile("test-token")
        print(f"未启用时验证结果: {result}")
        return
    
    if not settings.TURNSTILE_SECRET_KEY:
        print("警告: TURNSTILE_SECRET_KEY未配置")
        return
    
    print("测试无效令牌...")
    try:
        await verify_turnstile("invalid-token")
        print("错误: 无效令牌验证应该失败")
    except Exception as e:
        print(f"预期的验证失败: {e}")
    
    print("测试空令牌...")
    try:
        await verify_turnstile("")
        print("错误: 空令牌验证应该失败")
    except Exception as e:
        print(f"预期的验证失败: {e}")
    
    print("测试None令牌...")
    try:
        await verify_turnstile(None)
        print("错误: None令牌验证应该失败")
    except Exception as e:
        print(f"预期的验证失败: {e}")


async def test_api_endpoints():
    """测试API端点"""
    print("=== API端点测试 ===")
    
    try:
        from app.api.v1.api import get_turnstile_config
        
        config = await get_turnstile_config()
        print(f"Turnstile配置端点返回: {config}")
        
        if config["enabled"] and not config["site_key"]:
            print("警告: Turnstile已启用但没有site_key")
        
    except Exception as e:
        print(f"API端点测试失败: {e}")


async def main():
    """主测试函数"""
    print("开始Turnstile集成测试...\n")
    
    await test_turnstile_config()
    await test_turnstile_verification()
    await test_api_endpoints()
    
    print("\n=== 测试总结 ===")
    if settings.TURNSTILE_ENABLED:
        if settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY:
            print("✅ Turnstile配置完整")
        else:
            print("❌ Turnstile配置不完整，请检查环境变量")
    else:
        print("ℹ️  Turnstile未启用")
    
    print("\n配置步骤:")
    print("1. 访问 https://dash.cloudflare.com/?to=/:account/turnstile")
    print("2. 创建新的Turnstile站点")
    print("3. 在.env文件中设置:")
    print("   TURNSTILE_ENABLED=true")
    print("   TURNSTILE_SITE_KEY=你的站点密钥")
    print("   TURNSTILE_SECRET_KEY=你的秘密密钥")


if __name__ == "__main__":
    asyncio.run(main())
