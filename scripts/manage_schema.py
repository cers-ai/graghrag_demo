#!/usr/bin/env python3
"""
Schema管理命令行工具
"""

import sys
import json
import argparse
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.services.schema_manager import SchemaManager, SchemaValidationError


def validate_schema(args):
    """验证Schema文件"""
    logger.info("=" * 50)
    logger.info("Schema验证工具")
    logger.info("=" * 50)

    schema_file = args.schema_file

    if not Path(schema_file).exists():
        logger.error(f"Schema文件不存在: {schema_file}")
        return False

    try:
        manager = SchemaManager(schema_file)
        schema = manager.load_schema()

        logger.info("✅ Schema验证成功！")
        logger.info(f"📋 版本: {schema.version}")
        logger.info(f"📝 描述: {schema.description}")
        logger.info(f"📊 实体类型: {len(schema.entities)} 个")
        logger.info(f"📊 关系类型: {len(schema.relations)} 个")

        if args.verbose:
            logger.info(f"\n📋 实体列表:")
            for entity_name, entity in schema.entities.items():
                logger.info(f"  {entity_name}: {entity.description}")
                if args.show_properties:
                    for prop_name, prop_config in entity.properties.items():
                        required = "必需" if prop_name in entity.required_properties else "可选"
                        logger.info(f"    - {prop_name} ({prop_config['type']}) - {required}")

            logger.info(f"\n📋 关系列表:")
            for relation_name, relation in schema.relations.items():
                logger.info(f"  {relation_name}: {relation.source} -> {relation.target}")
                logger.info(f"    描述: {relation.description}")
                if args.show_properties and relation.properties:
                    for prop_name, prop_config in relation.properties.items():
                        logger.info(f"    - {prop_name} ({prop_config['type']})")

        return True

    except SchemaValidationError as e:
        logger.error(f"❌ Schema验证失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 验证过程出错: {e}")
        return False


def show_schema_info(args):
    """显示Schema信息"""
    logger.info("=" * 50)
    logger.info("Schema信息查看")
    logger.info("=" * 50)

    try:
        manager = SchemaManager(args.schema_file)
        schema = manager.load_schema()

        summary = manager.get_schema_summary()

        logger.info(f"📋 Schema摘要:")
        logger.info(f"  文件路径: {summary['file_path']}")
        logger.info(f"  版本: {summary['version']}")
        logger.info(f"  描述: {summary['description']}")
        logger.info(f"  加载时间: {summary['load_time']}")
        logger.info(f"  实体数量: {summary['entities_count']}")
        logger.info(f"  关系数量: {summary['relations_count']}")

        if args.entity:
            entity_schema = manager.get_entity_schema(args.entity)
            if entity_schema:
                logger.info(f"\n📋 实体详情: {args.entity}")
                logger.info(f"  描述: {entity_schema.description}")
                logger.info(f"  属性数量: {len(entity_schema.properties)}")
                logger.info(f"  必需属性: {list(entity_schema.required_properties)}")

                logger.info(f"  属性列表:")
                for prop_name, prop_config in entity_schema.properties.items():
                    required = "✓" if prop_name in entity_schema.required_properties else "○"
                    logger.info(f"    {required} {prop_name} ({prop_config['type']}): {prop_config.get('description', '')}")
            else:
                logger.error(f"实体不存在: {args.entity}")

        if args.relation:
            relation_schema = manager.get_relation_schema(args.relation)
            if relation_schema:
                logger.info(f"\n📋 关系详情: {args.relation}")
                logger.info(f"  描述: {relation_schema.description}")
                logger.info(f"  源实体: {relation_schema.source}")
                logger.info(f"  目标实体: {relation_schema.target}")
                logger.info(f"  属性数量: {len(relation_schema.properties)}")

                if relation_schema.properties:
                    logger.info(f"  属性列表:")
                    for prop_name, prop_config in relation_schema.properties.items():
                        logger.info(f"    - {prop_name} ({prop_config['type']}): {prop_config.get('description', '')}")
            else:
                logger.error(f"关系不存在: {args.relation}")

        return True

    except Exception as e:
        logger.error(f"❌ 获取Schema信息失败: {e}")
        return False


def export_schema(args):
    """导出Schema"""
    logger.info("=" * 50)
    logger.info("Schema导出工具")
    logger.info("=" * 50)

    try:
        manager = SchemaManager(args.schema_file)
        manager.load_schema()

        if args.format == 'json':
            schema_data = manager.export_schema_json()

            output_file = args.output or "schema.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Schema已导出为JSON格式: {output_file}")

        elif args.format == 'summary':
            summary = manager.get_schema_summary()

            output_file = args.output or "schema_summary.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"✅ Schema摘要已导出: {output_file}")

        return True

    except Exception as e:
        logger.error(f"❌ 导出Schema失败: {e}")
        return False


def test_schema_data(args):
    """测试Schema数据验证"""
    logger.info("=" * 50)
    logger.info("Schema数据验证测试")
    logger.info("=" * 50)

    try:
        manager = SchemaManager(args.schema_file)
        manager.load_schema()

        # 测试实体数据验证
        test_entity_data = {
            'Person': {
                'name': '张三',
                'age': 30
            },
            'Organization': {
                'name': 'ABC公司'
            }
        }

        logger.info("📋 测试实体数据验证:")
        for entity_name, data in test_entity_data.items():
            errors = manager.validate_entity_data(entity_name, data)
            if errors:
                logger.error(f"  ❌ {entity_name}: {errors}")
            else:
                logger.info(f"  ✅ {entity_name}: 验证通过")

        # 测试关系数据验证
        test_relation_data = {
            'WORKS_FOR': {
                'position': '软件工程师'
            }
        }

        logger.info(f"\n📋 测试关系数据验证:")
        for relation_name, data in test_relation_data.items():
            errors = manager.validate_relation_data(relation_name, data)
            if errors:
                logger.error(f"  ❌ {relation_name}: {errors}")
            else:
                logger.info(f"  ✅ {relation_name}: 验证通过")

        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False


def main():
    """主函数"""
    arg_parser = argparse.ArgumentParser(description="Schema管理工具")

    subparsers = arg_parser.add_subparsers(dest="command", help="命令")

    # 验证命令
    validate_parser = subparsers.add_parser("validate", help="验证Schema文件")
    validate_parser.add_argument("schema_file", help="Schema文件路径")
    validate_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    validate_parser.add_argument("-p", "--show-properties", action="store_true", help="显示属性详情")

    # 信息命令
    info_parser = subparsers.add_parser("info", help="显示Schema信息")
    info_parser.add_argument("schema_file", help="Schema文件路径")
    info_parser.add_argument("-e", "--entity", help="显示指定实体的详细信息")
    info_parser.add_argument("-r", "--relation", help="显示指定关系的详细信息")

    # 导出命令
    export_parser = subparsers.add_parser("export", help="导出Schema")
    export_parser.add_argument("schema_file", help="Schema文件路径")
    export_parser.add_argument("-f", "--format", choices=['json', 'summary'],
                              default='json', help="导出格式")
    export_parser.add_argument("-o", "--output", help="输出文件路径")

    # 测试命令
    test_parser = subparsers.add_parser("test", help="测试Schema数据验证")
    test_parser.add_argument("schema_file", help="Schema文件路径")

    args = arg_parser.parse_args()

    if not args.command:
        arg_parser.print_help()
        return

    try:
        if args.command == "validate":
            success = validate_schema(args)
        elif args.command == "info":
            success = show_schema_info(args)
        elif args.command == "export":
            success = export_schema(args)
        elif args.command == "test":
            success = test_schema_data(args)
        else:
            logger.error(f"未知命令: {args.command}")
            success = False

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
