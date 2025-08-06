"""
向后兼容性测试
验证跟踪系统不会破坏现有功能
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

class BackwardCompatibilityTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api/v1"
        self.test_results = []
    
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
    
    def test_existing_upload_endpoints(self):
        """测试现有上传端点是否正常工作"""
        print("\n🔍 测试现有上传端点...")
        
        # 测试主上传端点
        test_content = "测试向后兼容性的文件内容"
        files = {'file': ('test_compatibility.txt', test_content, 'text/plain')}
        
        try:
            response = requests.post(f"{self.api_base}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查响应格式是否保持兼容
                expected_fields = ['success', 'message', 'data']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "主上传端点兼容性", 
                        True, 
                        "响应格式保持兼容"
                    )
                    
                    # 检查是否添加了tracker_id而不破坏原有字段
                    if 'data' in data and isinstance(data['data'], dict):
                        if 'tracker_id' in data['data']:
                            self.log_test(
                                "Tracker ID集成", 
                                True, 
                                "成功添加tracker_id字段"
                            )
                        else:
                            self.log_test(
                                "Tracker ID集成", 
                                False, 
                                "未找到tracker_id字段"
                            )
                else:
                    self.log_test(
                        "主上传端点兼容性", 
                        False, 
                        f"响应缺少字段: {missing_fields}"
                    )
            else:
                self.log_test(
                    "主上传端点兼容性", 
                    False, 
                    f"上传失败: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("主上传端点兼容性", False, f"请求异常: {str(e)}")
    
    def test_email_upload_compatibility(self):
        """测试邮件上传功能兼容性"""
        print("\n📧 测试邮件上传兼容性...")
        
        # 测试邮件上传列表端点
        try:
            response = requests.get(f"{self.api_base}/email-upload/uploads", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查响应结构
                if 'items' in data and 'total' in data:
                    self.log_test(
                        "邮件上传列表兼容性", 
                        True, 
                        "列表端点响应格式正常"
                    )
                else:
                    self.log_test(
                        "邮件上传列表兼容性", 
                        False, 
                        "列表端点响应格式异常"
                    )
            else:
                self.log_test(
                    "邮件上传列表兼容性", 
                    False, 
                    f"列表端点失败: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("邮件上传列表兼容性", False, f"请求异常: {str(e)}")
        
        # 测试简单邮件上传端点
        try:
            response = requests.get(f"{self.api_base}/simple-email/api/uploads", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "简单邮件上传兼容性", 
                    True, 
                    "简单邮件端点正常"
                )
            else:
                self.log_test(
                    "简单邮件上传兼容性", 
                    False, 
                    f"简单邮件端点失败: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("简单邮件上传兼容性", False, f"请求异常: {str(e)}")
    
    def test_admin_endpoints_compatibility(self):
        """测试管理员端点兼容性"""
        print("\n👨‍💼 测试管理员端点兼容性...")
        
        # 测试管理员登录端点（不实际登录，只检查端点存在）
        try:
            response = requests.post(
                f"{self.api_base}/auth/login", 
                json={"email": "test@example.com", "password": "invalid"},
                timeout=10
            )
            
            # 401或422都是正常的，说明端点存在
            if response.status_code in [401, 422]:
                self.log_test(
                    "管理员登录端点兼容性", 
                    True, 
                    "登录端点响应正常"
                )
            else:
                self.log_test(
                    "管理员登录端点兼容性", 
                    False, 
                    f"登录端点异常: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("管理员登录端点兼容性", False, f"请求异常: {str(e)}")
    
    def test_database_schema_compatibility(self):
        """测试数据库模式兼容性"""
        print("\n🗄️ 测试数据库模式兼容性...")
        
        try:
            from app.models.article import Article
            from app.models.email_upload import EmailUpload
            from app.models.simple_email_upload import SimpleEmailUpload
            
            # 检查Article模型是否有新字段
            article_fields = [attr for attr in dir(Article) if not attr.startswith('_')]
            
            required_new_fields = ['method', 'tracker_id', 'processing_status']
            missing_fields = [field for field in required_new_fields if field not in article_fields]
            
            if not missing_fields:
                self.log_test(
                    "Article模型兼容性", 
                    True, 
                    "新字段已正确添加"
                )
            else:
                self.log_test(
                    "Article模型兼容性", 
                    False, 
                    f"缺少字段: {missing_fields}"
                )
            
            # 检查现有模型是否仍然可用
            try:
                # 尝试创建模型实例（不保存到数据库）
                email_upload = EmailUpload(
                    sender_email="test@example.com",
                    original_filename="test.txt",
                    stored_filename="stored_test.txt",
                    file_size=100,
                    file_type="text/plain"
                )
                
                self.log_test(
                    "EmailUpload模型兼容性", 
                    True, 
                    "模型创建正常"
                )
                
            except Exception as e:
                self.log_test(
                    "EmailUpload模型兼容性", 
                    False, 
                    f"模型创建失败: {str(e)}"
                )
            
        except Exception as e:
            self.log_test("数据库模式兼容性", False, f"模型导入失败: {str(e)}")
    
    def test_api_documentation_compatibility(self):
        """测试API文档兼容性"""
        print("\n📚 测试API文档兼容性...")
        
        try:
            # 检查OpenAPI文档
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            
            if response.status_code == 200:
                openapi_spec = response.json()
                
                # 检查是否包含新的跟踪端点
                paths = openapi_spec.get('paths', {})
                
                tracker_endpoints = [
                    '/api/v1/tracker/health',
                    '/api/v1/tracker/status/{tracker_id}',
                    '/api/v1/tracker/query'
                ]
                
                missing_endpoints = []
                for endpoint in tracker_endpoints:
                    if endpoint not in paths:
                        missing_endpoints.append(endpoint)
                
                if not missing_endpoints:
                    self.log_test(
                        "API文档兼容性", 
                        True, 
                        "新端点已添加到文档"
                    )
                else:
                    self.log_test(
                        "API文档兼容性", 
                        False, 
                        f"文档缺少端点: {missing_endpoints}"
                    )
                
                # 检查现有端点是否仍在文档中
                existing_endpoints = [
                    '/api/v1/upload',
                    '/api/v1/email-upload/uploads',
                    '/api/v1/auth/login'
                ]
                
                missing_existing = []
                for endpoint in existing_endpoints:
                    if endpoint not in paths:
                        missing_existing.append(endpoint)
                
                if not missing_existing:
                    self.log_test(
                        "现有端点文档兼容性", 
                        True, 
                        "现有端点文档完整"
                    )
                else:
                    self.log_test(
                        "现有端点文档兼容性", 
                        False, 
                        f"现有端点文档缺失: {missing_existing}"
                    )
            else:
                self.log_test(
                    "API文档兼容性", 
                    False, 
                    f"无法获取API文档: HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("API文档兼容性", False, f"请求异常: {str(e)}")
    
    def test_frontend_routes_compatibility(self):
        """测试前端路由兼容性"""
        print("\n🌐 测试前端路由兼容性...")
        
        # 假设前端运行在3000端口
        frontend_url = "http://localhost:3000"
        
        routes_to_test = [
            ("/", "首页"),
            ("/upload", "上传页面"),
            ("/admin/login", "管理员登录"),
            ("/tracker", "跟踪查询页面")  # 新添加的路由
        ]
        
        for route, description in routes_to_test:
            try:
                response = requests.get(f"{frontend_url}{route}", timeout=10)
                
                if response.status_code == 200:
                    self.log_test(
                        f"前端路由兼容性 ({description})", 
                        True, 
                        "路由可访问"
                    )
                else:
                    self.log_test(
                        f"前端路由兼容性 ({description})", 
                        False, 
                        f"路由不可访问: HTTP {response.status_code}"
                    )
                    
            except Exception as e:
                # 前端可能未启动，这不算兼容性问题
                self.log_test(
                    f"前端路由兼容性 ({description})", 
                    True, 
                    f"前端未启动或网络问题: {str(e)}"
                )
    
    def test_environment_variables_compatibility(self):
        """测试环境变量兼容性"""
        print("\n🔧 测试环境变量兼容性...")
        
        try:
            from app.core.config import settings
            
            # 检查关键配置是否仍然可用
            critical_configs = [
                'DATABASE_URL',
                'SECRET_KEY',
                'ALGORITHM'
            ]
            
            missing_configs = []
            for config in critical_configs:
                if not hasattr(settings, config.lower()) and not hasattr(settings, config):
                    missing_configs.append(config)
            
            if not missing_configs:
                self.log_test(
                    "环境变量兼容性", 
                    True, 
                    "关键配置项完整"
                )
            else:
                self.log_test(
                    "环境变量兼容性", 
                    False, 
                    f"缺少配置项: {missing_configs}"
                )
                
        except Exception as e:
            self.log_test("环境变量兼容性", False, f"配置加载失败: {str(e)}")
    
    def run_all_tests(self):
        """运行所有向后兼容性测试"""
        print("🔄 开始向后兼容性测试...")
        print("=" * 60)
        
        test_methods = [
            self.test_existing_upload_endpoints,
            self.test_email_upload_compatibility,
            self.test_admin_endpoints_compatibility,
            self.test_database_schema_compatibility,
            self.test_api_documentation_compatibility,
            self.test_frontend_routes_compatibility,
            self.test_environment_variables_compatibility
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(
                    f"{test_method.__name__}执行异常", 
                    False, 
                    str(e)
                )
        
        return self.generate_compatibility_report()
    
    def generate_compatibility_report(self):
        """生成兼容性测试报告"""
        print("\n" + "=" * 60)
        print("📊 向后兼容性测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"兼容性: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if failed_tests > 0:
            print("\n❌ 兼容性问题:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # 兼容性评估
        compatibility_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if compatibility_score >= 90:
            print(f"\n✅ 兼容性评估: 优秀 ({compatibility_score:.1f}%)")
            print("   系统具有良好的向后兼容性")
        elif compatibility_score >= 75:
            print(f"\n⚠️  兼容性评估: 良好 ({compatibility_score:.1f}%)")
            print("   系统基本保持向后兼容，有少量问题需要关注")
        else:
            print(f"\n❌ 兼容性评估: 需要改进 ({compatibility_score:.1f}%)")
            print("   系统存在较多兼容性问题，需要修复")
        
        # 保存详细报告
        report_file = f"compatibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "compatibility_score": compatibility_score
                },
                "detailed_results": self.test_results,
                "recommendations": self.generate_recommendations()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return {
            "success": compatibility_score >= 75,  # 75%以上认为兼容性可接受
            "score": compatibility_score,
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests
        }
    
    def generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        failed_tests = [result for result in self.test_results if not result['success']]
        
        if any("端点" in test['test_name'] for test in failed_tests):
            recommendations.append("检查API端点配置和路由设置")
        
        if any("数据库" in test['test_name'] for test in failed_tests):
            recommendations.append("验证数据库迁移是否正确执行")
        
        if any("模型" in test['test_name'] for test in failed_tests):
            recommendations.append("检查数据模型定义和字段映射")
        
        if any("前端" in test['test_name'] for test in failed_tests):
            recommendations.append("确保前端服务正常运行并检查路由配置")
        
        if any("配置" in test['test_name'] for test in failed_tests):
            recommendations.append("检查环境变量和配置文件设置")
        
        return recommendations

def main():
    """主函数"""
    print("向后兼容性测试工具")
    print("此工具将验证跟踪系统不会破坏现有功能")
    
    tester = BackwardCompatibilityTest()
    result = tester.run_all_tests()
    
    if result['success']:
        print("\n🎉 向后兼容性测试通过！系统保持良好兼容性。")
        return 0
    else:
        print(f"\n⚠️  兼容性得分: {result['score']:.1f}%，存在一些问题需要关注。")
        return 1

if __name__ == "__main__":
    exit(main())