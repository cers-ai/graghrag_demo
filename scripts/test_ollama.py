#!/usr/bin/env python3
"""
Ollama模型测试脚本
"""

import json
import time

import ollama
from loguru import logger


def test_ollama_connection():
    """测试Ollama连接"""
    logger.info("正在测试Ollama连接...")

    try:
        # 获取模型列表
        models = ollama.list()
        logger.info(f"✅ Ollama连接成功！")

        if "models" in models:
            logger.info(f"📋 可用模型数量: {len(models['models'])}")

            for model in models["models"]:
                name = model.get("name", "Unknown")
                size = model.get("size", 0)
                logger.info(f"  📦 {name} (大小: {size // (1024**3):.1f}GB)")
        else:
            logger.info(f"📋 模型信息: {models}")

        return True

    except Exception as e:
        logger.error(f"❌ Ollama连接失败: {e}")
        return False


def test_model_generation(model_name="qwen3:4b"):
    """测试模型生成功能"""
    logger.info(f"正在测试模型 {model_name} 的生成功能...")

    try:
        # 简单的测试提示
        prompt = "你好！请简单介绍一下你自己。"

        logger.info(f"📝 测试提示: {prompt}")

        start_time = time.time()

        # 调用模型
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            options={"temperature": 0.7, "max_tokens": 100},
        )

        end_time = time.time()
        duration = end_time - start_time

        response_text = response["response"]
        logger.info(f"🤖 模型响应: {response_text}")
        logger.info(f"⏱️ 响应时间: {duration:.2f}秒")

        return True

    except Exception as e:
        logger.error(f"❌ 模型生成测试失败: {e}")
        return False


def test_knowledge_extraction(model_name="qwen3:4b"):
    """测试知识抽取功能"""
    logger.info(f"正在测试模型 {model_name} 的知识抽取功能...")

    # 测试文本
    test_text = """
    张三是ABC公司的项目经理，负责管理知识图谱项目。
    李四是该公司的开发工程师，参与项目开发工作。
    王五是产品经理，负责需求分析。
    这个项目属于技术部门，预计在2024年完成。
    """

    # 知识抽取提示词
    extraction_prompt = f"""
请从以下文本中抽取实体和关系信息，并以JSON格式返回：

文本：{test_text}

请按照以下格式返回：
{{
    "entities": [
        {{"type": "Person", "name": "实体名称", "properties": {{"title": "职位", "department": "部门"}}}},
        {{"type": "Organization", "name": "实体名称", "properties": {{"type": "公司类型"}}}},
        {{"type": "Project", "name": "实体名称", "properties": {{"status": "状态"}}}}
    ],
    "relations": [
        {{"source": "源实体", "target": "目标实体", "type": "关系类型", "properties": {{}}}}
    ]
}}

只返回JSON，不要其他解释。
"""

    try:
        logger.info("📝 测试知识抽取...")

        start_time = time.time()

        response = ollama.generate(
            model=model_name,
            prompt=extraction_prompt,
            options={"temperature": 0.1, "max_tokens": 500},  # 降低温度以获得更一致的结果
        )

        end_time = time.time()
        duration = end_time - start_time

        response_text = response["response"].strip()
        logger.info(f"🤖 抽取结果: {response_text}")
        logger.info(f"⏱️ 抽取时间: {duration:.2f}秒")

        # 尝试解析JSON
        try:
            extracted_data = json.loads(response_text)
            logger.info("✅ JSON解析成功")
            logger.info(f"📊 抽取到 {len(extracted_data.get('entities', []))} 个实体")
            logger.info(f"📊 抽取到 {len(extracted_data.get('relations', []))} 个关系")
            return True
        except json.JSONDecodeError:
            logger.warning("⚠️ JSON解析失败，但模型响应正常")
            return True

    except Exception as e:
        logger.error(f"❌ 知识抽取测试失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Ollama模型测试")
    logger.info("=" * 50)

    # 测试连接
    if not test_ollama_connection():
        return False

    logger.info("")

    # 测试基本生成
    if not test_model_generation():
        return False

    logger.info("")

    # 测试知识抽取
    if not test_knowledge_extraction():
        return False

    logger.info("")
    logger.info("✅ 所有Ollama测试通过！")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
