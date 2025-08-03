"""
Neo4j数据库管理服务模块
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
from loguru import logger

from .information_extractor import ExtractedEntity, ExtractedRelation, ExtractionResult
from .schema_manager import SchemaManager


@dataclass
class GraphStats:
    """图谱统计信息"""
    total_nodes: int
    total_relationships: int
    node_types: Dict[str, int]
    relationship_types: Dict[str, int]
    last_updated: datetime


@dataclass
class QueryResult:
    """查询结果"""
    records: List[Dict[str, Any]]
    summary: Dict[str, Any]
    success: bool = True
    error_message: str = ""
    execution_time: float = 0.0


class Neo4jManager:
    """Neo4j数据库管理器"""

    def __init__(self,
                 uri: str = "bolt://localhost:7687",
                 username: str = "neo4j",
                 password: str = "graghrag123",
                 database: str = "neo4j"):
        """
        初始化Neo4j管理器

        Args:
            uri: Neo4j连接URI
            username: 用户名
            password: 密码
            database: 数据库名称
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Optional[Driver] = None

        logger.info(f"Neo4j管理器初始化完成")
        logger.info(f"连接URI: {uri}")
        logger.info(f"数据库: {database}")

    def connect(self) -> bool:
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )

            # 测试连接
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]

                if test_value == 1:
                    logger.info("✅ Neo4j连接成功")
                    return True
                else:
                    logger.error("❌ Neo4j连接测试失败")
                    return False

        except ServiceUnavailable as e:
            logger.error(f"❌ Neo4j服务不可用: {e}")
            return False
        except AuthError as e:
            logger.error(f"❌ Neo4j认证失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j连接已断开")

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> QueryResult:
        """
        执行Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            QueryResult: 查询结果
        """
        if not self.driver:
            return QueryResult(
                records=[],
                summary={},
                success=False,
                error_message="数据库未连接"
            )

        start_time = datetime.now()

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})

                records = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # 处理Neo4j节点和关系对象
                        if hasattr(value, '_properties'):
                            record_dict[key] = dict(value._properties)
                            if hasattr(value, '_labels'):
                                record_dict[key]['_labels'] = list(value._labels)
                            if hasattr(value, '_type'):
                                record_dict[key]['_type'] = value._type
                        else:
                            record_dict[key] = value
                    records.append(record_dict)

                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()

                summary = {
                    'records_count': len(records),
                    'execution_time': execution_time
                }

                logger.debug(f"查询执行成功，返回 {len(records)} 条记录")

                return QueryResult(
                    records=records,
                    summary=summary,
                    success=True,
                    execution_time=execution_time
                )

        except ClientError as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            logger.error(f"Cypher查询错误: {e}")
            return QueryResult(
                records=[],
                summary={},
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            logger.error(f"查询执行失败: {e}")
            return QueryResult(
                records=[],
                summary={},
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    def create_entity(self, entity: ExtractedEntity) -> bool:
        """
        创建实体节点

        Args:
            entity: 抽取的实体

        Returns:
            bool: 是否创建成功
        """
        # 构建属性字典
        properties = {
            'name': entity.name,
            'confidence': entity.confidence,
            'created_at': datetime.now().isoformat(),
            **entity.properties
        }

        # 构建Cypher查询
        query = f"""
        MERGE (e:{entity.type} {{name: $name}})
        SET e += $properties
        RETURN e
        """

        parameters = {
            'name': entity.name,
            'properties': properties
        }

        result = self.execute_query(query, parameters)

        if result.success:
            logger.debug(f"实体创建成功: {entity.type}({entity.name})")
            return True
        else:
            logger.error(f"实体创建失败: {result.error_message}")
            return False

    def create_relationship(self, relation: ExtractedRelation) -> bool:
        """
        创建关系

        Args:
            relation: 抽取的关系

        Returns:
            bool: 是否创建成功
        """
        # 构建属性字典
        properties = {
            'confidence': relation.confidence,
            'created_at': datetime.now().isoformat(),
            **relation.properties
        }

        # 构建Cypher查询
        query = f"""
        MATCH (source {{name: $source_name}})
        MATCH (target {{name: $target_name}})
        MERGE (source)-[r:{relation.type}]->(target)
        SET r += $properties
        RETURN r
        """

        parameters = {
            'source_name': relation.source,
            'target_name': relation.target,
            'properties': properties
        }

        result = self.execute_query(query, parameters)

        if result.success:
            logger.debug(f"关系创建成功: {relation.source} -[{relation.type}]-> {relation.target}")
            return True
        else:
            logger.error(f"关系创建失败: {result.error_message}")
            return False

    def import_extraction_result(self, extraction_result: ExtractionResult) -> Tuple[int, int]:
        """
        导入抽取结果到图数据库

        Args:
            extraction_result: 信息抽取结果

        Returns:
            Tuple[int, int]: (成功导入的实体数, 成功导入的关系数)
        """
        if not extraction_result.success:
            logger.warning("抽取结果不成功，跳过导入")
            return 0, 0

        logger.info(f"开始导入抽取结果: {len(extraction_result.entities)} 个实体, {len(extraction_result.relations)} 个关系")

        entity_count = 0
        relation_count = 0

        # 导入实体
        for entity in extraction_result.entities:
            if self.create_entity(entity):
                entity_count += 1

        # 导入关系
        for relation in extraction_result.relations:
            if self.create_relationship(relation):
                relation_count += 1

        logger.info(f"导入完成: 实体 {entity_count}/{len(extraction_result.entities)}, 关系 {relation_count}/{len(extraction_result.relations)}")

        return entity_count, relation_count

    def get_graph_stats(self) -> Optional[GraphStats]:
        """获取图谱统计信息"""
        try:
            # 获取节点统计
            node_query = """
            MATCH (n)
            RETURN labels(n) as labels, count(*) as count
            """
            node_result = self.execute_query(node_query)

            if not node_result.success:
                return None

            total_nodes = 0
            node_types = {}

            for record in node_result.records:
                labels = record['labels']
                count = record['count']
                total_nodes += count

                if labels:
                    label = labels[0]  # 使用第一个标签
                    node_types[label] = count

            # 获取关系统计
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(*) as count
            """
            rel_result = self.execute_query(rel_query)

            if not rel_result.success:
                return None

            total_relationships = 0
            relationship_types = {}

            for record in rel_result.records:
                rel_type = record['type']
                count = record['count']
                total_relationships += count
                relationship_types[rel_type] = count

            return GraphStats(
                total_nodes=total_nodes,
                total_relationships=total_relationships,
                node_types=node_types,
                relationship_types=relationship_types,
                last_updated=datetime.now()
            )

        except Exception as e:
            logger.error(f"获取图谱统计失败: {e}")
            return None

    def search_entities(self, entity_type: str = None, name_pattern: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜索实体

        Args:
            entity_type: 实体类型
            name_pattern: 名称模式（支持模糊匹配）
            limit: 返回结果限制

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        conditions = []
        parameters = {'limit': limit}

        if entity_type:
            label_filter = f":{entity_type}"
        else:
            label_filter = ""

        if name_pattern:
            conditions.append("n.name CONTAINS $name_pattern")
            parameters['name_pattern'] = name_pattern

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
        MATCH (n{label_filter})
        {where_clause}
        RETURN n, labels(n) as labels
        LIMIT $limit
        """

        result = self.execute_query(query, parameters)

        if result.success:
            entities = []
            for record in result.records:
                entity_data = record['n']
                entity_data['_labels'] = record['labels']
                entities.append(entity_data)
            return entities
        else:
            logger.error(f"实体搜索失败: {result.error_message}")
            return []

    def get_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        获取实体的所有关系

        Args:
            entity_name: 实体名称

        Returns:
            List[Dict[str, Any]]: 关系列表
        """
        query = """
        MATCH (source {name: $entity_name})-[r]-(target)
        RETURN source, r, target, type(r) as rel_type
        """

        result = self.execute_query(query, {'entity_name': entity_name})

        if result.success:
            relationships = []
            for record in result.records:
                rel_data = {
                    'source': record['source'],
                    'target': record['target'],
                    'relationship': record['r'],
                    'type': record['rel_type']
                }
                relationships.append(rel_data)
            return relationships
        else:
            logger.error(f"获取实体关系失败: {result.error_message}")
            return []

    def clear_database(self) -> bool:
        """清空数据库（谨慎使用）"""
        logger.warning("正在清空数据库...")

        query = "MATCH (n) DETACH DELETE n"
        result = self.execute_query(query)

        if result.success:
            logger.info("✅ 数据库已清空")
            return True
        else:
            logger.error(f"❌ 清空数据库失败: {result.error_message}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
