#!/usr/bin/env python3
"""
前后端集成测试
"""

import sys
import time
import subprocess
import requests
from pathlib import Path

def test_backend_api():
    """测试后端API"""
    print("🔍 测试后端API...")

    try:
        # 启动后端服务
        print("启动后端API服务...")
        backend_process = subprocess.Popen([
            sys.executable, "run_api.py"
        ], cwd=Path.cwd())

        # 等待服务启动
        time.sleep(10)

        # 测试健康检查
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ 后端API服务正常运行")
                data = response.json()
                print(f"服务状态: {data['status']}")
                return True
            else:
                print(f"❌ 后端API响应异常: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 无法连接到后端API: {e}")
            return False
        finally:
            # 停止后端服务
            backend_process.terminate()
            backend_process.wait()

    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
        return False

def test_frontend():
    """测试前端服务"""
    print("🔍 测试前端服务...")

    try:
        # 检查前端是否运行
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
            return True
        else:
            print(f"❌ 前端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到前端服务: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始前后端集成测试")
    print("=" * 50)

    # 测试前端
    frontend_ok = test_frontend()

    # 测试后端
    backend_ok = test_backend_api()

    print("=" * 50)
    print("📊 测试结果:")
    print(f"前端服务: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    print(f"后端API: {'✅ 正常' if backend_ok else '❌ 异常'}")

    if frontend_ok and backend_ok:
        print("🎉 前后端集成测试通过！")
        print("\n📍 访问地址:")
        print("  前端: http://localhost:5173")
        print("  后端API: http://localhost:8000")
        print("  API文档: http://localhost:8000/docs")
    else:
        print("⚠️ 部分服务异常，请检查配置")

if __name__ == "__main__":
    main()
