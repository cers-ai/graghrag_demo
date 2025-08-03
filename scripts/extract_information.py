#!/usr/bin/env python3
"""
信息抽取命令行工具
"""

import sys
import json
import argparse
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.services.information_extractor import InformationExtractor
from backend.app.services.schema_manager import SchemaManager
from backend.app.services.ollama_client import OllamaClient
from backend.app.services.document_parser import DocumentParser


def extract_from_text(args):
    """从文本抽取信息"""
    logger.info("=" * 50)
    logger.info("文本信息抽取")
    logger.info("=" * 50)

    # 初始化组件
    schema_manager = SchemaManager(args.schema_file)
    ollama_client = OllamaClient(
        model=args.model,
        prompts_dir=args.prompts_dir
    )
    extractor = InformationExtractor(
        schema_manager=schema_manager,
        ollama_client=ollama_client,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )

    try:
        # 加载Schema
        schema_manager.load_schema()
        logger.info("✅ Schema加载成功")

        # 测试Ollama连接
        if not ollama_client.test_connection():
            logger.error("❌ Ollama连接失败")
            return False

        # 获取输入文本
        if args.text:
            text = args.text
        elif args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            logger.error("请提供文本内容或文件路径")
            return False

        logger.info(f"📝 输入文本长度: {len(text)} 字符")

        # 执行抽取
        logger.info("🔍 开始信息抽取...")
        result = extractor.extract_from_text(text)

        if result.success:
            logger.info("✅ 信息抽取成功！")

            # 显示结果
            logger.info(f"\n📊 抽取结果:")
            logger.info(f"  实体数量: {len(result.entities)}")
            logger.info(f"  关系数量: {len(result.relations)}")

            if args.verbose:
                logger.info(f"\n📋 实体列表:")
                for i, entity in enumerate(result.entities, 1):
                    logger.info(f"  {i:2d}. {entity.type}: {entity.name}")
                    if entity.properties:
                        for key, value in entity.properties.items():
                            logger.info(f"      {key}: {value}")
                    logger.info(f"      置信度: {entity.confidence:.2f}")

                logger.info(f"\n📋 关系列表:")
                for i, relation in enumerate(result.relations, 1):
                    logger.info(f"  {i:2d}. {relation.source} --[{relation.type}]--> {relation.target}")
                    if relation.properties:
                        for key, value in relation.properties.items():
                            logger.info(f"      {key}: {value}")
                    logger.info(f"      置信度: {relation.confidence:.2f}")

            # 显示统计信息
            stats = extractor.get_extraction_stats(result)
            logger.info(f"\n📈 统计信息:")
            logger.info(f"  实体类型分布: {stats['entity_types']}")
            logger.info(f"  关系类型分布: {stats['relation_types']}")
            if result.metadata:
                logger.info(f"  处理时间: {result.metadata.get('processing_time', 0):.2f}秒")
                logger.info(f"  文本块数: {result.metadata.get('chunks_count', 1)}")

            # 验证结果
            if args.validate:
                logger.info(f"\n🔍 验证抽取结果...")
                errors = extractor.validate_extraction_result(result)
                if errors:
                    logger.warning(f"发现 {len(errors)} 个验证错误:")
                    for error in errors:
                        logger.warning(f"  - {error}")
                else:
                    logger.info("✅ 验证通过，无错误")

            # 保存结果
            if args.output:
                output_data = {
                    'entities': [
                        {
                            'type': e.type,
                            'name': e.name,
                            'properties': e.properties,
                            'confidence': e.confidence
                        } for e in result.entities
                    ],
                    'relations': [
                        {
                            'type': r.type,
                            'source': r.source,
                            'target': r.target,
                            'properties': r.properties,
                            'confidence': r.confidence
                        } for r in result.relations
                    ],
                    'metadata': {
                        'source_text_length': len(result.source_text),
                        'extraction_time': result.extraction_time.isoformat(),
                        'stats': stats
                    }
                }

                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)

                logger.info(f"💾 结果已保存到: {args.output}")

            return True
        else:
            logger.error(f"❌ 信息抽取失败: {result.error_message}")
            return False

    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        return False


def extract_from_document(args):
    """从文档抽取信息"""
    logger.info("=" * 50)
    logger.info("文档信息抽取")
    logger.info("=" * 50)

    # 初始化组件
    schema_manager = SchemaManager(args.schema_file)
    ollama_client = OllamaClient(
        model=args.model,
        prompts_dir=args.prompts_dir
    )
    extractor = InformationExtractor(
        schema_manager=schema_manager,
        ollama_client=ollama_client,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    document_parser = DocumentParser()

    try:
        # 加载Schema
        schema_manager.load_schema()
        logger.info("✅ Schema加载成功")

        # 解析文档
        logger.info(f"📄 解析文档: {args.document}")
        parsed_doc = document_parser.parse_document(args.document)

        if not parsed_doc.success:
            logger.error(f"❌ 文档解析失败: {parsed_doc.error_message}")
            return False

        logger.info(f"✅ 文档解析成功，内容长度: {len(parsed_doc.content)} 字符")

        # 执行抽取
        logger.info("🔍 开始信息抽取...")
        result = extractor.extract_from_text(parsed_doc.content)

        if result.success:
            logger.info("✅ 信息抽取成功！")

            # 显示结果摘要
            logger.info(f"\n📊 抽取结果:")
            logger.info(f"  文档: {parsed_doc.title}")
            logger.info(f"  实体数量: {len(result.entities)}")
            logger.info(f"  关系数量: {len(result.relations)}")

            # 保存结果
            if args.output:
                output_data = {
                    'document_info': {
                        'file_path': parsed_doc.file_path,
                        'title': parsed_doc.title,
                        'file_type': parsed_doc.file_type,
                        'metadata': parsed_doc.metadata
                    },
                    'extraction_result': {
                        'entities': [
                            {
                                'type': e.type,
                                'name': e.name,
                                'properties': e.properties,
                                'confidence': e.confidence
                            } for e in result.entities
                        ],
                        'relations': [
                            {
                                'type': r.type,
                                'source': r.source,
                                'target': r.target,
                                'properties': r.properties,
                                'confidence': r.confidence
                            } for r in result.relations
                        ],
                        'extraction_time': result.extraction_time.isoformat(),
                        'stats': extractor.get_extraction_stats(result)
                    }
                }

                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)

                logger.info(f"💾 结果已保存到: {args.output}")

            return True
        else:
            logger.error(f"❌ 信息抽取失败: {result.error_message}")
            return False

    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        return False


def test_extraction(args):
    """测试信息抽取功能"""
    logger.info("=" * 50)
    logger.info("信息抽取功能测试")
    logger.info("=" * 50)

    # 测试文本
    test_text = """
    张三是ABC科技公司的项目经理，负责管理知识图谱项目。
    李四是该公司的高级开发工程师，参与项目的技术开发工作。
    王五是产品经理，负责需求分析和产品设计。
    这个项目属于技术研发部门，预计在2024年6月完成。
    """

    logger.info(f"📝 测试文本: {test_text.strip()}")

    # 使用测试文本进行抽取
    args.text = test_text
    args.file = None

    return extract_from_text(args)


def main():
    """主函数"""
    arg_parser = argparse.ArgumentParser(description="信息抽取工具")

    # 全局参数
    arg_parser.add_argument("-s", "--schema-file", default="config/schema.yaml", help="Schema文件路径")
    arg_parser.add_argument("-m", "--model", default="qwen3:4b", help="使用的模型")
    arg_parser.add_argument("-p", "--prompts-dir", default="config/prompts", help="提示词目录")
    arg_parser.add_argument("--chunk-size", type=int, default=2000, help="文本分块大小")
    arg_parser.add_argument("--chunk-overlap", type=int, default=200, help="分块重叠大小")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    arg_parser.add_argument("--validate", action="store_true", help="验证抽取结果")
    arg_parser.add_argument("-o", "--output", help="输出文件路径")

    subparsers = arg_parser.add_subparsers(dest="command", help="命令")

    # 文本抽取
    text_parser = subparsers.add_parser("text", help="从文本抽取信息")
    text_group = text_parser.add_mutually_exclusive_group(required=True)
    text_group.add_argument("-t", "--text", help="输入文本")
    text_group.add_argument("-f", "--file", help="文本文件路径")

    # 文档抽取
    doc_parser = subparsers.add_parser("document", help="从文档抽取信息")
    doc_parser.add_argument("document", help="文档文件路径")

    # 测试模式
    subparsers.add_parser("test", help="测试信息抽取功能")

    args = arg_parser.parse_args()

    if not args.command:
        arg_parser.print_help()
        return

    try:
        if args.command == "text":
            success = extract_from_text(args)
        elif args.command == "document":
            success = extract_from_document(args)
        elif args.command == "test":
            success = test_extraction(args)
        else:
            logger.error(f"未知命令: {args.command}")
            success = False

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
