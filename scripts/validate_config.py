#!/usr/bin/env python3
"""
配置文件验证脚本
"""

import json
from pathlib import Path

import yaml
from loguru import logger


def validate_schema_file(schema_path: str) -> bool:
    """验证Schema配置文件"""
    logger.info(f"验证Schema文件: {schema_path}")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        # 检查必需字段
        required_fields = ["version", "description", "entities", "relations"]
        for field in required_fields:
            if field not in schema:
                logger.error(f"❌ Schema缺少必需字段: {field}")
                return False

        # 验证实体定义
        entities = schema.get("entities", {})
        if not entities:
            logger.error("❌ Schema中没有定义实体")
            return False

        for entity_name, entity_config in entities.items():
            if "properties" not in entity_config:
                logger.warning(f"⚠️ 实体 {entity_name} 没有定义属性")

            properties = entity_config.get("properties", {})
            for prop_name, prop_config in properties.items():
                if "type" not in prop_config:
                    logger.error(f"❌ 实体 {entity_name} 的属性 {prop_name} 缺少类型定义")
                    return False

        # 验证关系定义
        relations = schema.get("relations", {})
        if not relations:
            logger.error("❌ Schema中没有定义关系")
            return False

        for relation_name, relation_config in relations.items():
            required_rel_fields = ["source", "target"]
            for field in required_rel_fields:
                if field not in relation_config:
                    logger.error(f"❌ 关系 {relation_name} 缺少必需字段: {field}")
                    return False

            # 检查源和目标实体是否在实体定义中
            source = relation_config["source"]
            target = relation_config["target"]

            if source not in entities:
                logger.error(f"❌ 关系 {relation_name} 的源实体 {source} 未在实体中定义")
                return False

            if target not in entities:
                logger.error(f"❌ 关系 {relation_name} 的目标实体 {target} 未在实体中定义")
                return False

        logger.info("✅ Schema文件验证通过")
        logger.info(f"📊 定义了 {len(entities)} 个实体类型")
        logger.info(f"📊 定义了 {len(relations)} 个关系类型")

        return True

    except yaml.YAMLError as e:
        logger.error(f"❌ Schema文件YAML格式错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Schema文件验证失败: {e}")
        return False


def validate_config_file(config_path: str) -> bool:
    """验证配置文件"""
    logger.info(f"验证配置文件: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 检查必需的配置节
        required_sections = ["app", "server", "neo4j", "ollama", "document"]
        for section in required_sections:
            if section not in config:
                logger.error(f"❌ 配置文件缺少必需节: {section}")
                return False

        # 验证应用配置
        app_config = config.get("app", {})
        if "name" not in app_config:
            logger.error("❌ 应用配置缺少名称")
            return False

        # 验证服务器配置
        server_config = config.get("server", {})
        required_server_fields = ["host", "port"]
        for field in required_server_fields:
            if field not in server_config:
                logger.error(f"❌ 服务器配置缺少字段: {field}")
                return False

        # 验证Neo4j配置
        neo4j_config = config.get("neo4j", {})
        required_neo4j_fields = ["uri", "username", "password"]
        for field in required_neo4j_fields:
            if field not in neo4j_config:
                logger.error(f"❌ Neo4j配置缺少字段: {field}")
                return False

        # 验证Ollama配置
        ollama_config = config.get("ollama", {})
        required_ollama_fields = ["base_url", "model"]
        for field in required_ollama_fields:
            if field not in ollama_config:
                logger.error(f"❌ Ollama配置缺少字段: {field}")
                return False

        logger.info("✅ 配置文件验证通过")
        return True

    except yaml.YAMLError as e:
        logger.error(f"❌ 配置文件YAML格式错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 配置文件验证失败: {e}")
        return False


def validate_prompts_directory(prompts_dir: str) -> bool:
    """验证提示词目录"""
    logger.info(f"验证提示词目录: {prompts_dir}")

    prompts_path = Path(prompts_dir)
    if not prompts_path.exists():
        logger.error(f"❌ 提示词目录不存在: {prompts_dir}")
        return False

    # 检查必需的提示词文件
    required_prompts = [
        "entity_extraction.txt",
        "relation_extraction.txt",
        "document_summary.txt",
        "graph_query.txt",
    ]

    for prompt_file in required_prompts:
        prompt_path = prompts_path / prompt_file
        if not prompt_path.exists():
            logger.error(f"❌ 缺少提示词文件: {prompt_file}")
            return False

        # 检查文件是否为空
        if prompt_path.stat().st_size == 0:
            logger.error(f"❌ 提示词文件为空: {prompt_file}")
            return False

    logger.info("✅ 提示词目录验证通过")
    logger.info(f"📊 找到 {len(required_prompts)} 个提示词文件")

    return True


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("配置文件验证")
    logger.info("=" * 50)

    all_valid = True

    # 验证Schema文件
    if not validate_schema_file("config/schema.yaml"):
        all_valid = False

    logger.info("")

    # 验证配置文件
    if not validate_config_file("config/config.yaml"):
        all_valid = False

    logger.info("")

    # 验证提示词目录
    if not validate_prompts_directory("config/prompts"):
        all_valid = False

    logger.info("")

    if all_valid:
        logger.info("✅ 所有配置文件验证通过！")
    else:
        logger.error("❌ 配置文件验证失败！")

    return all_valid


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
