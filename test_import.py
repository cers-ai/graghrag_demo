#!/usr/bin/env python3
"""
测试导入
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试各个模块的导入"""
    print("🔍 测试模块导入...")

    try:
        from backend.app.services.document_scanner import DocumentScanner
        print('✅ DocumentScanner导入成功')
    except Exception as e:
        print(f'❌ DocumentScanner导入失败: {e}')

    try:
        from backend.app.services.document_parser import DocumentParser
        print('✅ DocumentParser导入成功')
    except Exception as e:
        print(f'❌ DocumentParser导入失败: {e}')

    try:
        from backend.app.services.schema_manager import SchemaManager
        print('✅ SchemaManager导入成功')
    except Exception as e:
        print(f'❌ SchemaManager导入失败: {e}')

    try:
        from backend.app.services.ollama_client import OllamaClient
        print('✅ OllamaClient导入成功')
    except Exception as e:
        print(f'❌ OllamaClient导入失败: {e}')

    try:
        from backend.app.services.information_extractor import InformationExtractor
        print('✅ InformationExtractor导入成功')
    except Exception as e:
        print(f'❌ InformationExtractor导入失败: {e}')

    try:
        from backend.app.services.neo4j_manager import Neo4jManager
        print('✅ Neo4jManager导入成功')
    except Exception as e:
        print(f'❌ Neo4jManager导入失败: {e}')

    try:
        from backend.app.main import app
        print('✅ FastAPI app导入成功')
    except Exception as e:
        print(f'❌ FastAPI app导入失败: {e}')

if __name__ == "__main__":
    test_imports()
