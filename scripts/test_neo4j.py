#!/usr/bin/env python3
"""
Neo4j数据库连接测试脚本
"""

import sys
import time

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable


def test_neo4j_connection():
    """测试Neo4j数据库连接"""

    # 连接配置
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "graghrag123"

    print("正在测试Neo4j数据库连接...")
    print(f"URI: {uri}")
    print(f"用户名: {username}")

    try:
        # 创建驱动
        driver = GraphDatabase.driver(uri, auth=(username, password))

        # 测试连接
        with driver.session() as session:
            # 执行简单查询
            result = session.run("RETURN 'Hello, Neo4j!' AS message")
            record = result.single()
            message = record["message"]

            print(f"✅ 连接成功！收到消息: {message}")

            # 获取数据库信息
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(
                    f"📊 数据库信息: {record['name']} {record['versions'][0]} ({record['edition']})"
                )

            # 创建测试节点
            print("\n正在创建测试节点...")
            session.run(
                """
                MERGE (test:TestNode {name: 'GraphRAG测试节点', created: datetime()})
                RETURN test
            """
            )

            # 查询测试节点
            result = session.run(
                "MATCH (test:TestNode) RETURN test.name AS name, test.created AS created"
            )
            for record in result:
                print(f"🔍 找到测试节点: {record['name']} (创建时间: {record['created']})")

            # 清理测试节点
            session.run("MATCH (test:TestNode) DELETE test")
            print("🧹 测试节点已清理")

        driver.close()
        print("\n✅ Neo4j数据库连接测试成功！")
        return True

    except ServiceUnavailable as e:
        print(f"❌ 无法连接到Neo4j数据库: {e}")
        print("请确保Neo4j服务正在运行")
        return False

    except AuthError as e:
        print(f"❌ 认证失败: {e}")
        print("请检查用户名和密码")
        return False

    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


def wait_for_neo4j(max_retries=10, delay=5):
    """等待Neo4j服务启动"""
    print(f"等待Neo4j服务启动（最多等待 {max_retries * delay} 秒）...")

    for i in range(max_retries):
        try:
            if test_neo4j_connection():
                return True
        except Exception:
            pass

        if i < max_retries - 1:
            print(f"第 {i + 1} 次尝试失败，{delay} 秒后重试...")
            time.sleep(delay)

    print("❌ Neo4j服务启动超时")
    return False


if __name__ == "__main__":
    print("=" * 50)
    print("Neo4j数据库连接测试")
    print("=" * 50)

    success = test_neo4j_connection()

    if not success:
        print("\n尝试等待服务启动...")
        success = wait_for_neo4j()

    sys.exit(0 if success else 1)
