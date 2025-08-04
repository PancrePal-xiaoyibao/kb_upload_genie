"""
测试运行脚本
提供便捷的测试运行方式
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """运行测试"""
    
    # 基础pytest命令
    cmd = ["python", "-m", "pytest"]
    
    # 添加测试路径
    test_dir = Path(__file__).parent / "tests"
    cmd.append(str(test_dir))
    
    # 根据测试类型添加标记
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    
    # 添加详细输出
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # 添加覆盖率报告
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    # 添加其他有用的选项
    cmd.extend([
        "--tb=short",  # 简短的错误回溯
        "--strict-markers",  # 严格标记模式
        "--disable-warnings",  # 禁用警告
        "-x"  # 遇到第一个失败就停止
    ])
    
    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 50)
    
    # 执行测试
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行邮件上传功能测试")
    
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "integration", "performance", "slow", "fast"],
        default="all",
        help="测试类型 (默认: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="安装测试依赖"
    )
    
    args = parser.parse_args()
    
    # 安装测试依赖
    if args.install_deps:
        print("安装测试依赖...")
        deps = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "httpx>=0.24.0",
            "aiofiles>=23.0.0"
        ]
        
        for dep in deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                print(f"✓ 已安装: {dep}")
            except subprocess.CalledProcessError:
                print(f"✗ 安装失败: {dep}")
        
        print("依赖安装完成")
        return 0
    
    # 运行测试
    return run_tests(args.type, args.verbose, args.coverage)


if __name__ == "__main__":
    sys.exit(main())