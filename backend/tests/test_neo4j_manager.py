"""
Neo4j管理模块测试
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.services.neo4j_manager import (
    Neo4jManager,
    GraphStats,
    QueryResult
)
from backend.app.services.information_extractor import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult
)


@pytest.fixture
def mock_driver():
    """模拟Neo4j驱动"""
    driver = Mock()
    session = Mock()
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    return driver, session


@pytest.fixture
def neo4j_manager():
    """创建Neo4j管理器实例"""
    return Neo4jManager(
        uri="bolt://localhost:7687",
        username="test_user",
        password="test_password",
        database="test_db"
    )


def test_neo4j_manager_init():
    """测试Neo4j管理器初始化"""
    manager = Neo4jManager(
        uri="bolt://test:7687",
        username="test",
        password="pass",
        database="testdb"
    )

    assert manager.uri == "bolt://test:7687"
    assert manager.username == "test"
    assert manager.password == "pass"
    assert manager.database == "testdb"
    assert manager.driver is None


@patch('backend.app.services.neo4j_manager.GraphDatabase')
def test_connect_success(mock_graph_db, neo4j_manager):
    """测试成功连接"""
    mock_driver = Mock()
    mock_session = Mock()
    mock_result = Mock()
    mock_record = Mock()

    mock_graph_db.driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.run.return_value = mock_result
    mock_result.single.return_value = {"test": 1}

    success = neo4j_manager.connect()

    assert success is True
    assert neo4j_manager.driver == mock_driver
    mock_graph_db.driver.assert_called_once_with(
        "bolt://localhost:7687",
        auth=("neo4j", "graghrag123")
    )


@patch('backend.app.services.neo4j_manager.GraphDatabase')
def test_connect_service_unavailable(mock_graph_db, neo4j_manager):
    """测试服务不可用"""
    from neo4j.exceptions import ServiceUnavailable

    mock_graph_db.driver.side_effect = ServiceUnavailable("Service unavailable")

    success = neo4j_manager.connect()

    assert success is False
    assert neo4j_manager.driver is None


@patch('backend.app.services.neo4j_manager.GraphDatabase')
def test_connect_auth_error(mock_graph_db, neo4j_manager):
    """测试认证错误"""
    from neo4j.exceptions import AuthError

    mock_graph_db.driver.side_effect = AuthError("Authentication failed")

    success = neo4j_manager.connect()

    assert success is False
    assert neo4j_manager.driver is None


def test_disconnect(neo4j_manager):
    """测试断开连接"""
    mock_driver = Mock()
    neo4j_manager.driver = mock_driver

    neo4j_manager.disconnect()

    mock_driver.close.assert_called_once()
    assert neo4j_manager.driver is None


def test_execute_query_no_driver(neo4j_manager):
    """测试未连接时执行查询"""
    result = neo4j_manager.execute_query("RETURN 1")

    assert result.success is False
    assert "数据库未连接" in result.error_message
    assert result.records == []


def test_execute_query_success(neo4j_manager, mock_driver):
    """测试成功执行查询"""
    driver, session = mock_driver
    neo4j_manager.driver = driver

    # 模拟查询结果
    mock_result = Mock()
    mock_record = Mock()
    mock_record.keys.return_value = ['name', 'age']
    mock_record.__getitem__.side_effect = lambda key: {'name': 'test', 'age': 30}[key]

    mock_result.__iter__.return_value = [mock_record]
    session.run.return_value = mock_result

    result = neo4j_manager.execute_query("MATCH (n) RETURN n.name as name, n.age as age")

    assert result.success is True
    assert len(result.records) == 1
    assert result.records[0]['name'] == 'test'
    assert result.records[0]['age'] == 30


def test_execute_query_cypher_error(neo4j_manager, mock_driver):
    """测试Cypher查询错误"""
    from neo4j.exceptions import ClientError

    driver, session = mock_driver
    neo4j_manager.driver = driver

    session.run.side_effect = ClientError("Invalid syntax")

    result = neo4j_manager.execute_query("INVALID QUERY")

    assert result.success is False
    assert "Invalid syntax" in result.error_message


def test_create_entity_success(neo4j_manager):
    """测试成功创建实体"""
    entity = ExtractedEntity(
        type="Person",
        name="张三",
        properties={"title": "工程师"},
        confidence=0.9
    )

    # 模拟成功的查询结果
    with patch.object(neo4j_manager, 'execute_query') as mock_query:
        mock_query.return_value = QueryResult(
            records=[{"e": {"name": "张三"}}],
            summary={},
            success=True
        )

        success = neo4j_manager.create_entity(entity)

        assert success is True
        mock_query.assert_called_once()


def test_create_entity_failure(neo4j_manager):
    """测试创建实体失败"""
    entity = ExtractedEntity(
        type="Person",
        name="张三",
        properties={},
        confidence=0.9
    )

    # 模拟失败的查询结果
    with patch.object(neo4j_manager, 'execute_query') as mock_query:
        mock_query.return_value = QueryResult(
            records=[],
            summary={},
            success=False,
            error_message="创建失败"
        )

        success = neo4j_manager.create_entity(entity)

        assert success is False


def test_create_relationship_success(neo4j_manager):
    """测试成功创建关系"""
    relation = ExtractedRelation(
        type="WORKS_FOR",
        source="张三",
        target="ABC公司",
        properties={},
        confidence=0.8
    )

    # 模拟成功的查询结果
    with patch.object(neo4j_manager, 'execute_query') as mock_query:
        mock_query.return_value = QueryResult(
            records=[{"r": {"type": "WORKS_FOR"}}],
            summary={},
            success=True
        )

        success = neo4j_manager.create_relationship(relation)

        assert success is True
        mock_query.assert_called_once()


def test_create_relationship_failure(neo4j_manager):
    """测试创建关系失败"""
    relation = ExtractedRelation(
        type="WORKS_FOR",
        source="张三",
        target="ABC公司",
        properties={},
        confidence=0.8
    )

    # 模拟失败的查询结果
    with patch.object(neo4j_manager, 'execute_query') as mock_query:
        mock_query.return_value = QueryResult(
            records=[],
            summary={},
            success=False,
            error_message="创建失败"
        )

        success = neo4j_manager.create_relationship(relation)

        assert success is False


def test_import_extraction_result_success(neo4j_manager):
    """测试成功导入抽取结果"""
    entities = [
        ExtractedEntity(type="Person", name="张三", properties={}, confidence=0.9),
        ExtractedEntity(type="Organization", name="ABC公司", properties={}, confidence=0.8)
    ]

    relations = [
        ExtractedRelation(type="WORKS_FOR", source="张三", target="ABC公司", properties={}, confidence=0.7)
    ]

    extraction_result = ExtractionResult(
        entities=entities,
        relations=relations,
        source_text="测试文本",
        extraction_time=datetime.now(),
        success=True
    )

    # 模拟成功的实体和关系创建
    with patch.object(neo4j_manager, 'create_entity', return_value=True) as mock_create_entity, \
         patch.object(neo4j_manager, 'create_relationship', return_value=True) as mock_create_rel:

        entity_count, relation_count = neo4j_manager.import_extraction_result(extraction_result)

        assert entity_count == 2
        assert relation_count == 1
        assert mock_create_entity.call_count == 2
        assert mock_create_rel.call_count == 1


def test_import_extraction_result_failed_extraction(neo4j_manager):
    """测试导入失败的抽取结果"""
    extraction_result = ExtractionResult(
        entities=[],
        relations=[],
        source_text="测试文本",
        extraction_time=datetime.now(),
        success=False,
        error_message="抽取失败"
    )

    entity_count, relation_count = neo4j_manager.import_extraction_result(extraction_result)

    assert entity_count == 0
    assert relation_count == 0


def test_get_graph_stats_success(neo4j_manager):
    """测试获取图谱统计信息成功"""
    # 模拟节点查询结果
    node_result = QueryResult(
        records=[
            {"labels": ["Person"], "count": 5},
            {"labels": ["Organization"], "count": 3}
        ],
        summary={},
        success=True
    )

    # 模拟关系查询结果
    rel_result = QueryResult(
        records=[
            {"type": "WORKS_FOR", "count": 4},
            {"type": "MANAGES", "count": 2}
        ],
        summary={},
        success=True
    )

    with patch.object(neo4j_manager, 'execute_query', side_effect=[node_result, rel_result]):
        stats = neo4j_manager.get_graph_stats()

        assert stats is not None
        assert stats.total_nodes == 8
        assert stats.total_relationships == 6
        assert stats.node_types["Person"] == 5
        assert stats.node_types["Organization"] == 3
        assert stats.relationship_types["WORKS_FOR"] == 4
        assert stats.relationship_types["MANAGES"] == 2


def test_get_graph_stats_failure(neo4j_manager):
    """测试获取图谱统计信息失败"""
    # 模拟查询失败
    failed_result = QueryResult(
        records=[],
        summary={},
        success=False,
        error_message="查询失败"
    )

    with patch.object(neo4j_manager, 'execute_query', return_value=failed_result):
        stats = neo4j_manager.get_graph_stats()

        assert stats is None


def test_search_entities_success(neo4j_manager):
    """测试搜索实体成功"""
    search_result = QueryResult(
        records=[
            {"n": {"name": "张三", "title": "工程师"}, "labels": ["Person"]},
            {"n": {"name": "李四", "title": "经理"}, "labels": ["Person"]}
        ],
        summary={},
        success=True
    )

    with patch.object(neo4j_manager, 'execute_query', return_value=search_result):
        entities = neo4j_manager.search_entities(entity_type="Person", name_pattern="张")

        assert len(entities) == 2
        assert entities[0]["name"] == "张三"
        assert entities[0]["_labels"] == ["Person"]


def test_search_entities_failure(neo4j_manager):
    """测试搜索实体失败"""
    failed_result = QueryResult(
        records=[],
        summary={},
        success=False,
        error_message="搜索失败"
    )

    with patch.object(neo4j_manager, 'execute_query', return_value=failed_result):
        entities = neo4j_manager.search_entities()

        assert entities == []


def test_clear_database_success(neo4j_manager):
    """测试清空数据库成功"""
    success_result = QueryResult(
        records=[],
        summary={},
        success=True
    )

    with patch.object(neo4j_manager, 'execute_query', return_value=success_result):
        success = neo4j_manager.clear_database()

        assert success is True


def test_clear_database_failure(neo4j_manager):
    """测试清空数据库失败"""
    failed_result = QueryResult(
        records=[],
        summary={},
        success=False,
        error_message="清空失败"
    )

    with patch.object(neo4j_manager, 'execute_query', return_value=failed_result):
        success = neo4j_manager.clear_database()

        assert success is False


def test_context_manager(neo4j_manager):
    """测试上下文管理器"""
    with patch.object(neo4j_manager, 'connect', return_value=True) as mock_connect, \
         patch.object(neo4j_manager, 'disconnect') as mock_disconnect:

        with neo4j_manager as manager:
            assert manager == neo4j_manager

        mock_connect.assert_called_once()
        mock_disconnect.assert_called_once()


def test_graph_stats_dataclass():
    """测试GraphStats数据类"""
    stats = GraphStats(
        total_nodes=10,
        total_relationships=15,
        node_types={"Person": 5, "Organization": 5},
        relationship_types={"WORKS_FOR": 10, "MANAGES": 5},
        last_updated=datetime.now()
    )

    assert stats.total_nodes == 10
    assert stats.total_relationships == 15
    assert stats.node_types["Person"] == 5
    assert stats.relationship_types["WORKS_FOR"] == 10


def test_query_result_dataclass():
    """测试QueryResult数据类"""
    result = QueryResult(
        records=[{"name": "test"}],
        summary={"count": 1},
        success=True,
        execution_time=1.5
    )

    assert result.records == [{"name": "test"}]
    assert result.summary == {"count": 1}
    assert result.success is True
    assert result.error_message == ""
    assert result.execution_time == 1.5
