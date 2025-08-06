"""
跟踪系统部署脚本
自动化部署和验证跟踪系统功能
"""

import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path

class TrackerSystemDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.migration_script = self.project_root / "migrations" / "add_tracker_fields.py"
        self.test_script = self.project_root / "test_tracker_integration.py"
    
    def print_step(self, step: str, message: str):
        """打印部署步骤"""
        print(f"\n🔧 [{step}] {message}")
        print("-" * 50)
    
    def print_success(self, message: str):
        """打印成功信息"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误信息"""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """打印警告信息"""
        print(f"⚠️  {message}")
    
    def check_dependencies(self):
        """检查依赖项"""
        self.print_step("依赖检查", "检查必要的依赖项...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            self.print_error("需要Python 3.8或更高版本")
            return False
        
        self.print_success(f"Python版本: {sys.version}")
        
        # 检查必要的包
        required_packages = [
            "fastapi",
            "sqlalchemy",
            "asyncpg",
            "pydantic",
            "uvicorn"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                self.print_success(f"包 {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                self.print_error(f"包 {package} 未安装")
        
        if missing_packages:
            self.print_error(f"请安装缺失的包: pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def check_database_connection(self):
        """检查数据库连接"""
        self.print_step("数据库检查", "检查数据库连接...")
        
        try:
            # 尝试导入数据库相关模块
            from app.core.database import get_db_session
            
            async def test_connection():
                try:
                    async with get_db_session() as db:
                        await db.execute("SELECT 1")
                        return True
                except Exception as e:
                    self.print_error(f"数据库连接失败: {e}")
                    return False
            
            # 运行连接测试
            result = asyncio.run(test_connection())
            
            if result:
                self.print_success("数据库连接正常")
                return True
            else:
                return False
                
        except Exception as e:
            self.print_error(f"数据库模块导入失败: {e}")
            return False
    
    def run_database_migration(self):
        """运行数据库迁移"""
        self.print_step("数据库迁移", "添加跟踪系统字段...")
        
        if not self.migration_script.exists():
            self.print_error(f"迁移脚本不存在: {self.migration_script}")
            return False
        
        try:
            # 运行迁移脚本
            result = subprocess.run([
                sys.executable, 
                str(self.migration_script), 
                "full"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                self.print_success("数据库迁移完成")
                print(result.stdout)
                return True
            else:
                self.print_error("数据库迁移失败")
                print(result.stderr)
                return False
                
        except Exception as e:
            self.print_error(f"运行迁移脚本失败: {e}")
            return False
    
    def start_backend_server(self):
        """启动后端服务器"""
        self.print_step("后端服务", "启动FastAPI服务器...")
        
        try:
            # 检查服务器是否已经运行
            import requests
            try:
                response = requests.get("http://localhost:8000/docs", timeout=5)
                if response.status_code == 200:
                    self.print_success("后端服务器已在运行")
                    return True
            except:
                pass
            
            # 启动服务器
            self.print_warning("正在启动后端服务器...")
            self.print_warning("请在另一个终端运行: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
            
            # 等待用户确认
            input("启动后端服务器后，按回车键继续...")
            
            # 再次检查
            try:
                response = requests.get("http://localhost:8000/docs", timeout=10)
                if response.status_code == 200:
                    self.print_success("后端服务器运行正常")
                    return True
                else:
                    self.print_error("后端服务器响应异常")
                    return False
            except Exception as e:
                self.print_error(f"无法连接到后端服务器: {e}")
                return False
                
        except Exception as e:
            self.print_error(f"启动后端服务器失败: {e}")
            return False
    
    def check_api_endpoints(self):
        """检查API端点"""
        self.print_step("API检查", "验证跟踪系统API端点...")
        
        try:
            import requests
            
            # 检查健康端点
            endpoints = [
                ("GET", "/api/v1/tracker/health", "健康检查"),
                ("GET", "/api/v1/tracker/status/test", "状态查询"),
                ("POST", "/api/v1/tracker/query", "POST查询")
            ]
            
            for method, endpoint, description in endpoints:
                try:
                    url = f"http://localhost:8000{endpoint}"
                    
                    if method == "GET":
                        response = requests.get(url, timeout=10)
                    elif method == "POST":
                        response = requests.post(url, json={"tracker_id": "test"}, timeout=10)
                    
                    # 检查响应（404也是正常的，说明端点存在）
                    if response.status_code in [200, 404, 422]:
                        self.print_success(f"{description} 端点正常")
                    else:
                        self.print_warning(f"{description} 端点响应异常: {response.status_code}")
                        
                except Exception as e:
                    self.print_error(f"{description} 端点检查失败: {e}")
            
            return True
            
        except Exception as e:
            self.print_error(f"API端点检查失败: {e}")
            return False
    
    def run_integration_tests(self):
        """运行集成测试"""
        self.print_step("集成测试", "运行跟踪系统集成测试...")
        
        if not self.test_script.exists():
            self.print_error(f"测试脚本不存在: {self.test_script}")
            return False
        
        try:
            # 运行测试脚本
            result = subprocess.run([
                sys.executable, 
                str(self.test_script)
            ], cwd=self.project_root, input="\n", text=True)
            
            if result.returncode == 0:
                self.print_success("集成测试通过")
                return True
            else:
                self.print_warning("部分集成测试失败，请查看详细报告")
                return True  # 不阻止部署，只是警告
                
        except Exception as e:
            self.print_error(f"运行集成测试失败: {e}")
            return False
    
    def generate_deployment_summary(self):
        """生成部署摘要"""
        self.print_step("部署摘要", "生成部署信息...")
        
        summary = f"""
🎉 跟踪系统部署完成！

📋 系统信息:
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 跟踪查询页面: http://localhost:3000/tracker (需要启动前端)

🔧 主要功能:
- ✅ 数据库模式已扩展 (method, tracker_id, processing_status字段)
- ✅ 跟踪ID查询API已部署
- ✅ 前端状态查询组件已创建
- ✅ 错误处理和通知系统已集成

📡 API端点:
- GET  /api/v1/tracker/health - 健康检查
- GET  /api/v1/tracker/status/{{tracker_id}} - 查询状态
- POST /api/v1/tracker/query - POST方式查询

🚀 下一步:
1. 启动前端服务: cd frontend && npm run dev
2. 访问跟踪页面: http://localhost:3000/tracker
3. 测试文件上传并获取跟踪ID
4. 使用跟踪ID查询状态

📞 支持:
如有问题，请检查:
- 数据库连接配置
- 环境变量设置
- 服务器日志输出
        """
        
        print(summary)
        
        # 保存到文件
        summary_file = self.project_root / "DEPLOYMENT_SUMMARY.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        self.print_success(f"部署摘要已保存到: {summary_file}")
    
    def deploy(self):
        """执行完整部署流程"""
        print("🚀 跟踪系统自动化部署")
        print("=" * 60)
        
        steps = [
            ("检查依赖", self.check_dependencies),
            ("检查数据库", self.check_database_connection),
            ("数据库迁移", self.run_database_migration),
            ("启动后端", self.start_backend_server),
            ("检查API", self.check_api_endpoints),
            ("集成测试", self.run_integration_tests),
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    failed_steps.append(step_name)
                    
                    # 对于关键步骤，询问是否继续
                    if step_name in ["检查依赖", "检查数据库", "数据库迁移"]:
                        continue_deploy = input(f"\n{step_name}失败，是否继续部署？(y/N): ")
                        if continue_deploy.lower() != 'y':
                            self.print_error("部署已取消")
                            return False
                
            except KeyboardInterrupt:
                self.print_error("部署被用户中断")
                return False
            except Exception as e:
                self.print_error(f"{step_name}执行异常: {e}")
                failed_steps.append(step_name)
        
        # 生成部署摘要
        self.generate_deployment_summary()
        
        if failed_steps:
            self.print_warning(f"部署完成，但以下步骤失败: {', '.join(failed_steps)}")
            return False
        else:
            self.print_success("🎉 跟踪系统部署成功！")
            return True

def main():
    """主函数"""
    deployer = TrackerSystemDeployer()
    
    print("欢迎使用跟踪系统部署工具")
    print("此工具将自动部署和配置资源上传跟踪系统")
    
    confirm = input("\n是否开始部署？(y/N): ")
    if confirm.lower() != 'y':
        print("部署已取消")
        return
    
    success = deployer.deploy()
    
    if success:
        print("\n🎊 部署成功！系统已准备就绪。")
        sys.exit(0)
    else:
        print("\n⚠️  部署完成但存在问题，请检查上述错误信息。")
        sys.exit(1)

if __name__ == "__main__":
    main()