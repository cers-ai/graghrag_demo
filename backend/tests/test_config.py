"""
配置相关测试
"""

from pathlib import Path

import pytest
import yaml


def test_config_file_exists():
    """测试配置文件是否存在"""
    config_path = Path("config/config.yaml")
    assert config_path.exists(), "配置文件不存在"


def test_config_file_valid():
    """测试配置文件格式是否正确"""
    config_path = Path("config/config.yaml")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 检查必需的配置节
    required_sections = ["app", "server", "neo4j", "ollama", "document"]
    for section in required_sections:
        assert section in config, f"配置文件缺少必需节: {section}"


def test_schema_file_exists():
    """测试Schema文件是否存在"""
    schema_path = Path("config/schema.yaml")
    assert schema_path.exists(), "Schema文件不存在"


def test_schema_file_valid():
    """测试Schema文件格式是否正确"""
    schema_path = Path("config/schema.yaml")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # 检查必需字段
    required_fields = ["version", "description", "entities", "relations"]
    for field in required_fields:
        assert field in schema, f"Schema缺少必需字段: {field}"

    # 检查实体定义
    entities = schema.get("entities", {})
    assert len(entities) > 0, "Schema中没有定义实体"

    # 检查关系定义
    relations = schema.get("relations", {})
    assert len(relations) > 0, "Schema中没有定义关系"


def test_prompts_directory_exists():
    """测试提示词目录是否存在"""
    prompts_dir = Path("config/prompts")
    assert prompts_dir.exists(), "提示词目录不存在"
    assert prompts_dir.is_dir(), "提示词路径不是目录"


def test_required_prompt_files_exist():
    """测试必需的提示词文件是否存在"""
    prompts_dir = Path("config/prompts")

    required_prompts = [
        "entity_extraction.txt",
        "relation_extraction.txt",
        "document_summary.txt",
        "graph_query.txt",
    ]

    for prompt_file in required_prompts:
        prompt_path = prompts_dir / prompt_file
        assert prompt_path.exists(), f"缺少提示词文件: {prompt_file}"
        assert prompt_path.stat().st_size > 0, f"提示词文件为空: {prompt_file}"
