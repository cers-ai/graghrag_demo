"""
社区摘要服务
实现GraphRAG核心功能：为社区生成智能摘要
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class CommunitySummarizer:
    """社区摘要生成器 - GraphRAG核心组件"""

    def __init__(self, ollama_client: OllamaClient, neo4j_manager=None):
        """初始化社区摘要生成器"""
        self.ollama_client = ollama_client
        self.neo4j_manager = neo4j_manager
        self.community_summaries = {}

    def generate_community_summary(
        self, community_id: int, level: str = "detailed"
    ) -> Dict[str, Any]:
        """
        为指定社区生成摘要

        Args:
            community_id: 社区ID
            level: 摘要级别 ("brief", "detailed", "comprehensive")

        Returns:
            社区摘要结果
        """
        try:
            logger.info(f"开始为社区 {community_id} 生成摘要，级别: {level}")

            # 获取社区数据
            community_data = self._get_community_data(community_id)
            if not community_data["success"]:
                return community_data

            # 生成摘要
            summary = self._generate_summary_with_llm(community_data["data"], level)

            # 保存摘要
            self._save_summary_to_neo4j(community_id, summary)

            result = {
                "success": True,
                "community_id": community_id,
                "level": level,
                "summary": summary,
                "node_count": len(community_data["data"]["nodes"]),
                "edge_count": len(community_data["data"]["edges"]),
            }

            # 缓存摘要
            self.community_summaries[community_id] = result

            logger.info(f"社区 {community_id} 摘要生成完成")
            return result

        except Exception as e:
            logger.error(f"生成社区摘要失败: {e}")
            return {"success": False, "error": str(e)}

    def generate_all_communities_summary(
        self, level: str = "detailed"
    ) -> Dict[str, Any]:
        """为所有社区生成摘要"""
        try:
            logger.info(f"开始为所有社区生成摘要，级别: {level}")

            # 获取所有社区ID
            community_ids = self._get_all_community_ids()
            if not community_ids:
                return {"success": False, "error": "未找到任何社区"}

            summaries = {}
            failed_communities = []

            for community_id in community_ids:
                result = self.generate_community_summary(community_id, level)
                if result["success"]:
                    summaries[community_id] = result
                else:
                    failed_communities.append(community_id)

            return {
                "success": True,
                "total_communities": len(community_ids),
                "successful_summaries": len(summaries),
                "failed_communities": failed_communities,
                "summaries": summaries,
            }

        except Exception as e:
            logger.error(f"批量生成社区摘要失败: {e}")
            return {"success": False, "error": str(e)}

    def _get_community_data(self, community_id: int) -> Dict[str, Any]:
        """获取社区的详细数据"""
        try:
            if not self.neo4j_manager:
                return {"success": False, "error": "Neo4j管理器未初始化"}

            # 获取社区内的节点和关系
            query = """
            MATCH (n {community_id: $community_id})
            OPTIONAL MATCH (n)-[r]-(m {community_id: $community_id})
            RETURN n.name as node_name, labels(n) as node_labels,
                   n.properties as node_properties,
                   collect(DISTINCT {
                       target: m.name,
                       relation: type(r),
                       properties: r.properties
                   }) as relationships
            """

            result = self.neo4j_manager.execute_query(
                query, {"community_id": community_id}
            )

            nodes = []
            edges = []
            entities_by_type = {}
            relations_by_type = {}

            for record in result:
                node_name = record["node_name"]
                node_labels = record["node_labels"] or []
                node_properties = record["node_properties"] or {}
                relationships = record["relationships"] or []

                # 处理节点
                node_type = node_labels[0] if node_labels else "Unknown"
                if node_type not in entities_by_type:
                    entities_by_type[node_type] = []

                entities_by_type[node_type].append(
                    {"name": node_name, "properties": node_properties}
                )

                nodes.append(
                    {
                        "name": node_name,
                        "type": node_type,
                        "properties": node_properties,
                    }
                )

                # 处理关系
                for rel in relationships:
                    if rel["target"]:  # 确保目标节点存在
                        rel_type = rel["relation"]
                        if rel_type not in relations_by_type:
                            relations_by_type[rel_type] = []

                        relations_by_type[rel_type].append(
                            {
                                "source": node_name,
                                "target": rel["target"],
                                "properties": rel["properties"] or {},
                            }
                        )

                        edges.append(
                            {
                                "source": node_name,
                                "target": rel["target"],
                                "type": rel_type,
                                "properties": rel["properties"] or {},
                            }
                        )

            return {
                "success": True,
                "data": {
                    "community_id": community_id,
                    "nodes": nodes,
                    "edges": edges,
                    "entities_by_type": entities_by_type,
                    "relations_by_type": relations_by_type,
                    "stats": {
                        "total_nodes": len(nodes),
                        "total_edges": len(edges),
                        "entity_types": len(entities_by_type),
                        "relation_types": len(relations_by_type),
                    },
                },
            }

        except Exception as e:
            logger.error(f"获取社区数据失败: {e}")
            return {"success": False, "error": str(e)}

    def _generate_summary_with_llm(
        self, community_data: Dict[str, Any], level: str
    ) -> Dict[str, Any]:
        """使用LLM生成社区摘要"""
        try:
            # 构建提示词
            prompt = self._build_summary_prompt(community_data, level)

            # 调用Ollama生成摘要
            response = self.ollama_client.generate_response(prompt)

            if not response["success"]:
                raise Exception(f"LLM调用失败: {response.get('error', 'Unknown error')}")

            # 解析响应
            summary_text = response["response"]

            # 尝试解析为JSON，如果失败则作为纯文本处理
            try:
                summary_json = json.loads(summary_text)
                if isinstance(summary_json, dict):
                    return summary_json
            except json.JSONDecodeError:
                pass

            # 如果不是JSON格式，创建标准格式
            return {
                "title": f"社区 {community_data['community_id']} 摘要",
                "description": summary_text,
                "key_entities": list(community_data["entities_by_type"].keys()),
                "key_relations": list(community_data["relations_by_type"].keys()),
                "main_topics": self._extract_topics_from_text(summary_text),
                "level": level,
            }

        except Exception as e:
            logger.error(f"LLM生成摘要失败: {e}")
            # 返回基础摘要
            return self._generate_basic_summary(community_data, level)

    def _build_summary_prompt(self, community_data: Dict[str, Any], level: str) -> str:
        """构建摘要生成的提示词"""
        entities_info = []
        for entity_type, entities in community_data["entities_by_type"].items():
            entity_names = [e["name"] for e in entities[:5]]  # 限制数量
            entities_info.append(f"{entity_type}: {', '.join(entity_names)}")

        relations_info = []
        for relation_type, relations in community_data["relations_by_type"].items():
            rel_examples = [f"{r['source']}-{r['target']}" for r in relations[:3]]
            relations_info.append(f"{relation_type}: {', '.join(rel_examples)}")

        if level == "brief":
            prompt = f"""
请为以下知识图谱社区生成简要摘要：

实体类型和示例：
{chr(10).join(entities_info)}

关系类型和示例：
{chr(10).join(relations_info)}

请用1-2句话概括这个社区的主要内容和主题。
"""
        elif level == "detailed":
            prompt = f"""
请为以下知识图谱社区生成详细摘要：

社区统计：
- 节点数量: {community_data['stats']['total_nodes']}
- 关系数量: {community_data['stats']['total_edges']}
- 实体类型: {community_data['stats']['entity_types']}
- 关系类型: {community_data['stats']['relation_types']}

实体类型和示例：
{chr(10).join(entities_info)}

关系类型和示例：
{chr(10).join(relations_info)}

请生成包含以下内容的摘要：
1. 社区的主要主题和领域
2. 关键实体和它们的作用
3. 主要的关系模式
4. 这个社区在整个知识图谱中的可能作用

请用JSON格式返回，包含title, description, key_points等字段。
"""
        else:  # comprehensive
            prompt = f"""
请为以下知识图谱社区生成全面的分析摘要：

社区详细信息：
- 社区ID: {community_data['community_id']}
- 节点数量: {community_data['stats']['total_nodes']}
- 关系数量: {community_data['stats']['total_edges']}

实体详细信息：
{chr(10).join(entities_info)}

关系详细信息：
{chr(10).join(relations_info)}

请生成包含以下内容的全面分析：
1. 社区的核心主题和业务领域
2. 实体层次结构和重要性分析
3. 关系网络的模式和特征
4. 社区的功能和在知识图谱中的战略价值
5. 潜在的应用场景和用途

请用JSON格式返回详细的分析结果。
"""

        return prompt

    def _extract_topics_from_text(self, text: str) -> List[str]:
        """从文本中提取主题关键词"""
        # 简单的关键词提取，可以后续优化
        keywords = []
        common_words = {"的", "是", "在", "和", "与", "或", "但", "而", "等", "及"}

        words = text.replace("，", " ").replace("。", " ").replace("、", " ").split()
        for word in words:
            if len(word) > 1 and word not in common_words:
                keywords.append(word)

        return list(set(keywords))[:10]  # 返回前10个唯一关键词

    def _generate_basic_summary(
        self, community_data: Dict[str, Any], level: str
    ) -> Dict[str, Any]:
        """生成基础摘要（当LLM失败时的备选方案）"""
        entity_types = list(community_data["entities_by_type"].keys())
        relation_types = list(community_data["relations_by_type"].keys())

        description = f"这个社区包含 {community_data['stats']['total_nodes']} 个节点和 {community_data['stats']['total_edges']} 个关系。"
        description += f"主要实体类型包括：{', '.join(entity_types)}。"
        description += f"主要关系类型包括：{', '.join(relation_types)}。"

        return {
            "title": f"社区 {community_data['community_id']} 基础摘要",
            "description": description,
            "key_entities": entity_types,
            "key_relations": relation_types,
            "main_topics": entity_types + relation_types,
            "level": level,
            "generated_by": "basic_summarizer",
        }

    def _save_summary_to_neo4j(self, community_id: int, summary: Dict[str, Any]):
        """将摘要保存到Neo4j"""
        try:
            if not self.neo4j_manager:
                return

            # 创建或更新社区摘要节点
            query = """
            MERGE (cs:CommunitySummary {community_id: $community_id})
            SET cs.title = $title,
                cs.description = $description,
                cs.key_entities = $key_entities,
                cs.key_relations = $key_relations,
                cs.main_topics = $main_topics,
                cs.level = $level,
                cs.updated_at = datetime()
            """

            self.neo4j_manager.execute_query(
                query,
                {
                    "community_id": community_id,
                    "title": summary.get("title", ""),
                    "description": summary.get("description", ""),
                    "key_entities": summary.get("key_entities", []),
                    "key_relations": summary.get("key_relations", []),
                    "main_topics": summary.get("main_topics", []),
                    "level": summary.get("level", "detailed"),
                },
            )

            logger.info(f"社区 {community_id} 摘要已保存到Neo4j")

        except Exception as e:
            logger.error(f"保存摘要到Neo4j失败: {e}")

    def _get_all_community_ids(self) -> List[int]:
        """获取所有社区ID"""
        try:
            if not self.neo4j_manager:
                return []

            query = """
            MATCH (n)
            WHERE n.community_id IS NOT NULL
            RETURN DISTINCT n.community_id as community_id
            ORDER BY community_id
            """

            result = self.neo4j_manager.execute_query(query)
            return [record["community_id"] for record in result]

        except Exception as e:
            logger.error(f"获取社区ID列表失败: {e}")
            return []

    def get_community_summary(self, community_id: int) -> Dict[str, Any]:
        """获取指定社区的摘要"""
        try:
            # 先从缓存中查找
            if community_id in self.community_summaries:
                return self.community_summaries[community_id]

            # 从Neo4j中查找
            if self.neo4j_manager:
                query = """
                MATCH (cs:CommunitySummary {community_id: $community_id})
                RETURN cs.title as title, cs.description as description,
                       cs.key_entities as key_entities, cs.key_relations as key_relations,
                       cs.main_topics as main_topics, cs.level as level
                """

                result = self.neo4j_manager.execute_query(
                    query, {"community_id": community_id}
                )
                if result:
                    record = result[0]
                    return {
                        "success": True,
                        "community_id": community_id,
                        "summary": {
                            "title": record["title"],
                            "description": record["description"],
                            "key_entities": record["key_entities"],
                            "key_relations": record["key_relations"],
                            "main_topics": record["main_topics"],
                            "level": record["level"],
                        },
                    }

            return {"success": False, "error": "未找到社区摘要"}

        except Exception as e:
            logger.error(f"获取社区摘要失败: {e}")
            return {"success": False, "error": str(e)}
