"""
跟踪系统集成测试
测试完整的上传跟踪流程
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class TrackerIntegrationTest:
    def __init__(self):
        self.test_results = []
        self.tracker_ids = []
    
    def log_test(self, test_name: str, success: bool, message: str, data: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        
        if data and not success:
            print(f"   详细信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    def test_api_health(self):
        """测试API健康状态"""
        try:
            response = requests.get(f"{API_BASE}/tracker/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API健康检查", 
                    True, 
                    f"服务状态: {data.get('status', 'unknown')}", 
                    data
                )
                return True
            else:
                self.log_test(
                    "API健康检查", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("API健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_invalid_tracker_query(self):
        """测试无效跟踪ID查询"""
        invalid_ids = [
            "",  # 空ID
            "invalid",  # 格式错误
            "TRK-NONEXISTENT-ID",  # 不存在的ID
            "12345",  # 太短
            "a" * 100  # 太长
        ]
        
        for invalid_id in invalid_ids:
            try:
                response = requests.get(
                    f"{API_BASE}/tracker/status/{invalid_id}",
                    timeout=10
                )
                
                if response.status_code in [400, 404]:
                    data = response.json()
                    self.log_test(
                        f"无效ID测试 ({invalid_id[:20]}...)", 
                        True, 
                        f"正确返回错误: {data.get('message', 'unknown')}"
                    )
                else:
                    self.log_test(
                        f"无效ID测试 ({invalid_id[:20]}...)", 
                        False, 
                        f"应该返回错误但返回了 {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"无效ID测试 ({invalid_id[:20]}...)", 
                    False, 
                    f"请求异常: {str(e)}"
                )
    
    def test_tracker_query_post(self):
        """测试POST方式查询跟踪状态"""
        test_data = {
            "tracker_id": "TRK-TEST-NONEXISTENT"
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/tracker/query",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 404]:
                data = response.json()
                self.log_test(
                    "POST查询测试", 
                    True, 
                    f"API响应正常: {data.get('message', 'unknown')}", 
                    data
                )
            else:
                self.log_test(
                    "POST查询测试", 
                    False, 
                    f"意外的状态码: {response.status_code}", 
                    response.text
                )
                
        except Exception as e:
            self.log_test("POST查询测试", False, f"请求异常: {str(e)}")
    
    def test_file_upload_with_tracker(self):
        """测试文件上传并获取跟踪ID"""
        # 创建测试文件
        test_content = "这是一个测试文件，用于验证跟踪系统功能。"
        
        files = {
            'file': ('test_tracker.txt', test_content, 'text/plain')
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/upload",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'tracker_id' in data.get('data', {}):
                    tracker_id = data['data']['tracker_id']
                    self.tracker_ids.append(tracker_id)
                    
                    self.log_test(
                        "文件上传测试", 
                        True, 
                        f"上传成功，跟踪ID: {tracker_id}", 
                        data
                    )
                    
                    # 立即测试查询这个跟踪ID
                    self.test_specific_tracker_query(tracker_id)
                    
                else:
                    self.log_test(
                        "文件上传测试", 
                        False, 
                        "上传成功但未返回跟踪ID", 
                        data
                    )
            else:
                self.log_test(
                    "文件上传测试", 
                    False, 
                    f"上传失败: HTTP {response.status_code}", 
                    response.text
                )
                
        except Exception as e:
            self.log_test("文件上传测试", False, f"上传异常: {str(e)}")
    
    def test_specific_tracker_query(self, tracker_id: str):
        """测试特定跟踪ID的查询"""
        try:
            response = requests.get(
                f"{API_BASE}/tracker/status/{tracker_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and data.get('data'):
                    tracker_data = data['data']
                    self.log_test(
                        f"跟踪查询测试 ({tracker_id[:12]}...)", 
                        True, 
                        f"状态: {tracker_data.get('processing_status', 'unknown')}", 
                        tracker_data
                    )
                else:
                    self.log_test(
                        f"跟踪查询测试 ({tracker_id[:12]}...)", 
                        False, 
                        "查询成功但数据格式错误", 
                        data
                    )
            else:
                self.log_test(
                    f"跟踪查询测试 ({tracker_id[:12]}...)", 
                    False, 
                    f"查询失败: HTTP {response.status_code}", 
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                f"跟踪查询测试 ({tracker_id[:12]}...)", 
                False, 
                f"查询异常: {str(e)}"
            )
    
    def test_frontend_accessibility(self):
        """测试前端页面可访问性"""
        try:
            response = requests.get(f"{BASE_URL}/tracker", timeout=10)
            
            if response.status_code == 200:
                # 检查页面是否包含关键元素
                content = response.text
                
                key_elements = [
                    "上传跟踪",  # 页面标题
                    "跟踪ID",    # 输入标签
                    "查询状态",  # 按钮文本
                ]
                
                missing_elements = []
                for element in key_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    self.log_test(
                        "前端页面测试", 
                        True, 
                        "页面加载正常，包含所有关键元素"
                    )
                else:
                    self.log_test(
                        "前端页面测试", 
                        False, 
                        f"页面缺少元素: {', '.join(missing_elements)}"
                    )
            else:
                self.log_test(
                    "前端页面测试", 
                    False, 
                    f"页面加载失败: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("前端页面测试", False, f"页面访问异常: {str(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始跟踪系统集成测试...")
        print("=" * 50)
        
        # 基础测试
        if not self.test_api_health():
            print("❌ API服务不可用，跳过其他测试")
            return self.generate_report()
        
        # 功能测试
        self.test_invalid_tracker_query()
        self.test_tracker_query_post()
        self.test_file_upload_with_tracker()
        self.test_frontend_accessibility()
        
        return self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        if self.tracker_ids:
            print(f"\n📋 生成的跟踪ID ({len(self.tracker_ids)}个):")
            for tracker_id in self.tracker_ids:
                print(f"  - {tracker_id}")
        
        # 保存详细报告
        report_file = f"tracker_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
                },
                "tracker_ids": self.tracker_ids,
                "detailed_results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return {
            "success": failed_tests == 0,
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "tracker_ids": self.tracker_ids
        }

def main():
    """主函数"""
    print("跟踪系统集成测试")
    print("确保后端服务运行在 http://localhost:8000")
    print("确保前端服务运行在相应端口")
    
    input("按回车键开始测试...")
    
    tester = TrackerIntegrationTest()
    result = tester.run_all_tests()
    
    if result['success']:
        print("\n🎉 所有测试通过！系统集成成功。")
        exit(0)
    else:
        print(f"\n⚠️  有 {result['failed']} 个测试失败，请检查系统配置。")
        exit(1)

if __name__ == "__main__":
    main()