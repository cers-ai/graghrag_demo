#!/usr/bin/env python3
"""
Ollama客户端测试工具
"""

import sys
import json
import argparse
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.services.ollama_client import OllamaClient


def test_connection(args):
    """测试Ollama连接"""
    logger.info("=" * 50)
    logger.info("Ollama连接测试")
    logger.info("=" * 50)

    client = OllamaClient(
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout
    )

    success = client.test_connection()

    if success:
        logger.info("✅ Ollama连接测试成功！")

        # 显示客户端信息
        info = client.get_client_info()
        logger.info(f"\n📋 客户端信息:")
        logger.info(f"  模型: {info['model']}")
        logger.info(f"  服务地址: {info['base_url']}")
        logger.info(f"  超时时间: {info['timeout']}秒")
        logger.info(f"  可用模型: {info['available_models']}")
        logger.info(f"  模板数量: {info['templates_count']}")

        return True
    else:
        logger.error("❌ Ollama连接测试失败！")
        return False


def test_generation(args):
    """测试文本生成"""
    logger.info("=" * 50)
    logger.info("文本生成测试")
    logger.info("=" * 50)

    client = OllamaClient(
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout
    )

    prompt = args.prompt or "你好！请简单介绍一下你自己。"

    logger.info(f"📝 测试提示词: {prompt}")

    options = {}
    if args.temperature is not None:
        options['temperature'] = args.temperature
    if args.max_tokens is not None:
        options['num_predict'] = args.max_tokens

    response = client.generate(prompt, options=options)

    if response.success:
        logger.info("✅ 文本生成成功！")
        logger.info(f"🤖 模型响应: {response.content}")
        logger.info(f"⏱️ 响应时间: {response.response_time:.2f}秒")

        if args.verbose:
            logger.info(f"\n📊 详细信息:")
            logger.info(f"  模型: {response.model}")
            logger.info(f"  提示词长度: {len(response.prompt)} 字符")
            logger.info(f"  响应长度: {len(response.content)} 字符")
            if response.metadata:
                logger.info(f"  元数据: {response.metadata}")

        return True
    else:
        logger.error(f"❌ 文本生成失败: {response.error_message}")
        return False


def test_templates(args):
    """测试提示词模板"""
    logger.info("=" * 50)
    logger.info("提示词模板测试")
    logger.info("=" * 50)

    client = OllamaClient(
        model=args.model,
        base_url=args.base_url,
        prompts_dir=args.prompts_dir
    )

    templates = client.get_prompt_templates()

    if not templates:
        logger.warning("没有找到提示词模板")
        return False

    logger.info(f"📋 找到 {len(templates)} 个模板:")

    for template in templates:
        logger.info(f"  📄 {template.name} ({template.category})")
        logger.info(f"     描述: {template.description}")
        logger.info(f"     变量: {template.variables}")

        if args.verbose:
            logger.info(f"     模板内容: {template.template[:100]}...")

    # 测试模板使用
    if args.test_template:
        template_name = args.test_template
        template = client.get_template(template_name)

        if not template:
            logger.error(f"模板不存在: {template_name}")
            return False

        logger.info(f"\n🧪 测试模板: {template_name}")

        # 使用示例变量
        test_variables = {}
        for var in template.variables:
            if var == 'text':
                test_variables[var] = "张三是ABC公司的项目经理。"
            elif var == 'entity_type':
                test_variables[var] = "Person"
            elif var == 'schema':
                test_variables[var] = "Person(name, title), Organization(name)"
            elif var == 'question':
                test_variables[var] = "查找所有人员"
            else:
                test_variables[var] = f"示例{var}"

        logger.info(f"📝 测试变量: {test_variables}")

        response = client.generate_with_template(
            template_name=template_name,
            variables=test_variables
        )

        if response.success:
            logger.info("✅ 模板生成成功！")
            logger.info(f"🤖 生成结果: {response.content}")
            logger.info(f"⏱️ 响应时间: {response.response_time:.2f}秒")
        else:
            logger.error(f"❌ 模板生成失败: {response.error_message}")
            return False

    return True


def list_models(args):
    """列出可用模型"""
    logger.info("=" * 50)
    logger.info("可用模型列表")
    logger.info("=" * 50)

    client = OllamaClient(base_url=args.base_url)

    models = client.get_available_models()

    if models:
        logger.info(f"📋 找到 {len(models)} 个可用模型:")
        for i, model in enumerate(models, 1):
            current = " (当前)" if model == args.model else ""
            logger.info(f"  {i:2d}. {model}{current}")
    else:
        logger.warning("没有找到可用模型")
        return False

    return True


def interactive_test(args):
    """交互式测试"""
    logger.info("=" * 50)
    logger.info("Ollama交互式测试")
    logger.info("=" * 50)
    logger.info("输入 'quit' 或 'exit' 退出")

    client = OllamaClient(
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout
    )

    # 测试连接
    if not client.test_connection():
        logger.error("连接失败，无法进行交互式测试")
        return False

    while True:
        try:
            prompt = input("\n请输入提示词: ").strip()

            if prompt.lower() in ['quit', 'exit', '退出']:
                logger.info("退出交互式测试")
                break

            if not prompt:
                continue

            logger.info("正在生成响应...")

            response = client.generate(prompt)

            if response.success:
                print(f"\n🤖 响应: {response.content}")
                print(f"⏱️ 时间: {response.response_time:.2f}秒")
            else:
                print(f"\n❌ 错误: {response.error_message}")

        except KeyboardInterrupt:
            logger.info("\n收到中断信号，退出交互式测试")
            break
        except EOFError:
            logger.info("\n输入结束，退出交互式测试")
            break

    return True


def main():
    """主函数"""
    arg_parser = argparse.ArgumentParser(description="Ollama客户端测试工具")

    # 全局参数
    arg_parser.add_argument("-m", "--model", default="qwen3:4b", help="使用的模型")
    arg_parser.add_argument("-u", "--base-url", default="http://localhost:11434", help="Ollama服务地址")
    arg_parser.add_argument("-t", "--timeout", type=int, default=300, help="超时时间（秒）")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    subparsers = arg_parser.add_subparsers(dest="command", help="命令")

    # 连接测试
    subparsers.add_parser("connect", help="测试Ollama连接")

    # 文本生成测试
    gen_parser = subparsers.add_parser("generate", help="测试文本生成")
    gen_parser.add_argument("-p", "--prompt", help="测试提示词")
    gen_parser.add_argument("--temperature", type=float, help="生成温度")
    gen_parser.add_argument("--max-tokens", type=int, help="最大生成长度")

    # 模板测试
    template_parser = subparsers.add_parser("templates", help="测试提示词模板")
    template_parser.add_argument("--prompts-dir", default="config/prompts", help="提示词目录")
    template_parser.add_argument("--test-template", help="测试指定模板")

    # 模型列表
    subparsers.add_parser("models", help="列出可用模型")

    # 交互式测试
    subparsers.add_parser("interactive", help="交互式测试")

    args = arg_parser.parse_args()

    if not args.command:
        arg_parser.print_help()
        return

    try:
        if args.command == "connect":
            success = test_connection(args)
        elif args.command == "generate":
            success = test_generation(args)
        elif args.command == "templates":
            success = test_templates(args)
        elif args.command == "models":
            success = list_models(args)
        elif args.command == "interactive":
            success = interactive_test(args)
        else:
            logger.error(f"未知命令: {args.command}")
            success = False

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
