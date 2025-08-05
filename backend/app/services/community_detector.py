"""
社区检测服务
实现GraphRAG核心功能：图社区检测算法
"""

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import community as community_louvain
import networkx as nx
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class CommunityDetector:
    """社区检测器 - GraphRAG核心组件"""

    def __init__(self, neo4j_manager=None):
        """初始化社区检测器"""
        self.neo4j_manager = neo4j_manager
        self.communities = {}
        self.community_stats = {}

    def detect_communities(
        self, algorithm: str = "louvain", resolution: float = 1.0
    ) -> Dict[str, Any]:
        """
        检测图中的社区结构

        Args:
            algorithm: 社区检测算法 ("louvain", "label_propagation", "leiden")
            resolution: 分辨率参数，控制社区大小

        Returns:
            社区检测结果
        """
        try:
            logger.info(f"开始社区检测，算法: {algorithm}, 分辨率: {resolution}")

            # 从Neo4j获取图数据
            graph_data = self._get_graph_from_neo4j()
            if not graph_data:
                return {"success": False, "error": "无法获取图数据"}

            # 构建NetworkX图
            G = self._build_networkx_graph(graph_data)
            if G.number_of_nodes() == 0:
                return {"success": False, "error": "图中没有节点"}

            # 执行社区检测
            communities = self._run_community_detection(G, algorithm, resolution)

            # 计算社区统计信息
            stats = self._calculate_community_stats(G, communities)

            # 保存社区信息到Neo4j
            self._save_communities_to_neo4j(communities)

            # 存储结果
            self.communities = communities
            self.community_stats = stats

            result = {
                "success": True,
                "algorithm": algorithm,
                "resolution": resolution,
                "total_communities": len(set(communities.values())),
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "communities": communities,
                "stats": stats,
                "modularity": self._calculate_modularity(G, communities),
            }

            logger.info(f"社区检测完成，发现 {len(set(communities.values()))} 个社区")
            return result

        except Exception as e:
            logger.error(f"社区检测失败: {e}")
            return {"success": False, "error": str(e)}

    def _get_graph_from_neo4j(self) -> Optional[Dict[str, Any]]:
        """从Neo4j获取图数据"""
        try:
            if not self.neo4j_manager:
                return None

            # 获取所有节点和关系
            query = """
            MATCH (n)-[r]->(m)
            RETURN n.name as source, m.name as target,
                   type(r) as relation_type, labels(n) as source_labels,
                   labels(m) as target_labels, r.weight as weight
            """

            result = self.neo4j_manager.execute_query(query)

            nodes = set()
            edges = []

            for record in result:
                source = record["source"]
                target = record["target"]
                weight = record.get("weight", 1.0)

                nodes.add(source)
                nodes.add(target)
                edges.append(
                    {
                        "source": source,
                        "target": target,
                        "weight": weight,
                        "relation_type": record["relation_type"],
                    }
                )

            return {"nodes": list(nodes), "edges": edges}

        except Exception as e:
            logger.error(f"从Neo4j获取图数据失败: {e}")
            return None

    def _build_networkx_graph(self, graph_data: Dict[str, Any]) -> nx.Graph:
        """构建NetworkX图"""
        G = nx.Graph()

        # 添加节点
        for node in graph_data["nodes"]:
            G.add_node(node)

        # 添加边
        for edge in graph_data["edges"]:
            weight = edge.get("weight", 1.0)
            G.add_edge(edge["source"], edge["target"], weight=weight)

        return G

    def _run_community_detection(
        self, G: nx.Graph, algorithm: str, resolution: float
    ) -> Dict[str, int]:
        """执行社区检测算法"""
        if algorithm == "louvain":
            return community_louvain.best_partition(G, resolution=resolution)
        elif algorithm == "label_propagation":
            communities = nx.algorithms.community.label_propagation_communities(G)
            return self._communities_to_dict(communities)
        elif algorithm == "leiden":
            # 如果有leiden算法库，可以在这里实现
            # 暂时使用louvain作为替代
            return community_louvain.best_partition(G, resolution=resolution)
        else:
            raise ValueError(f"不支持的算法: {algorithm}")

    def _communities_to_dict(self, communities) -> Dict[str, int]:
        """将社区列表转换为字典格式"""
        result = {}
        for i, community in enumerate(communities):
            for node in community:
                result[node] = i
        return result

    def _calculate_community_stats(
        self, G: nx.Graph, communities: Dict[str, int]
    ) -> Dict[str, Any]:
        """计算社区统计信息"""
        stats = defaultdict(
            lambda: {
                "size": 0,
                "nodes": [],
                "internal_edges": 0,
                "external_edges": 0,
                "density": 0.0,
            }
        )

        # 按社区分组节点
        for node, community_id in communities.items():
            stats[community_id]["size"] += 1
            stats[community_id]["nodes"].append(node)

        # 计算边的分布
        for edge in G.edges():
            source, target = edge
            source_community = communities.get(source)
            target_community = communities.get(target)

            if source_community == target_community:
                stats[source_community]["internal_edges"] += 1
            else:
                stats[source_community]["external_edges"] += 1
                stats[target_community]["external_edges"] += 1

        # 计算密度
        for community_id, stat in stats.items():
            size = stat["size"]
            if size > 1:
                max_edges = size * (size - 1) / 2
                stat["density"] = (
                    stat["internal_edges"] / max_edges if max_edges > 0 else 0
                )

        return dict(stats)

    def _calculate_modularity(self, G: nx.Graph, communities: Dict[str, int]) -> float:
        """计算模块度"""
        try:
            # 将社区字典转换为社区列表
            community_sets = defaultdict(set)
            for node, community_id in communities.items():
                community_sets[community_id].add(node)

            community_list = list(community_sets.values())
            return nx.algorithms.community.modularity(G, community_list)
        except Exception as e:
            logger.warning(f"计算模块度失败: {e}")
            return 0.0

    def _save_communities_to_neo4j(self, communities: Dict[str, int]):
        """将社区信息保存到Neo4j"""
        try:
            if not self.neo4j_manager:
                return

            # 为每个节点添加社区标签
            for node, community_id in communities.items():
                query = """
                MATCH (n {name: $node_name})
                SET n.community_id = $community_id
                """
                self.neo4j_manager.execute_query(
                    query, {"node_name": node, "community_id": community_id}
                )

            logger.info("社区信息已保存到Neo4j")

        except Exception as e:
            logger.error(f"保存社区信息到Neo4j失败: {e}")

    def get_community_nodes(self, community_id: int) -> List[str]:
        """获取指定社区的所有节点"""
        if not self.communities:
            return []

        return [node for node, cid in self.communities.items() if cid == community_id]

    def get_community_subgraph(self, community_id: int) -> Dict[str, Any]:
        """获取指定社区的子图"""
        try:
            if not self.neo4j_manager:
                return {"success": False, "error": "Neo4j管理器未初始化"}

            # 获取社区内的所有节点和关系
            query = """
            MATCH (n {community_id: $community_id})-[r]-(m {community_id: $community_id})
            RETURN n.name as source, m.name as target,
                   type(r) as relation_type, labels(n) as source_labels,
                   labels(m) as target_labels
            """

            result = self.neo4j_manager.execute_query(
                query, {"community_id": community_id}
            )

            nodes = set()
            edges = []

            for record in result:
                source = record["source"]
                target = record["target"]
                nodes.add(source)
                nodes.add(target)
                edges.append(
                    {
                        "source": source,
                        "target": target,
                        "relation_type": record["relation_type"],
                    }
                )

            return {
                "success": True,
                "community_id": community_id,
                "nodes": list(nodes),
                "edges": edges,
                "size": len(nodes),
            }

        except Exception as e:
            logger.error(f"获取社区子图失败: {e}")
            return {"success": False, "error": str(e)}

    def get_all_communities_summary(self) -> Dict[str, Any]:
        """获取所有社区的摘要信息"""
        if not self.community_stats:
            return {"success": False, "error": "未找到社区统计信息"}

        summary = {"total_communities": len(self.community_stats), "communities": []}

        for community_id, stats in self.community_stats.items():
            summary["communities"].append(
                {
                    "id": community_id,
                    "size": stats["size"],
                    "density": round(stats["density"], 3),
                    "internal_edges": stats["internal_edges"],
                    "external_edges": stats["external_edges"],
                    "nodes": stats["nodes"][:5],  # 只显示前5个节点
                }
            )

        # 按社区大小排序
        summary["communities"].sort(key=lambda x: x["size"], reverse=True)

        return {"success": True, "data": summary}
