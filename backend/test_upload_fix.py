#!/usr/bin/env python3
"""
测试上传API修复
验证500错误是否已解决
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path

async def test_upload_api():
    """测试上传API"""
    print("🧪 测试上传API修复...")
    
    # 创建测试文件
    test_file_path = Path("test_upload.txt")
    test_content = "这是一个测试文件，用于验证上传功能。\nTest upload functionality."
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 测试上传
        async with aiohttp.ClientSession() as session:
            with open(test_file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_upload.txt')
                data.add_field('turnstile_token', '')
                
                async with session.post(
                    'http://localhost:8000/api/v1/upload',
                    data=data
                ) as response:
                    status = response.status
                    result = await response.json()
                    
                    print(f"📊 响应状态: {status}")
                    print(f"📄 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    if status == 200:
                        print("✅ 上传API修复成功！")
                        if 'data' in result and 'tracker_id' in result['data']:
                            tracker_id = result['data']['tracker_id']
                            print(f"🔍 生成的跟踪ID: {tracker_id}")
                            
                            # 测试跟踪查询
                            await test_tracker_query(session, tracker_id)
                        return True
                    else:
                        print(f"❌ 上传仍然失败: {result}")
                        return False
                        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        # 清理测试文件
        if test_file_path.exists():
            test_file_path.unlink()

async def test_tracker_query(session, tracker_id):
    """测试跟踪查询功能"""
    print(f"\n🔍 测试跟踪查询功能...")
    
    try:
        async with session.get(
            f'http://localhost:8000/api/v1/tracker/status/{tracker_id}'
        ) as response:
            status = response.status
            result = await response.json()
            
            print(f"📊 查询状态: {status}")
            print(f"📄 查询结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if status == 200:
                print("✅ 跟踪查询功能正常！")
            else:
                print(f"❌ 跟踪查询失败: {result}")
                
    except Exception as e:
        print(f"❌ 跟踪查询测试失败: {e}")

async def test_health_check():
    """测试健康检查"""
    print("🏥 测试API健康检查...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/api/v1/health') as response:
                status = response.status
                result = await response.json()
                
                print(f"📊 健康检查状态: {status}")
                print(f"📄 健康检查结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                return status == 200
                
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试上传API修复...")
    
    # 1. 健康检查
    health_ok = await test_health_check()
    if not health_ok:
        print("❌ API服务不可用，请先启动后端服务")
        return
    
    # 2. 测试上传功能
    upload_ok = await test_upload_api()
    
    if upload_ok:
        print("\n🎉 所有测试通过！上传API修复成功！")
    else:
        print("\n❌ 测试失败，需要进一步检查")

if __name__ == "__main__":
    asyncio.run(main())