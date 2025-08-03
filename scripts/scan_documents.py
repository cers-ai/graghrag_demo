#!/usr/bin/env python3
"""
文档扫描命令行工具
"""

import sys
import time
import argparse
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.services.document_scanner import DocumentScanner


def file_event_callback(file_path: str, event_type: str):
    """文件事件回调函数"""
    logger.info(f"📄 文件事件: {event_type} - {Path(file_path).name}")


def scan_mode(args):
    """扫描模式"""
    logger.info("=" * 50)
    logger.info("文档扫描工具 - 扫描模式")
    logger.info("=" * 50)

    scanner = DocumentScanner(
        scan_directories=args.directories,
        supported_formats=args.formats,
        callback=file_event_callback if args.verbose else None
    )

    # 执行扫描
    documents = scanner.scan_all_directories()

    # 显示结果
    logger.info(f"\n📊 扫描结果:")
    logger.info(f"  扫描目录: {len(args.directories)} 个")
    logger.info(f"  发现文档: {len(documents)} 个")

    if args.verbose:
        logger.info(f"\n📋 文档列表:")
        for i, doc in enumerate(documents, 1):
            logger.info(f"  {i:2d}. {doc.file_name}")
            logger.info(f"      路径: {doc.file_path}")
            logger.info(f"      大小: {doc.file_size:,} 字节")
            logger.info(f"      类型: {doc.file_type}")
            logger.info(f"      修改: {doc.modified_time}")
            logger.info("")

    # 显示统计信息
    stats = scanner.get_stats()
    logger.info(f"📈 统计信息:")
    logger.info(f"  总文件数: {stats['total_files']}")
    logger.info(f"  支持文件: {stats['supported_files']}")
    logger.info(f"  扫描时间: {stats['last_scan_time']}")


def monitor_mode(args):
    """监控模式"""
    logger.info("=" * 50)
    logger.info("文档扫描工具 - 监控模式")
    logger.info("=" * 50)

    scanner = DocumentScanner(
        scan_directories=args.directories,
        supported_formats=args.formats,
        callback=file_event_callback
    )

    # 初始扫描
    logger.info("执行初始扫描...")
    documents = scanner.scan_all_directories()
    logger.info(f"发现 {len(documents)} 个文档")

    # 开始监控
    logger.info("开始监控文件变化...")
    logger.info("按 Ctrl+C 停止监控")

    try:
        scanner.start_monitoring()

        while True:
            time.sleep(1)

            # 每10秒显示一次统计信息
            if int(time.time()) % 10 == 0:
                stats = scanner.get_stats()
                logger.info(f"📊 当前状态: 文档 {stats['current_documents']} 个, "
                           f"新增 {stats['new_files']} 个, "
                           f"修改 {stats['modified_files']} 个, "
                           f"删除 {stats['deleted_files']} 个")
                time.sleep(1)  # 避免重复显示

    except KeyboardInterrupt:
        logger.info("\n收到停止信号，正在停止监控...")

    finally:
        scanner.stop_monitoring()
        logger.info("监控已停止")


def test_mode(args):
    """测试模式"""
    logger.info("=" * 50)
    logger.info("文档扫描工具 - 测试模式")
    logger.info("=" * 50)

    # 创建测试目录和文件
    test_dir = Path("./test_documents")
    test_dir.mkdir(exist_ok=True)

    test_files = [
        "测试文档1.docx",
        "测试表格1.xlsx",
        "测试PDF1.pdf",
        "测试文本1.txt"
    ]

    logger.info("创建测试文件...")
    for file_name in test_files:
        test_file = test_dir / file_name
        test_file.touch()
        logger.info(f"  创建: {file_name}")

    # 测试扫描
    scanner = DocumentScanner(
        scan_directories=[str(test_dir)],
        supported_formats=[".docx", ".xlsx", ".pdf", ".txt"]
    )

    documents = scanner.scan_all_directories()
    logger.info(f"\n✅ 测试成功！发现 {len(documents)} 个测试文档")

    # 清理测试文件
    if not args.keep_test_files:
        logger.info("\n清理测试文件...")
        for file_name in test_files:
            test_file = test_dir / file_name
            if test_file.exists():
                test_file.unlink()
                logger.info(f"  删除: {file_name}")

        if test_dir.exists() and not any(test_dir.iterdir()):
            test_dir.rmdir()
            logger.info(f"  删除目录: {test_dir}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文档扫描工具")

    # 子命令
    subparsers = parser.add_subparsers(dest="mode", help="运行模式")

    # 扫描模式
    scan_parser = subparsers.add_parser("scan", help="扫描指定目录")
    scan_parser.add_argument("directories", nargs="+", help="要扫描的目录")
    scan_parser.add_argument("-f", "--formats", nargs="+",
                           default=[".docx", ".xlsx", ".pdf", ".txt"],
                           help="支持的文件格式")
    scan_parser.add_argument("-v", "--verbose", action="store_true",
                           help="显示详细信息")

    # 监控模式
    monitor_parser = subparsers.add_parser("monitor", help="监控目录变化")
    monitor_parser.add_argument("directories", nargs="+", help="要监控的目录")
    monitor_parser.add_argument("-f", "--formats", nargs="+",
                              default=[".docx", ".xlsx", ".pdf", ".txt"],
                              help="支持的文件格式")

    # 测试模式
    test_parser = subparsers.add_parser("test", help="运行测试")
    test_parser.add_argument("--keep-test-files", action="store_true",
                           help="保留测试文件")

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return

    try:
        if args.mode == "scan":
            scan_mode(args)
        elif args.mode == "monitor":
            monitor_mode(args)
        elif args.mode == "test":
            test_mode(args)

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
