#!/usr/bin/env python3
"""
完整的上传功能测试
验证所有修复是否成功
"""

import asyncio
import aiohttp
import json
import os
import tempfile
from pathlib import Path

async def test_complete_upload_flow():
    """测试完整的上传流程"""
    print("🧪 测试完整上传流程...")
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是一个测试文件，用于验证上传和跟踪功能。\nTest upload and tracking functionality.")
        test_file_path = f.name
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. 测试单文件上传
            print("📤 测试单文件上传...")
            with open(test_file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_upload.txt')
                data.add_field('turnstile_token', '')
                
                async with session.post('http://localhost:8000/api/v1/upload', data=data) as response:
                    result = await response.json()
                    print(f"上传响应状态: {response.status}")
                    print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    if response.status == 200 and result.get('success'):
                        tracker_id = result['data']['tracker_id']
                        print(f"✅ 上传成功，Tracker ID: {tracker_id}")
                        
                        # 2. 测试跟踪查询
                        print(f"🔍 测试跟踪查询...")
                        await asyncio.sleep(1)  # 等待数据库写入
                        
                        async with session.get(f'http://localhost:8000/api/v1/tracker/status/{tracker_id}') as track_response:
                            track_result = await track_response.json()
                            print(f"跟踪查询状态: {track_response.status}")
                            print(f"跟踪结果: {json.dumps(track_result, indent=2, ensure_ascii=False)}")
                            
                            if track_response.status == 200:
                                print("✅ 跟踪查询成功")
                            else:
                                print("❌ 跟踪查询失败")
                    else:
                        print("❌ 上传失败")
                        
            # 3. 测试多文件上传
            print("\n📤 测试多文件上传...")
            files_data = aiohttp.FormData()
            
            # 创建多个测试文件
            test_files = []
            for i in range(2):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.txt', delete=False) as f:
                    f.write(f"测试文件 {i+1}\nTest file {i+1}")
                    test_files.append(f.name)
            
            try:
                for i, file_path in enumerate(test_files):
                    with open(file_path, 'rb') as f:
                        files_data.add_field('files', f, filename=f'test_multi_{i+1}.txt')
                
                files_data.add_field('turnstile_token', '')
                
                async with session.post('http://localhost:8000/api/v1/upload/multiple', data=files_data) as response:
                    result = await response.json()
                    print(f"多文件上传状态: {response.status}")
                    print(f"多文件上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    if response.status == 200:
                        print("✅ 多文件上传成功")
                    else:
                        print("❌ 多文件上传失败")
                        
            finally:
                # 清理测试文件
                for file_path in test_files:
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        
    finally:
        # 清理主测试文件
        try:
            os.unlink(test_file_path)
        except:
            pass

async def test_api_health():
    """测试API健康状态"""
    print("🏥 测试API健康状态...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试主API健康检查
            async with session.get('http://localhost:8000/api/v1/health') as response:
                result = await response.json()
                print(f"API健康检查: {response.status} - {result}")
                
            # 测试跟踪系统健康检查
            async with session.get('http://localhost:8000/api/v1/tracker/health') as response:
                result = await response.json()
                print(f"跟踪系统健康检查: {response.status} - {result}")
                
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始完整上传功能测试")
    print("=" * 50)
    
    await test_api_health()
    print("\n" + "=" * 50)
    await test_complete_upload_flow()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())