"""
测试配置文件
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from neo4j import GraphDatabase

# 测试配置
TEST_NEO4J_URI = "bolt://localhost:7687"
TEST_NEO4J_USERNAME = "neo4j"
TEST_NEO4J_PASSWORD = "graghrag123"
TEST_DATABASE = "test_graghrag"


@pytest.fixture(scope="session")
def temp_dir():
    """创建临时目录"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture(scope="session")
def neo4j_driver():
    """Neo4j数据库连接"""
    driver = GraphDatabase.driver(
        TEST_NEO4J_URI, auth=(TEST_NEO4J_USERNAME, TEST_NEO4J_PASSWORD)
    )
    yield driver
    driver.close()


@pytest.fixture(scope="function")
def clean_neo4j(neo4j_driver):
    """清理Neo4j测试数据"""
    with neo4j_driver.session() as session:
        # 清理所有测试数据
        session.run("MATCH (n) WHERE n.test_marker = true DETACH DELETE n")

    yield

    with neo4j_driver.session() as session:
        # 测试后清理
        session.run("MATCH (n) WHERE n.test_marker = true DETACH DELETE n")


@pytest.fixture
def test_config():
    """测试配置"""
    return {
        "neo4j": {
            "uri": TEST_NEO4J_URI,
            "username": TEST_NEO4J_USERNAME,
            "password": TEST_NEO4J_PASSWORD,
            "database": TEST_DATABASE,
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "qwen3:4b",
            "timeout": 30,
        },
        "document": {
            "scan_directories": ["./test_data"],
            "supported_formats": [".docx", ".xlsx"],
            "output_directory": "./test_output",
        },
    }


@pytest.fixture
def sample_text():
    """示例文本数据"""
    return """
    张三是ABC公司的项目经理，负责管理知识图谱项目。
    李四是该公司的开发工程师，参与项目开发工作。
    王五是产品经理，负责需求分析。
    这个项目属于技术部门，预计在2024年完成。
    """


@pytest.fixture
def sample_entities():
    """示例实体数据"""
    return [
        {
            "type": "Person",
            "name": "张三",
            "properties": {"title": "项目经理", "department": "技术部"},
        },
        {
            "type": "Person",
            "name": "李四",
            "properties": {"title": "开发工程师", "department": "技术部"},
        },
        {"type": "Organization", "name": "ABC公司", "properties": {"type": "科技公司"}},
        {"type": "Project", "name": "知识图谱项目", "properties": {"status": "进行中"}},
    ]


@pytest.fixture
def sample_relations():
    """示例关系数据"""
    return [
        {
            "source": "张三",
            "target": "ABC公司",
            "type": "WORKS_FOR",
            "properties": {"position": "项目经理"},
        },
        {
            "source": "李四",
            "target": "ABC公司",
            "type": "WORKS_FOR",
            "properties": {"position": "开发工程师"},
        },
        {
            "source": "张三",
            "target": "知识图谱项目",
            "type": "MANAGES",
            "properties": {"role": "项目负责人"},
        },
    ]
