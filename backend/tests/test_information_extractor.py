"""
信息抽取模块测试
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.services.information_extractor import (
    InformationExtractor,
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult
)
from backend.app.services.schema_manager import SchemaManager, KnowledgeGraphSchema
from backend.app.services.ollama_client import OllamaClient, ModelResponse


@pytest.fixture
def mock_schema_manager():
    """模拟Schema管理器"""
    manager = Mock(spec=SchemaManager)

    # 创建模拟Schema
    mock_schema = Mock(spec=KnowledgeGraphSchema)
    mock_schema.entities = {
        'Person': Mock(
            description='人员实体',
            properties={
                'name': {'type': 'string', 'required': True},
                'title': {'type': 'string', 'required': False}
            },
            required_properties={'name'}
        ),
        'Organization': Mock(
            description='组织实体',
            properties={
                'name': {'type': 'string', 'required': True}
            },
            required_properties={'name'}
        )
    }
    mock_schema.relations = {
        'WORKS_FOR': Mock(
            description='工作关系',
            source='Person',
            target='Organization',
            properties={}
        )
    }

    manager.get_schema.return_value = mock_schema
    manager.validate_entity_data.return_value = []
    manager.validate_relation_data.return_value = []

    return manager


@pytest.fixture
def mock_ollama_client():
    """模拟Ollama客户端"""
    client = Mock(spec=OllamaClient)

    # 模拟成功的响应
    mock_response = ModelResponse(
        content='```json\n{"entities": [{"type": "Person", "name": "张三", "properties": {"title": "工程师"}}], "relations": []}\n```',
        model="test-model",
        prompt="test prompt",
        response_time=1.0,
        success=True
    )

    client.generate_with_template.return_value = mock_response

    return client


@pytest.fixture
def extractor(mock_schema_manager, mock_ollama_client):
    """创建信息抽取器实例"""
    return InformationExtractor(
        schema_manager=mock_schema_manager,
        ollama_client=mock_ollama_client,
        chunk_size=100,  # 小的分块大小用于测试
        chunk_overlap=20
    )


def test_information_extractor_init(mock_schema_manager, mock_ollama_client):
    """测试信息抽取器初始化"""
    extractor = InformationExtractor(
        schema_manager=mock_schema_manager,
        ollama_client=mock_ollama_client,
        chunk_size=2000,
        chunk_overlap=200
    )

    assert extractor.schema_manager == mock_schema_manager
    assert extractor.ollama_client == mock_ollama_client
    assert extractor.chunk_size == 2000
    assert extractor.chunk_overlap == 200


def test_split_text_short(extractor):
    """测试短文本分块"""
    text = "这是一个短文本。"
    chunks = extractor._split_text(text)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_text_long(extractor):
    """测试长文本分块"""
    # 创建超过chunk_size的文本
    text = "这是第一句。" * 30  # 超过100字符
    chunks = extractor._split_text(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= extractor.chunk_size + extractor.chunk_overlap for chunk in chunks)


def test_format_schema_for_prompt(extractor, mock_schema_manager):
    """测试Schema格式化"""
    schema = mock_schema_manager.get_schema()
    formatted = extractor._format_schema_for_prompt(schema)

    assert "实体类型:" in formatted
    assert "关系类型:" in formatted
    assert "Person" in formatted
    assert "Organization" in formatted
    assert "WORKS_FOR" in formatted


def test_parse_model_response_valid_json(extractor):
    """测试解析有效的JSON响应"""
    response = '''```json
    {
        "entities": [
            {
                "type": "Person",
                "name": "张三",
                "properties": {"title": "工程师"},
                "confidence": 0.9
            }
        ],
        "relations": [
            {
                "type": "WORKS_FOR",
                "source": "张三",
                "target": "ABC公司",
                "properties": {},
                "confidence": 0.8
            }
        ]
    }
    ```'''

    entities, relations = extractor._parse_model_response(response, "测试文本")

    assert len(entities) == 1
    assert len(relations) == 1

    entity = entities[0]
    assert entity.type == "Person"
    assert entity.name == "张三"
    assert entity.properties["title"] == "工程师"
    assert entity.confidence == 0.9

    relation = relations[0]
    assert relation.type == "WORKS_FOR"
    assert relation.source == "张三"
    assert relation.target == "ABC公司"
    assert relation.confidence == 0.8


def test_parse_model_response_invalid_json(extractor):
    """测试解析无效的JSON响应"""
    response = "这不是有效的JSON格式"

    entities, relations = extractor._parse_model_response(response, "测试文本")

    # 应该返回空列表而不是抛出异常
    assert entities == []
    assert relations == []


def test_merge_entities(extractor):
    """测试实体合并"""
    entities = [
        ExtractedEntity(type="Person", name="张三", properties={"title": "工程师"}, confidence=0.8),
        ExtractedEntity(type="Person", name="张三", properties={"age": "30"}, confidence=0.9),
        ExtractedEntity(type="Person", name="李四", properties={"title": "经理"}, confidence=0.7)
    ]

    merged = extractor._merge_entities(entities)

    assert len(merged) == 2

    # 找到张三的实体
    zhangsan = next(e for e in merged if e.name == "张三")
    assert zhangsan.confidence == 0.9  # 应该保留更高的置信度
    assert "title" in zhangsan.properties
    assert "age" in zhangsan.properties


def test_merge_relations(extractor):
    """测试关系合并"""
    relations = [
        ExtractedRelation(type="WORKS_FOR", source="张三", target="ABC公司", properties={"position": "工程师"}, confidence=0.8),
        ExtractedRelation(type="WORKS_FOR", source="张三", target="ABC公司", properties={"department": "技术部"}, confidence=0.9),
        ExtractedRelation(type="WORKS_FOR", source="李四", target="ABC公司", properties={"position": "经理"}, confidence=0.7)
    ]

    merged = extractor._merge_relations(relations)

    assert len(merged) == 2

    # 找到张三的关系
    zhangsan_rel = next(r for r in merged if r.source == "张三")
    assert zhangsan_rel.confidence == 0.9
    assert "position" in zhangsan_rel.properties
    assert "department" in zhangsan_rel.properties


def test_extract_from_text_success(extractor, mock_ollama_client):
    """测试成功的文本抽取"""
    text = "张三是ABC公司的工程师。"

    result = extractor.extract_from_text(text)

    assert result.success is True
    assert result.source_text == text
    assert isinstance(result.extraction_time, datetime)
    assert result.metadata is not None


def test_extract_from_text_no_schema(extractor, mock_schema_manager):
    """测试没有Schema的情况"""
    mock_schema_manager.get_schema.return_value = None

    text = "张三是ABC公司的工程师。"
    result = extractor.extract_from_text(text)

    assert result.success is False
    assert "Schema未加载" in result.error_message


def test_extract_from_text_model_failure(extractor, mock_ollama_client):
    """测试模型调用失败的情况"""
    mock_response = ModelResponse(
        content="",
        model="test-model",
        prompt="test prompt",
        response_time=1.0,
        success=False,
        error_message="模型调用失败"
    )
    mock_ollama_client.generate_with_template.return_value = mock_response

    text = "张三是ABC公司的工程师。"
    result = extractor.extract_from_text(text)

    assert result.success is False
    assert "抽取失败" in result.error_message


def test_validate_extraction_result(extractor, mock_schema_manager):
    """测试抽取结果验证"""
    result = ExtractionResult(
        entities=[
            ExtractedEntity(type="Person", name="张三", properties={"title": "工程师"})
        ],
        relations=[
            ExtractedRelation(type="WORKS_FOR", source="张三", target="ABC公司", properties={})
        ],
        source_text="测试文本",
        extraction_time=datetime.now()
    )

    errors = extractor.validate_extraction_result(result)

    # 由于mock返回空错误列表，应该没有错误
    assert errors == []


def test_get_extraction_stats(extractor):
    """测试获取抽取统计信息"""
    result = ExtractionResult(
        entities=[
            ExtractedEntity(type="Person", name="张三", properties={}),
            ExtractedEntity(type="Person", name="李四", properties={}),
            ExtractedEntity(type="Organization", name="ABC公司", properties={})
        ],
        relations=[
            ExtractedRelation(type="WORKS_FOR", source="张三", target="ABC公司", properties={}),
            ExtractedRelation(type="WORKS_FOR", source="李四", target="ABC公司", properties={})
        ],
        source_text="测试文本",
        extraction_time=datetime.now()
    )

    stats = extractor.get_extraction_stats(result)

    assert stats['total_entities'] == 3
    assert stats['total_relations'] == 2
    assert stats['entity_types']['Person'] == 2
    assert stats['entity_types']['Organization'] == 1
    assert stats['relation_types']['WORKS_FOR'] == 2


def test_extracted_entity_dataclass():
    """测试ExtractedEntity数据类"""
    entity = ExtractedEntity(
        type="Person",
        name="张三",
        properties={"title": "工程师"},
        confidence=0.9,
        source_text="测试文本"
    )

    assert entity.type == "Person"
    assert entity.name == "张三"
    assert entity.properties["title"] == "工程师"
    assert entity.confidence == 0.9
    assert entity.source_text == "测试文本"


def test_extracted_relation_dataclass():
    """测试ExtractedRelation数据类"""
    relation = ExtractedRelation(
        type="WORKS_FOR",
        source="张三",
        target="ABC公司",
        properties={"position": "工程师"},
        confidence=0.8,
        source_text="测试文本"
    )

    assert relation.type == "WORKS_FOR"
    assert relation.source == "张三"
    assert relation.target == "ABC公司"
    assert relation.properties["position"] == "工程师"
    assert relation.confidence == 0.8
    assert relation.source_text == "测试文本"


def test_extraction_result_dataclass():
    """测试ExtractionResult数据类"""
    entities = [ExtractedEntity(type="Person", name="张三", properties={})]
    relations = [ExtractedRelation(type="WORKS_FOR", source="张三", target="ABC公司", properties={})]

    result = ExtractionResult(
        entities=entities,
        relations=relations,
        source_text="测试文本",
        extraction_time=datetime.now(),
        success=True,
        metadata={"key": "value"}
    )

    assert result.entities == entities
    assert result.relations == relations
    assert result.source_text == "测试文本"
    assert result.success is True
    assert result.error_message == ""
    assert result.metadata["key"] == "value"
