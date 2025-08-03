"""
Schema管理模块测试
"""

import pytest
import tempfile
import yaml
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.services.schema_manager import (
    SchemaManager,
    SchemaValidationError,
    EntitySchema,
    RelationSchema,
    KnowledgeGraphSchema
)


@pytest.fixture
def valid_schema_data():
    """有效的Schema数据"""
    return {
        'version': '1.0.0',
        'description': '测试Schema',
        'entities': {
            'Person': {
                'description': '人员实体',
                'properties': {
                    'name': {
                        'type': 'string',
                        'required': True,
                        'description': '姓名'
                    },
                    'age': {
                        'type': 'integer',
                        'required': False,
                        'description': '年龄'
                    }
                }
            },
            'Organization': {
                'description': '组织实体',
                'properties': {
                    'name': {
                        'type': 'string',
                        'required': True,
                        'description': '组织名称'
                    }
                }
            }
        },
        'relations': {
            'WORKS_FOR': {
                'description': '工作关系',
                'source': 'Person',
                'target': 'Organization',
                'properties': {
                    'position': {
                        'type': 'string',
                        'required': False,
                        'description': '职位'
                    }
                }
            }
        }
    }


@pytest.fixture
def temp_schema_file(valid_schema_data):
    """创建临时Schema文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(valid_schema_data, f, allow_unicode=True)
        temp_path = Path(f.name)

    yield temp_path

    # 清理
    if temp_path.exists():
        temp_path.unlink()


def test_schema_manager_init():
    """测试Schema管理器初始化"""
    manager = SchemaManager("test_schema.yaml")

    assert manager.schema_file == Path("test_schema.yaml")
    assert manager.schema is None
    assert manager._file_mtime is None


def test_load_valid_schema(temp_schema_file):
    """测试加载有效Schema"""
    manager = SchemaManager(str(temp_schema_file))

    schema = manager.load_schema()

    assert isinstance(schema, KnowledgeGraphSchema)
    assert schema.version == '1.0.0'
    assert schema.description == '测试Schema'
    assert len(schema.entities) == 2
    assert len(schema.relations) == 1

    # 检查实体
    assert 'Person' in schema.entities
    assert 'Organization' in schema.entities

    person_entity = schema.entities['Person']
    assert person_entity.name == 'Person'
    assert person_entity.description == '人员实体'
    assert 'name' in person_entity.required_properties
    assert 'age' not in person_entity.required_properties

    # 检查关系
    assert 'WORKS_FOR' in schema.relations
    works_for_relation = schema.relations['WORKS_FOR']
    assert works_for_relation.source == 'Person'
    assert works_for_relation.target == 'Organization'


def test_load_nonexistent_file():
    """测试加载不存在的文件"""
    manager = SchemaManager("/nonexistent/schema.yaml")

    with pytest.raises(FileNotFoundError):
        manager.load_schema()


def test_invalid_yaml_format():
    """测试无效的YAML格式"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write("invalid: yaml: content: [")
        temp_path = Path(f.name)

    try:
        manager = SchemaManager(str(temp_path))

        with pytest.raises(SchemaValidationError):
            manager.load_schema()
    finally:
        temp_path.unlink()


def test_missing_required_fields():
    """测试缺少必需字段"""
    invalid_schema = {
        'version': '1.0.0',
        # 缺少 description, entities, relations
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(invalid_schema, f)
        temp_path = Path(f.name)

    try:
        manager = SchemaManager(str(temp_path))

        with pytest.raises(SchemaValidationError) as exc_info:
            manager.load_schema()

        assert "缺少必需字段" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_invalid_relation_reference():
    """测试关系引用不存在的实体"""
    invalid_schema = {
        'version': '1.0.0',
        'description': '测试Schema',
        'entities': {
            'Person': {
                'description': '人员实体',
                'properties': {}
            }
        },
        'relations': {
            'WORKS_FOR': {
                'description': '工作关系',
                'source': 'Person',
                'target': 'NonexistentEntity',  # 不存在的实体
                'properties': {}
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(invalid_schema, f)
        temp_path = Path(f.name)

    try:
        manager = SchemaManager(str(temp_path))

        with pytest.raises(SchemaValidationError) as exc_info:
            manager.load_schema()

        assert "未定义" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_get_schema_methods(temp_schema_file):
    """测试获取Schema的各种方法"""
    manager = SchemaManager(str(temp_schema_file))
    manager.load_schema()

    # 测试获取整个Schema
    schema = manager.get_schema()
    assert schema is not None

    # 测试获取实体Schema
    person_schema = manager.get_entity_schema('Person')
    assert person_schema is not None
    assert person_schema.name == 'Person'

    nonexistent_entity = manager.get_entity_schema('NonexistentEntity')
    assert nonexistent_entity is None

    # 测试获取关系Schema
    works_for_schema = manager.get_relation_schema('WORKS_FOR')
    assert works_for_schema is not None
    assert works_for_schema.name == 'WORKS_FOR'

    nonexistent_relation = manager.get_relation_schema('NonexistentRelation')
    assert nonexistent_relation is None

    # 测试获取名称列表
    entity_names = manager.get_entity_names()
    assert 'Person' in entity_names
    assert 'Organization' in entity_names

    relation_names = manager.get_relation_names()
    assert 'WORKS_FOR' in relation_names


def test_validate_entity_data(temp_schema_file):
    """测试实体数据验证"""
    manager = SchemaManager(str(temp_schema_file))
    manager.load_schema()

    # 测试有效数据
    valid_person_data = {
        'name': '张三',
        'age': 30
    }
    errors = manager.validate_entity_data('Person', valid_person_data)
    assert len(errors) == 0

    # 测试缺少必需属性
    invalid_person_data = {
        'age': 30
        # 缺少必需的 name 属性
    }
    errors = manager.validate_entity_data('Person', invalid_person_data)
    assert len(errors) > 0
    assert any('缺少必需属性' in error for error in errors)

    # 测试未知实体类型
    errors = manager.validate_entity_data('UnknownEntity', {})
    assert len(errors) > 0
    assert any('未知的实体类型' in error for error in errors)


def test_validate_relation_data(temp_schema_file):
    """测试关系数据验证"""
    manager = SchemaManager(str(temp_schema_file))
    manager.load_schema()

    # 测试有效关系数据
    valid_relation_data = {
        'position': '软件工程师'
    }
    errors = manager.validate_relation_data('WORKS_FOR', valid_relation_data)
    assert len(errors) == 0

    # 测试未知关系类型
    errors = manager.validate_relation_data('UnknownRelation', {})
    assert len(errors) > 0
    assert any('未知的关系类型' in error for error in errors)


def test_schema_caching(temp_schema_file):
    """测试Schema缓存机制"""
    manager = SchemaManager(str(temp_schema_file))

    # 第一次加载
    schema1 = manager.load_schema()
    load_time1 = schema1.load_time

    # 第二次加载（应该使用缓存）
    schema2 = manager.load_schema()
    load_time2 = schema2.load_time

    assert load_time1 == load_time2  # 应该是同一个对象

    # 强制重新加载
    schema3 = manager.load_schema(force_reload=True)
    load_time3 = schema3.load_time

    assert load_time3 > load_time1  # 应该是新加载的


def test_get_schema_summary(temp_schema_file):
    """测试获取Schema摘要"""
    manager = SchemaManager(str(temp_schema_file))
    manager.load_schema()

    summary = manager.get_schema_summary()

    assert summary['version'] == '1.0.0'
    assert summary['description'] == '测试Schema'
    assert summary['entities_count'] == 2
    assert summary['relations_count'] == 1
    assert 'Person' in summary['entity_names']
    assert 'WORKS_FOR' in summary['relation_names']


def test_export_schema_json(temp_schema_file):
    """测试导出Schema为JSON"""
    manager = SchemaManager(str(temp_schema_file))
    manager.load_schema()

    json_schema = manager.export_schema_json()

    assert json_schema['version'] == '1.0.0'
    assert 'entities' in json_schema
    assert 'relations' in json_schema
    assert 'metadata' in json_schema

    # 检查实体结构
    assert 'Person' in json_schema['entities']
    person_entity = json_schema['entities']['Person']
    assert 'description' in person_entity
    assert 'properties' in person_entity
    assert 'required_properties' in person_entity


def test_empty_schema_manager():
    """测试未加载Schema的管理器"""
    manager = SchemaManager("nonexistent.yaml")

    assert manager.get_schema() is None
    assert manager.get_entity_schema('Person') is None
    assert manager.get_relation_schema('WORKS_FOR') is None
    assert manager.get_entity_names() == []
    assert manager.get_relation_names() == []
    assert manager.get_schema_summary() == {}
    assert manager.export_schema_json() == {}
