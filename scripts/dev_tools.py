#!/usr/bin/env python3
"""
开发工具脚本
"""

import subprocess
import sys
from pathlib import Path

from loguru import logger


def run_command(command: str, cwd: str = None) -> bool:
    """运行命令"""
    try:
        logger.info(f"执行命令: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode == 0:
            logger.info("✅ 命令执行成功")
            if result.stdout:
                logger.info(f"输出: {result.stdout}")
            return True
        else:
            logger.error(f"❌ 命令执行失败 (返回码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ 命令执行异常: {e}")
        return False


def format_code():
    """格式化代码"""
    logger.info("正在格式化Python代码...")

    # 使用black格式化
    success = run_command("black backend/ scripts/")

    if success:
        logger.info("✅ 代码格式化完成")
    else:
        logger.error("❌ 代码格式化失败")

    return success


def lint_code():
    """代码检查"""
    logger.info("正在进行代码检查...")

    # 使用flake8检查
    success = run_command("flake8 backend/ scripts/")

    if success:
        logger.info("✅ 代码检查通过")
    else:
        logger.error("❌ 代码检查发现问题")

    return success


def run_tests():
    """运行测试"""
    logger.info("正在运行测试...")

    # 运行pytest
    success = run_command("pytest backend/tests/ -v")

    if success:
        logger.info("✅ 测试通过")
    else:
        logger.error("❌ 测试失败")

    return success


def check_dependencies():
    """检查依赖"""
    logger.info("正在检查依赖...")

    # 检查pip依赖
    success = run_command("pip check")

    if success:
        logger.info("✅ 依赖检查通过")
    else:
        logger.error("❌ 依赖检查发现问题")

    return success


def setup_pre_commit():
    """设置pre-commit钩子"""
    logger.info("正在设置pre-commit钩子...")

    # 安装pre-commit
    if not run_command("pip install pre-commit"):
        return False

    # 安装钩子
    success = run_command("pre-commit install")

    if success:
        logger.info("✅ pre-commit钩子设置完成")
    else:
        logger.error("❌ pre-commit钩子设置失败")

    return success


def create_logs_directory():
    """创建日志目录"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    logger.info(f"✅ 日志目录已创建: {logs_dir.absolute()}")


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开发环境工具")
    logger.info("=" * 50)

    if len(sys.argv) < 2:
        logger.info("使用方法:")
        logger.info("  python scripts/dev_tools.py format    # 格式化代码")
        logger.info("  python scripts/dev_tools.py lint      # 代码检查")
        logger.info("  python scripts/dev_tools.py test      # 运行测试")
        logger.info("  python scripts/dev_tools.py deps      # 检查依赖")
        logger.info("  python scripts/dev_tools.py setup     # 设置开发环境")
        logger.info("  python scripts/dev_tools.py all       # 运行所有检查")
        return

    command = sys.argv[1].lower()

    if command == "format":
        format_code()
    elif command == "lint":
        lint_code()
    elif command == "test":
        run_tests()
    elif command == "deps":
        check_dependencies()
    elif command == "setup":
        create_logs_directory()
        setup_pre_commit()
    elif command == "all":
        create_logs_directory()
        all_success = True
        all_success &= format_code()
        all_success &= lint_code()
        all_success &= check_dependencies()
        all_success &= run_tests()

        if all_success:
            logger.info("✅ 所有检查通过！")
        else:
            logger.error("❌ 部分检查失败！")
    else:
        logger.error(f"未知命令: {command}")


if __name__ == "__main__":
    main()
