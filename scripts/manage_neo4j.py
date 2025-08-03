#!/usr/bin/env python3
"""
Neo4j数据库管理工具
"""

import sys
import json
import argparse
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.services.neo4j_manager import Neo4jManager
from backend.app.services.information_extractor import ExtractedEntity, ExtractedRelation, ExtractionResult
from datetime import datetime


def test_connection(args):
    """测试Neo4j连接"""
    logger.info("=" * 50)
    logger.info("Neo4j连接测试")
    logger.info("=" * 50)

    manager = Neo4jManager(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )

    success = manager.connect()

    if success:
        logger.info("✅ Neo4j连接测试成功！")

        # 执行简单查询测试
        result = manager.execute_query("RETURN 'Hello Neo4j!' as message")
        if result.success:
            logger.info(f"📝 查询测试: {result.records[0]['message']}")
            logger.info(f"⏱️ 执行时间: {result.execution_time:.3f}秒")

        manager.disconnect()
        return True
    else:
        logger.error("❌ Neo4j连接测试失败！")
        return False


def show_stats(args):
    """显示图谱统计信息"""
    logger.info("=" * 50)
    logger.info("图谱统计信息")
    logger.info("=" * 50)

    manager = Neo4jManager(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )

    if not manager.connect():
        logger.error("❌ 无法连接到Neo4j数据库")
        return False

    try:
        stats = manager.get_graph_stats()

        if stats:
            logger.info(f"📊 图谱统计信息:")
            logger.info(f"  总节点数: {stats.total_nodes}")
            logger.info(f"  总关系数: {stats.total_relationships}")
            logger.info(f"  更新时间: {stats.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

            if stats.node_types:
                logger.info(f"\n📋 节点类型分布:")
                for node_type, count in stats.node_types.items():
                    logger.info(f"  {node_type}: {count}")

            if stats.relationship_types:
                logger.info(f"\n📋 关系类型分布:")
                for rel_type, count in stats.relationship_types.items():
                    logger.info(f"  {rel_type}: {count}")

            return True
        else:
            logger.error("❌ 获取统计信息失败")
            return False

    finally:
        manager.disconnect()


def search_entities(args):
    """搜索实体"""
    logger.info("=" * 50)
    logger.info("实体搜索")
    logger.info("=" * 50)

    manager = Neo4jManager(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )

    if not manager.connect():
        logger.error("❌ 无法连接到Neo4j数据库")
        return False

    try:
        entities = manager.search_entities(
            entity_type=args.entity_type,
            name_pattern=args.name_pattern,
            limit=args.limit
        )

        if entities:
            logger.info(f"🔍 找到 {len(entities)} 个实体:")

            for i, entity in enumerate(entities, 1):
                labels = entity.get('_labels', [])
                name = entity.get('name', 'Unknown')

                logger.info(f"  {i:2d}. {':'.join(labels)} - {name}")

                if args.verbose:
                    for key, value in entity.items():
                        if key not in ['_labels', 'name']:
                            logger.info(f"      {key}: {value}")
        else:
            logger.info("🔍 未找到匹配的实体")

        return True

    finally:
        manager.disconnect()


def execute_query(args):
    """执行自定义查询"""
    logger.info("=" * 50)
    logger.info("执行Cypher查询")
    logger.info("=" * 50)

    manager = Neo4jManager(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )

    if not manager.connect():
        logger.error("❌ 无法连接到Neo4j数据库")
        return False

    try:
        logger.info(f"📝 执行查询: {args.query}")

        result = manager.execute_query(args.query)

        if result.success:
            logger.info(f"✅ 查询执行成功")
            logger.info(f"📊 返回记录数: {len(result.records)}")
            logger.info(f"⏱️ 执行时间: {result.execution_time:.3f}秒")

            if result.records and args.verbose:
                logger.info(f"\n📋 查询结果:")
                for i, record in enumerate(result.records[:10], 1):  # 只显示前10条
                    logger.info(f"  {i:2d}. {record}")

                if len(result.records) > 10:
                    logger.info(f"  ... 还有 {len(result.records) - 10} 条记录")

            # 保存结果
            if args.output:
                output_data = {
                    'query': args.query,
                    'success': result.success,
                    'records': result.records,
                    'summary': result.summary,
                    'execution_time': result.execution_time
                }

                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)

                logger.info(f"💾 结果已保存到: {args.output}")

            return True
        else:
            logger.error(f"❌ 查询执行失败: {result.error_message}")
            return False

    finally:
        manager.disconnect()


def import_test_data(args):
    """导入测试数据"""
    logger.info("=" * 50)
    logger.info("导入测试数据")
    logger.info("=" * 50)

    manager = Neo4jManager(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )

    if not manager.connect():
        logger.error("❌ 无法连接到Neo4j数据库")
        return False

    try:
        # 创建测试实体
        test_entities = [
            ExtractedEntity(
                type="Person",
                name="张三",
                properties={"title": "项目经理", "department": "技术部"},
                confidence=0.9
            ),
            ExtractedEntity(
                type="Person",
                name="李四",
                properties={"title": "开发工程师", "department": "技术部"},
                confidence=0.8
            ),
            ExtractedEntity(
                type="Organization",
                name="ABC科技公司",
                properties={"type": "科技公司", "address": "北京市"},
                confidence=0.95
            ),
            ExtractedEntity(
                type="Project",
                name="知识图谱项目",
                properties={"status": "进行中", "description": "构建企业知识图谱"},
                confidence=0.85
            )
        ]

        # 创建测试关系
        test_relations = [
            ExtractedRelation(
                type="WORKS_FOR",
                source="张三",
                target="ABC科技公司",
                properties={"position": "项目经理"},
                confidence=0.9
            ),
            ExtractedRelation(
                type="WORKS_FOR",
                source="李四",
                target="ABC科技公司",
                properties={"position": "开发工程师"},
                confidence=0.8
            ),
            ExtractedRelation(
                type="MANAGES",
                source="张三",
                target="知识图谱项目",
                properties={},
                confidence=0.85
            ),
            ExtractedRelation(
                type="PARTICIPATES_IN",
                source="李四",
                target="知识图谱项目",
                properties={},
                confidence=0.8
            ),
            ExtractedRelation(
                type="BELONGS_TO",
                source="知识图谱项目",
                target="ABC科技公司",
                properties={},
                confidence=0.9
            )
        ]

        # 创建抽取结果
        extraction_result = ExtractionResult(
            entities=test_entities,
            relations=test_relations,
            source_text="测试数据",
            extraction_time=datetime.now(),
            success=True
        )

        # 导入数据
        logger.info("🔄 开始导入测试数据...")
        entity_count, relation_count = manager.import_extraction_result(extraction_result)

        logger.info(f"✅ 测试数据导入完成!")
        logger.info(f"  导入实体: {entity_count}/{len(test_entities)}")
        logger.info(f"  导入关系: {relation_count}/{len(test_relations)}")

        return True

    finally:
        manager.disconnect()


def clear_database(args):
    """清空数据库"""
    logger.info("=" * 50)
    logger.info("清空数据库")
    logger.info("=" * 50)

    if not args.confirm:
        logger.warning("⚠️ 此操作将删除所有数据，请使用 --confirm 参数确认")
        return False

    manager = Neo4jManager(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )

    if not manager.connect():
        logger.error("❌ 无法连接到Neo4j数据库")
        return False

    try:
        success = manager.clear_database()

        if success:
            logger.info("✅ 数据库已清空")
            return True
        else:
            logger.error("❌ 清空数据库失败")
            return False

    finally:
        manager.disconnect()


def main():
    """主函数"""
    arg_parser = argparse.ArgumentParser(description="Neo4j数据库管理工具")

    # 全局参数
    arg_parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j连接URI")
    arg_parser.add_argument("--username", default="neo4j", help="用户名")
    arg_parser.add_argument("--password", default="graghrag123", help="密码")
    arg_parser.add_argument("--database", default="neo4j", help="数据库名称")

    subparsers = arg_parser.add_subparsers(dest="command", help="命令")

    # 连接测试
    subparsers.add_parser("connect", help="测试Neo4j连接")

    # 统计信息
    subparsers.add_parser("stats", help="显示图谱统计信息")

    # 搜索实体
    search_parser = subparsers.add_parser("search", help="搜索实体")
    search_parser.add_argument("--entity-type", help="实体类型")
    search_parser.add_argument("--name-pattern", help="名称模式")
    search_parser.add_argument("--limit", type=int, default=100, help="结果限制")
    search_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    # 执行查询
    query_parser = subparsers.add_parser("query", help="执行Cypher查询")
    query_parser.add_argument("query", help="Cypher查询语句")
    query_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细结果")
    query_parser.add_argument("-o", "--output", help="输出文件路径")

    # 导入测试数据
    subparsers.add_parser("import-test", help="导入测试数据")

    # 清空数据库
    clear_parser = subparsers.add_parser("clear", help="清空数据库")
    clear_parser.add_argument("--confirm", action="store_true", help="确认清空操作")

    args = arg_parser.parse_args()

    if not args.command:
        arg_parser.print_help()
        return

    try:
        if args.command == "connect":
            success = test_connection(args)
        elif args.command == "stats":
            success = show_stats(args)
        elif args.command == "search":
            success = search_entities(args)
        elif args.command == "query":
            success = execute_query(args)
        elif args.command == "import-test":
            success = import_test_data(args)
        elif args.command == "clear":
            success = clear_database(args)
        else:
            logger.error(f"未知命令: {args.command}")
            success = False

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
