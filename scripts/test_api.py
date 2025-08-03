#!/usr/bin/env python3
"""
API测试脚本
"""

import requests
import json
import time
import argparse
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查接口"""
    print("=" * 50)
    print("测试健康检查接口")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/health")

        if response.status_code == 200:
            data = response.json()
            print("✅ 健康检查成功")
            print(f"状态: {data['status']}")

            for service, status in data['services'].items():
                if status['status'] == 'healthy':
                    print(f"  ✅ {service}: 正常")
                else:
                    print(f"  ❌ {service}: 异常 - {status.get('error', '')}")

            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_schema():
    """测试Schema接口"""
    print("=" * 50)
    print("测试Schema接口")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/schema")

        if response.status_code == 200:
            data = response.json()
            schema = data['schema']

            print("✅ Schema获取成功")
            print(f"版本: {schema['version']}")
            print(f"描述: {schema['description']}")
            print(f"实体类型: {len(schema['entities'])} 个")
            print(f"关系类型: {len(schema['relations'])} 个")

            print("\n实体类型:")
            for name, entity in schema['entities'].items():
                print(f"  - {name}: {entity['description']}")

            print("\n关系类型:")
            for name, relation in schema['relations'].items():
                print(f"  - {name}: {relation['source']} -> {relation['target']}")

            return True
        else:
            print(f"❌ Schema获取失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_extraction():
    """测试信息抽取接口"""
    print("=" * 50)
    print("测试信息抽取接口")
    print("=" * 50)

    test_text = """
    张三是ABC科技公司的项目经理，负责管理知识图谱项目。
    李四是该公司的高级开发工程师，参与项目的技术开发工作。
    王五是产品经理，负责需求分析和产品设计。
    这个项目属于技术研发部门，预计在2024年6月完成。
    """

    try:
        payload = {
            "text": test_text,
            "chunk_size": 2000,
            "chunk_overlap": 200
        }

        print(f"📝 测试文本: {test_text.strip()}")
        print("🔍 开始抽取...")

        response = requests.post(f"{BASE_URL}/extraction/extract", json=payload)

        if response.status_code == 200:
            data = response.json()

            if data['success']:
                print("✅ 信息抽取成功")
                print(f"实体数量: {len(data['entities'])}")
                print(f"关系数量: {len(data['relations'])}")

                print("\n📋 抽取的实体:")
                for i, entity in enumerate(data['entities'], 1):
                    print(f"  {i}. {entity['type']}: {entity['name']}")
                    if entity['properties']:
                        for key, value in entity['properties'].items():
                            print(f"     {key}: {value}")

                print("\n📋 抽取的关系:")
                for i, relation in enumerate(data['relations'], 1):
                    print(f"  {i}. {relation['source']} -[{relation['type']}]-> {relation['target']}")

                return True
            else:
                print(f"❌ 抽取失败: {data['error_message']}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_extract_and_import():
    """测试抽取并导入接口"""
    print("=" * 50)
    print("测试抽取并导入接口")
    print("=" * 50)

    test_text = """
    赵六是XYZ公司的技术总监，管理着整个技术团队。
    孙七是该公司的架构师，负责系统架构设计。
    他们正在开发一个新的AI平台项目。
    """

    try:
        payload = {
            "text": test_text,
            "chunk_size": 2000,
            "chunk_overlap": 200
        }

        print(f"📝 测试文本: {test_text.strip()}")
        print("🔍 开始抽取并导入...")

        response = requests.post(f"{BASE_URL}/extraction/extract-and-import", json=payload)

        if response.status_code == 200:
            data = response.json()

            if data['success']:
                print("✅ 抽取并导入请求成功")
                print(f"消息: {data['message']}")
                print(f"实体数量: {data['entities_count']}")
                print(f"关系数量: {data['relations_count']}")

                # 等待后台处理
                print("⏳ 等待后台导入完成...")
                time.sleep(5)

                return True
            else:
                print(f"❌ 抽取失败: {data.get('error_message', '未知错误')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_graph_stats():
    """测试图谱统计接口"""
    print("=" * 50)
    print("测试图谱统计接口")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/graph/stats")

        if response.status_code == 200:
            data = response.json()

            if data['success']:
                stats = data['stats']
                print("✅ 图谱统计获取成功")
                print(f"总节点数: {stats['total_nodes']}")
                print(f"总关系数: {stats['total_relationships']}")
                print(f"更新时间: {stats['last_updated']}")

                print("\n节点类型分布:")
                for node_type, count in stats['node_types'].items():
                    print(f"  {node_type}: {count}")

                print("\n关系类型分布:")
                for rel_type, count in stats['relationship_types'].items():
                    print(f"  {rel_type}: {count}")

                return True
            else:
                print("❌ 获取统计信息失败")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_search():
    """测试实体搜索接口"""
    print("=" * 50)
    print("测试实体搜索接口")
    print("=" * 50)

    try:
        # 搜索Person类型的实体
        payload = {
            "entity_type": "Person",
            "limit": 10
        }

        response = requests.post(f"{BASE_URL}/graph/search", json=payload)

        if response.status_code == 200:
            data = response.json()

            if data['success']:
                print("✅ 实体搜索成功")
                print(f"找到 {data['count']} 个实体")

                for i, entity in enumerate(data['entities'], 1):
                    name = entity.get('name', 'Unknown')
                    labels = entity.get('_labels', [])
                    print(f"  {i}. {':'.join(labels)} - {name}")

                return True
            else:
                print("❌ 搜索失败")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_query():
    """测试图数据库查询接口"""
    print("=" * 50)
    print("测试图数据库查询接口")
    print("=" * 50)

    try:
        # 查询所有Person节点
        payload = {
            "query": "MATCH (p:Person) RETURN p.name as name, p.title as title LIMIT 5"
        }

        response = requests.post(f"{BASE_URL}/graph/query", json=payload)

        if response.status_code == 200:
            data = response.json()

            if data['success']:
                print("✅ 查询执行成功")
                print(f"返回记录数: {len(data['records'])}")
                print(f"执行时间: {data['execution_time']:.3f}秒")

                print("\n查询结果:")
                for i, record in enumerate(data['records'], 1):
                    name = record.get('name', 'Unknown')
                    title = record.get('title', 'Unknown')
                    print(f"  {i}. {name} - {title}")

                return True
            else:
                print(f"❌ 查询失败: {data['error_message']}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始API测试")

    tests = [
        ("健康检查", test_health),
        ("Schema接口", test_schema),
        ("信息抽取", test_extraction),
        ("抽取并导入", test_extract_and_import),
        ("图谱统计", test_graph_stats),
        ("实体搜索", test_search),
        ("图数据库查询", test_query)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))

            if success:
                print(f"✅ {test_name} 测试通过\n")
            else:
                print(f"❌ {test_name} 测试失败\n")

        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}\n")
            results.append((test_name, False))

        time.sleep(1)  # 间隔1秒

    # 输出测试总结
    print("=" * 50)
    print("测试总结")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("🎉 所有测试都通过了！")
    else:
        print("⚠️ 部分测试失败，请检查系统状态")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="API测试工具")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API基础URL")
    parser.add_argument("--test", choices=[
        "health", "schema", "extraction", "import", "stats", "search", "query", "all"
    ], default="all", help="要运行的测试")

    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.base_url

    if args.test == "all":
        run_all_tests()
    elif args.test == "health":
        test_health()
    elif args.test == "schema":
        test_schema()
    elif args.test == "extraction":
        test_extraction()
    elif args.test == "import":
        test_extract_and_import()
    elif args.test == "stats":
        test_graph_stats()
    elif args.test == "search":
        test_search()
    elif args.test == "query":
        test_query()

if __name__ == "__main__":
    main()
