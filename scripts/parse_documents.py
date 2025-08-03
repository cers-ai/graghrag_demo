#!/usr/bin/env python3
"""
文档解析命令行工具
"""

import sys
import argparse
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.services.document_parser import DocumentParser


def parse_single_file(args):
    """解析单个文件"""
    logger.info("=" * 50)
    logger.info("文档解析工具 - 单文件解析")
    logger.info("=" * 50)

    file_path = Path(args.file)

    if not file_path.exists():
        logger.error(f"文件不存在: {file_path}")
        return False

    doc_parser = DocumentParser()

    if not doc_parser.is_supported(file_path):
        logger.error(f"不支持的文件格式: {file_path.suffix}")
        return False

    logger.info(f"正在解析文件: {file_path}")

    result = doc_parser.parse_document(file_path)

    if result.success:
        logger.info("✅ 解析成功！")
        logger.info(f"📄 文件: {result.file_name}")
        logger.info(f"📝 标题: {result.title}")
        logger.info(f"📊 内容长度: {len(result.content)} 字符")

        if args.verbose:
            logger.info(f"\n📋 元数据:")
            for key, value in result.metadata.items():
                logger.info(f"  {key}: {value}")

        if args.show_content:
            logger.info(f"\n📖 内容预览:")
            content_preview = result.content[:500]
            if len(result.content) > 500:
                content_preview += "..."
            logger.info(content_preview)

        # 保存到文件
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {result.title}\n\n")
                f.write(f"**文件**: {result.file_name}\n")
                f.write(f"**解析时间**: {result.parse_time}\n\n")
                f.write("## 内容\n\n")
                f.write(result.content)
                f.write("\n\n## 元数据\n\n")
                for key, value in result.metadata.items():
                    f.write(f"- **{key}**: {value}\n")

            logger.info(f"💾 结果已保存到: {output_path}")

        return True
    else:
        logger.error(f"❌ 解析失败: {result.error_message}")
        return False


def parse_directory(args):
    """解析目录中的所有文档"""
    logger.info("=" * 50)
    logger.info("文档解析工具 - 目录解析")
    logger.info("=" * 50)

    directory = Path(args.directory)

    if not directory.exists():
        logger.error(f"目录不存在: {directory}")
        return False

    if not directory.is_dir():
        logger.error(f"路径不是目录: {directory}")
        return False

    doc_parser = DocumentParser()

    # 查找支持的文件
    supported_files = []
    for file_path in directory.rglob('*'):
        if file_path.is_file() and doc_parser.is_supported(file_path):
            supported_files.append(file_path)

    if not supported_files:
        logger.warning(f"目录中没有找到支持的文档文件: {directory}")
        return False

    logger.info(f"找到 {len(supported_files)} 个支持的文档文件")

    # 批量解析
    results = doc_parser.batch_parse(supported_files)

    # 统计结果
    success_count = sum(1 for r in results if r.success)
    failed_count = len(results) - success_count

    logger.info(f"\n📊 解析结果:")
    logger.info(f"  总文件数: {len(results)}")
    logger.info(f"  成功解析: {success_count}")
    logger.info(f"  解析失败: {failed_count}")

    # 显示详细结果
    if args.verbose:
        logger.info(f"\n📋 详细结果:")
        for i, result in enumerate(results, 1):
            status = "✅" if result.success else "❌"
            logger.info(f"  {i:2d}. {status} {result.file_name}")
            if not result.success:
                logger.info(f"      错误: {result.error_message}")
            elif args.show_content:
                content_preview = result.content[:100].replace('\n', ' ')
                if len(result.content) > 100:
                    content_preview += "..."
                logger.info(f"      内容: {content_preview}")

    # 保存结果
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        for result in results:
            if result.success:
                output_file = output_dir / f"{Path(result.file_name).stem}.md"

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {result.title}\n\n")
                    f.write(f"**原文件**: {result.file_name}\n")
                    f.write(f"**解析时间**: {result.parse_time}\n\n")
                    f.write("## 内容\n\n")
                    f.write(result.content)
                    f.write("\n\n## 元数据\n\n")
                    for key, value in result.metadata.items():
                        f.write(f"- **{key}**: {value}\n")

        logger.info(f"💾 解析结果已保存到: {output_dir}")

    return success_count > 0


def test_document_parser():
    """测试解析器功能"""
    logger.info("=" * 50)
    logger.info("文档解析工具 - 功能测试")
    logger.info("=" * 50)

    doc_parser = DocumentParser()

    # 测试支持的格式
    logger.info("📋 支持的文件格式:")
    for fmt in doc_parser.supported_formats.keys():
        logger.info(f"  {fmt}")

    # 创建测试目录
    test_dir = Path("./test_parse")
    test_dir.mkdir(exist_ok=True)

    # 创建测试文本文件
    test_txt = test_dir / "test.txt"
    with open(test_txt, 'w', encoding='utf-8') as f:
        f.write("测试文档标题\n\n这是测试内容。\n\n重要说明:\n这是重要信息。")

    logger.info(f"\n创建测试文件: {test_txt}")

    # 测试解析
    result = doc_parser.parse_document(test_txt)

    if result.success:
        logger.info("✅ 测试解析成功！")
        logger.info(f"标题: {result.title}")
        logger.info(f"内容长度: {len(result.content)} 字符")
        logger.info(f"内容预览: {result.content[:100]}...")
    else:
        logger.error(f"❌ 测试解析失败: {result.error_message}")

    # 清理测试文件
    test_txt.unlink()
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()

    return result.success


def main():
    """主函数"""
    arg_parser = argparse.ArgumentParser(description="文档解析工具")

    subparsers = arg_parser.add_subparsers(dest="mode", help="运行模式")

    # 单文件解析
    file_parser = subparsers.add_parser("file", help="解析单个文件")
    file_parser.add_argument("file", help="要解析的文件路径")
    file_parser.add_argument("-o", "--output", help="输出文件路径")
    file_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    file_parser.add_argument("-c", "--show-content", action="store_true", help="显示内容预览")

    # 目录解析
    dir_parser = subparsers.add_parser("dir", help="解析目录中的所有文档")
    dir_parser.add_argument("directory", help="要解析的目录路径")
    dir_parser.add_argument("-o", "--output", help="输出目录路径")
    dir_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    dir_parser.add_argument("-c", "--show-content", action="store_true", help="显示内容预览")

    # 测试模式
    test_parser = subparsers.add_parser("test", help="测试解析器功能")

    args = arg_parser.parse_args()

    if not args.mode:
        arg_parser.print_help()
        return

    try:
        logger.info(f"运行模式: {args.mode}")

        if args.mode == "file":
            success = parse_single_file(args)
        elif args.mode == "dir":
            success = parse_directory(args)
        elif args.mode == "test":
            success = test_document_parser()
        else:
            logger.error(f"未知模式: {args.mode}")
            success = False

        sys.exit(0 if success else 1)

    except Exception as e:
        import traceback
        logger.error(f"执行失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
