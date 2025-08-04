#!/usr/bin/env python3
"""
Turnstile验证模式测试脚本
"""

import requests
import os
from pathlib import Path

def test_upload_with_token(token=None):
    """测试带有或不带有token的上传"""
    # 创建测试文件
    test_file_path = "test_upload.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for Turnstile validation.")
    
    try:
        # 准备上传数据
        files = {'file': open(test_file_path, 'rb')}
        data = {}
        
        if token is not None:
            data['turnstile_token'] = token
            
        # 发送上传请求
        response = requests.post(
            'http://localhost:8000/api/v1/upload',
            files=files,
            data=data
        )
        
        print(f"测试令牌: {token or '无'}")
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
        print("-" * 50)
        
        return response.status_code == 200
        
    finally:
        # 清理测试文件
        files['file'].close()
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def get_turnstile_config():
    """获取Turnstile配置"""
    response = requests.get('http://localhost:8000/api/v1/turnstile/config')
    return response.json()

if __name__ == "__main__":
    print("🧪 Turnstile验证模式测试")
    print("=" * 50)
    
    # 获取配置
    config = get_turnstile_config()
    print(f"Turnstile配置: {config}")
    print("-" * 50)
    
    # 测试1: 无令牌
    print("测试1: 无令牌上传")
    test_upload_with_token(None)
    
    # 测试2: 空令牌
    print("测试2: 空令牌上传")
    test_upload_with_token("")
    
    # 测试3: 假令牌
    print("测试3: 假令牌上传")
    test_upload_with_token("fake_token_12345")
    
    print("✅ 测试完成")
    print("\n📝 配置说明:")
    print("- 要强制验证: 设置 TURNSTILE_ALLOW_SKIP_IN_DEV=false")
    print("- 要允许跳过: 设置 TURNSTILE_ALLOW_SKIP_IN_DEV=true")
