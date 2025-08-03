#!/usr/bin/env python3
"""
Neo4j数据库初始化脚本
根据schema.yaml创建约束和索引
"""

from pathlib import Path

import yaml
from loguru import logger
from neo4j import GraphDatabase


class Neo4jInitializer:
    """Neo4j数据库初始化器"""

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """关闭数据库连接"""
        self.driver.close()

    def load_schema(self, schema_path: str) -> dict:
        """加载Schema配置"""
        with open(schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def create_constraints(self, schema: dict):
        """创建约束"""
        logger.info("正在创建数据库约束...")

        with self.driver.session() as session:
            for entity_name, entity_config in schema.get("entities", {}).items():
                # 为每个实体的必需属性创建唯一约束
                for prop_name, prop_config in entity_config.get(
                    "properties", {}
                ).items():
                    if prop_config.get("required", False):
                        constraint_name = (
                            f"constraint_{entity_name.lower()}_{prop_name.lower()}"
                        )

                        # 检查约束是否已存在
                        check_query = """
                        SHOW CONSTRAINTS
                        YIELD name
                        WHERE name = $constraint_name
                        RETURN count(*) as count
                        """
                        result = session.run(
                            check_query, constraint_name=constraint_name
                        )
                        if result.single()["count"] == 0:
                            # 创建唯一约束
                            constraint_query = f"""
                            CREATE CONSTRAINT {constraint_name}
                            FOR (n:{entity_name})
                            REQUIRE n.{prop_name} IS UNIQUE
                            """
                            try:
                                session.run(constraint_query)
                                logger.info(f"✅ 创建约束: {constraint_name}")
                            except Exception as e:
                                logger.warning(f"⚠️ 约束创建失败 {constraint_name}: {e}")
                        else:
                            logger.info(f"📋 约束已存在: {constraint_name}")

    def create_indexes(self, schema: dict):
        """创建索引"""
        logger.info("正在创建数据库索引...")

        with self.driver.session() as session:
            for entity_name, entity_config in schema.get("entities", {}).items():
                # 为每个实体的所有属性创建索引
                for prop_name in entity_config.get("properties", {}).keys():
                    index_name = f"index_{entity_name.lower()}_{prop_name.lower()}"

                    # 检查索引是否已存在
                    check_query = """
                    SHOW INDEXES
                    YIELD name
                    WHERE name = $index_name
                    RETURN count(*) as count
                    """
                    result = session.run(check_query, index_name=index_name)
                    if result.single()["count"] == 0:
                        # 创建索引
                        index_query = f"""
                        CREATE INDEX {index_name}
                        FOR (n:{entity_name})
                        ON (n.{prop_name})
                        """
                        try:
                            session.run(index_query)
                            logger.info(f"✅ 创建索引: {index_name}")
                        except Exception as e:
                            logger.warning(f"⚠️ 索引创建失败 {index_name}: {e}")
                    else:
                        logger.info(f"📋 索引已存在: {index_name}")

    def create_sample_data(self):
        """创建示例数据"""
        logger.info("正在创建示例数据...")

        with self.driver.session() as session:
            # 创建示例人员
            session.run(
                """
                MERGE (p1:Person {name: '张三', title: '项目经理', department: '技术部'})
                MERGE (p2:Person {name: '李四', title: '开发工程师', department: '技术部'})
                MERGE (p3:Person {name: '王五', title: '产品经理', department: '产品部'})

                MERGE (org:Organization {name: '示例公司', type: '科技公司'})
                MERGE (proj:Project {name: '知识图谱项目', status: '进行中'})
                MERGE (doc:Document {title: '项目需求文档', type: 'Word文档'})

                MERGE (p1)-[:WORKS_FOR {position: '项目经理'}]->(org)
                MERGE (p2)-[:WORKS_FOR {position: '开发工程师'}]->(org)
                MERGE (p3)-[:WORKS_FOR {position: '产品经理'}]->(org)

                MERGE (p1)-[:MANAGES {role: '项目负责人'}]->(proj)
                MERGE (p2)-[:PARTICIPATES_IN {role: '开发人员'}]->(proj)
                MERGE (p3)-[:PARTICIPATES_IN {role: '需求分析'}]->(proj)

                MERGE (proj)-[:BELONGS_TO]->(org)
                MERGE (doc)-[:AUTHORED_BY]->(p3)
                MERGE (doc)-[:RELATES_TO]->(proj)
            """
            )

            logger.info("✅ 示例数据创建完成")

    def show_database_info(self):
        """显示数据库信息"""
        logger.info("数据库信息:")

        with self.driver.session() as session:
            # 显示节点统计
            result = session.run(
                "MATCH (n) RETURN labels(n) as labels, count(*) as count"
            )
            logger.info("节点统计:")
            for record in result:
                labels = record["labels"]
                count = record["count"]
                if labels:
                    logger.info(f"  {labels[0]}: {count} 个节点")

            # 显示关系统计
            result = session.run(
                "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count"
            )
            logger.info("关系统计:")
            for record in result:
                logger.info(f"  {record['type']}: {record['count']} 个关系")


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Neo4j数据库初始化")
    logger.info("=" * 50)

    # 连接配置
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "graghrag123"
    schema_path = "config/schema.yaml"

    try:
        # 初始化数据库
        initializer = Neo4jInitializer(uri, username, password)

        # 加载Schema
        schema = initializer.load_schema(schema_path)
        logger.info(f"📋 加载Schema: {schema.get('description', 'Unknown')}")

        # 创建约束和索引
        initializer.create_constraints(schema)
        initializer.create_indexes(schema)

        # 创建示例数据
        initializer.create_sample_data()

        # 显示数据库信息
        initializer.show_database_info()

        initializer.close()
        logger.info("✅ Neo4j数据库初始化完成！")

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
