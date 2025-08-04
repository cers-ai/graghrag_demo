#!/usr/bin/env python3
"""
系统验证脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


def verify_modules():
    """验证核心功能模块"""
    print("🔍 验证核心功能模块...")

    results = []

    # 检查文档扫描模块
    try:
        from backend.app.services.document_scanner import DocumentScanner

        scanner = DocumentScanner(scan_directories=[])
        results.append(("文档扫描模块", True, None))
    except Exception as e:
        results.append(("文档扫描模块", False, str(e)))

    # 检查文档解析模块
    try:
        from backend.app.services.document_parser import DocumentParser

        parser = DocumentParser()
        results.append(("文档解析模块", True, None))
    except Exception as e:
        results.append(("文档解析模块", False, str(e)))

    # 检查Schema管理模块
    try:
        from backend.app.services.schema_manager import SchemaManager

        schema_mgr = SchemaManager("config/schema.yaml")
        schema_mgr.load_schema()
        results.append(("Schema管理模块", True, None))
    except Exception as e:
        results.append(("Schema管理模块", False, str(e)))

    # 检查Ollama客户端模块
    try:
        from backend.app.services.ollama_client import OllamaClient

        ollama_client = OllamaClient()
        results.append(("Ollama客户端模块", True, None))
    except Exception as e:
        results.append(("Ollama客户端模块", False, str(e)))

    # 检查信息抽取模块
    try:
        from backend.app.services.information_extractor import InformationExtractor

        # 需要先创建依赖对象
        schema_mgr = SchemaManager("config/schema.yaml")
        schema_mgr.load_schema()
        ollama_client = OllamaClient()
        extractor = InformationExtractor(schema_mgr, ollama_client)
        results.append(("信息抽取模块", True, None))
    except Exception as e:
        results.append(("信息抽取模块", False, str(e)))

    # 检查Neo4j管理模块
    try:
        from backend.app.services.neo4j_manager import Neo4jManager

        neo4j_mgr = Neo4jManager()
        results.append(("Neo4j管理模块", True, None))
    except Exception as e:
        results.append(("Neo4j管理模块", False, str(e)))

    return results


def verify_frontend():
    """验证前端服务"""
    print("🔍 验证前端服务...")

    try:
        import requests

        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def verify_backend():
    """验证后端API服务"""
    print("🔍 验证后端API服务...")

    try:
        import requests

        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def main():
    """主函数"""
    print("🚀 开始系统验证")
    print("=" * 50)

    # 验证核心模块
    module_results = verify_modules()

    print("\n📋 核心模块验证结果:")
    for module_name, success, error in module_results:
        status = "✅" if success else "❌"
        print(f"  {status} {module_name}")
        if not success and error:
            print(f"     错误: {error}")

    # 验证前端服务
    frontend_success, frontend_error = verify_frontend()
    print(f'\n🎨 前端服务: {"✅ 正常" if frontend_success else "❌ 异常"}')
    if not frontend_success:
        print(f"     错误: {frontend_error}")

    # 验证后端服务
    backend_success, backend_result = verify_backend()
    print(f'🔧 后端API: {"✅ 正常" if backend_success else "❌ 异常"}')
    if not backend_success:
        print(f"     错误: {backend_result}")
    elif isinstance(backend_result, dict):
        print(f'     状态: {backend_result.get("status", "unknown")}')

    # 统计结果
    total_modules = len(module_results)
    success_modules = sum(1 for _, success, _ in module_results if success)

    print("\n" + "=" * 50)
    print("📊 验证总结:")
    print(f"  核心模块: {success_modules}/{total_modules} 正常")
    print(f'  前端服务: {"正常" if frontend_success else "异常"}')
    print(f'  后端API: {"正常" if backend_success else "异常"}')

    if success_modules == total_modules and frontend_success:
        print("\n🎉 系统验证通过！所有核心功能正常运行。")
        if not backend_success:
            print("⚠️  注意: 后端API需要Neo4j和Ollama服务支持才能完全正常工作。")
    else:
        print("\n⚠️  系统验证发现问题，请检查上述错误信息。")


if __name__ == "__main__":
    main()
