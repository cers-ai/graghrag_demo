"""
GraphRAG问答服务
实现基于社区结构的增强检索生成
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from .community_detector import CommunityDetector
from .community_summarizer import CommunitySummarizer
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class GraphRAGQA:
    """GraphRAG问答系统 - 基于社区结构的检索增强生成"""

    def __init__(self, ollama_client: OllamaClient, neo4j_manager=None):
        """初始化GraphRAG问答系统"""
        self.ollama_client = ollama_client
        self.neo4j_manager = neo4j_manager
        self.community_detector = CommunityDetector(neo4j_manager)
        self.community_summarizer = CommunitySummarizer(ollama_client, neo4j_manager)

    def answer_question(
        self, question: str, search_strategy: str = "community_first"
    ) -> Dict[str, Any]:
        """
        基于GraphRAG方法回答问题

        Args:
            question: 用户问题
            search_strategy: 搜索策略 ("community_first", "global_first", "hybrid")

        Returns:
            问答结果
        """
        try:
            logger.info(f"开始GraphRAG问答，问题: {question}, 策略: {search_strategy}")

            # 分析问题，确定相关社区
            relevant_communities = self._find_relevant_communities(question)

            # 根据策略执行搜索
            if search_strategy == "community_first":
                answer = self._community_first_search(question, relevant_communities)
            elif search_strategy == "global_first":
                answer = self._global_first_search(question)
            else:  # hybrid
                answer = self._hybrid_search(question, relevant_communities)

            result = {
                "success": True,
                "question": question,
                "answer": answer["response"],
                "strategy": search_strategy,
                "relevant_communities": relevant_communities,
                "sources": answer.get("sources", []),
                "confidence": answer.get("confidence", 0.5),
            }

            logger.info("GraphRAG问答完成")
            return result

        except Exception as e:
            logger.error(f"GraphRAG问答失败: {e}")
            return {"success": False, "error": str(e)}

    def _find_relevant_communities(self, question: str) -> List[Dict[str, Any]]:
        """根据问题找到相关社区"""
        try:
            # 获取所有社区摘要
            all_summaries = self._get_all_community_summaries()

            if not all_summaries:
                return []

            # 使用LLM分析问题与社区的相关性
            relevance_prompt = f"""
问题: {question}

以下是知识图谱中的社区摘要信息：
{self._format_communities_for_prompt(all_summaries)}

请分析这个问题与哪些社区最相关，按相关性从高到低排序。
请返回JSON格式，包含community_id和relevance_score（0-1之间）。

示例格式：
[
    {{"community_id": 1, "relevance_score": 0.9, "reason": "直接相关"}},
    {{"community_id": 2, "relevance_score": 0.6, "reason": "部分相关"}}
]
"""

            response = self.ollama_client.generate_response(relevance_prompt)

            if response["success"]:
                try:
                    relevance_data = json.loads(response["response"])
                    # 过滤相关性分数大于0.3的社区
                    relevant = [
                        item
                        for item in relevance_data
                        if item.get("relevance_score", 0) > 0.3
                    ]
                    return sorted(
                        relevant,
                        key=lambda x: x.get("relevance_score", 0),
                        reverse=True,
                    )
                except json.JSONDecodeError:
                    logger.warning("无法解析社区相关性分析结果")

            # 如果LLM分析失败，使用关键词匹配
            return self._keyword_based_community_matching(question, all_summaries)

        except Exception as e:
            logger.error(f"查找相关社区失败: {e}")
            return []

    def _community_first_search(
        self, question: str, relevant_communities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """社区优先搜索策略"""
        try:
            if not relevant_communities:
                # 如果没有相关社区，回退到全局搜索
                return self._global_first_search(question)

            # 获取最相关社区的详细信息
            top_communities = relevant_communities[:3]  # 取前3个最相关的社区
            community_contexts = []

            for comm in top_communities:
                community_id = comm["community_id"]

                # 获取社区摘要
                summary = self.community_summarizer.get_community_summary(community_id)
                if summary["success"]:
                    community_contexts.append(
                        {
                            "community_id": community_id,
                            "summary": summary["summary"],
                            "relevance": comm.get("relevance_score", 0),
                        }
                    )

                # 获取社区子图
                subgraph = self.community_detector.get_community_subgraph(community_id)
                if subgraph["success"]:
                    community_contexts[-1]["subgraph"] = subgraph

            # 基于社区上下文生成答案
            answer_prompt = self._build_community_answer_prompt(
                question, community_contexts
            )
            response = self.ollama_client.generate_response(answer_prompt)

            if response["success"]:
                return {
                    "response": response["response"],
                    "sources": [
                        f"社区 {ctx['community_id']}" for ctx in community_contexts
                    ],
                    "confidence": 0.8,
                    "method": "community_first",
                }
            else:
                raise Exception("LLM生成答案失败")

        except Exception as e:
            logger.error(f"社区优先搜索失败: {e}")
            # 回退到全局搜索
            return self._global_first_search(question)

    def _global_first_search(self, question: str) -> Dict[str, Any]:
        """全局优先搜索策略"""
        try:
            # 在整个图中搜索相关信息
            search_results = self._search_global_graph(question)

            # 基于全局搜索结果生成答案
            answer_prompt = f"""
基于以下知识图谱信息回答问题：

问题: {question}

相关信息：
{self._format_search_results(search_results)}

请基于提供的信息给出准确、详细的答案。如果信息不足，请说明。
"""

            response = self.ollama_client.generate_response(answer_prompt)

            if response["success"]:
                return {
                    "response": response["response"],
                    "sources": ["全局图搜索"],
                    "confidence": 0.6,
                    "method": "global_first",
                }
            else:
                raise Exception("LLM生成答案失败")

        except Exception as e:
            logger.error(f"全局搜索失败: {e}")
            return {
                "response": "抱歉，无法找到相关信息来回答您的问题。",
                "sources": [],
                "confidence": 0.1,
                "method": "fallback",
            }

    def _hybrid_search(
        self, question: str, relevant_communities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """混合搜索策略"""
        try:
            # 结合社区搜索和全局搜索
            community_results = []
            if relevant_communities:
                community_answer = self._community_first_search(
                    question, relevant_communities
                )
                community_results.append(community_answer)

            global_answer = self._global_first_search(question)

            # 综合两种搜索结果
            synthesis_prompt = f"""
问题: {question}

社区搜索结果:
{community_results[0]["response"] if community_results else "无社区相关信息"}

全局搜索结果:
{global_answer["response"]}

请综合以上信息，给出最准确、最完整的答案。
"""

            response = self.ollama_client.generate_response(synthesis_prompt)

            if response["success"]:
                sources = []
                if community_results:
                    sources.extend(community_results[0]["sources"])
                sources.extend(global_answer["sources"])

                return {
                    "response": response["response"],
                    "sources": list(set(sources)),
                    "confidence": 0.7,
                    "method": "hybrid",
                }
            else:
                # 如果综合失败，返回最好的单一结果
                if (
                    community_results
                    and community_results[0]["confidence"] > global_answer["confidence"]
                ):
                    return community_results[0]
                else:
                    return global_answer

        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return self._global_first_search(question)

    def _search_global_graph(self, question: str) -> List[Dict[str, Any]]:
        """在全局图中搜索相关信息"""
        try:
            if not self.neo4j_manager:
                return []

            # 提取问题中的关键词
            keywords = self._extract_keywords_from_question(question)

            # 构建搜索查询
            search_queries = []

            # 按实体名称搜索
            for keyword in keywords:
                query = """
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower($keyword)
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN n.name as entity, labels(n) as entity_type,
                       collect({target: m.name, relation: type(r)}) as connections
                LIMIT 5
                """
                result = self.neo4j_manager.execute_query(query, {"keyword": keyword})
                search_queries.extend(result)

            return search_queries

        except Exception as e:
            logger.error(f"全局图搜索失败: {e}")
            return []

    def _extract_keywords_from_question(self, question: str) -> List[str]:
        """从问题中提取关键词"""
        # 简单的关键词提取，可以后续优化
        stop_words = {"什么", "如何", "为什么", "哪里", "谁", "是", "的", "了", "在", "和", "与"}
        words = question.replace("？", "").replace("?", "").replace("，", " ").split()
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        return keywords[:5]  # 返回前5个关键词

    def _get_all_community_summaries(self) -> List[Dict[str, Any]]:
        """获取所有社区摘要"""
        try:
            if not self.neo4j_manager:
                return []

            query = """
            MATCH (cs:CommunitySummary)
            RETURN cs.community_id as community_id, cs.title as title,
                   cs.description as description, cs.key_entities as key_entities,
                   cs.key_relations as key_relations, cs.main_topics as main_topics
            """

            result = self.neo4j_manager.execute_query(query)
            return [dict(record) for record in result]

        except Exception as e:
            logger.error(f"获取社区摘要失败: {e}")
            return []

    def _keyword_based_community_matching(
        self, question: str, summaries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """基于关键词的社区匹配"""
        keywords = self._extract_keywords_from_question(question)
        relevant_communities = []

        for summary in summaries:
            score = 0
            description = summary.get("description", "").lower()
            topics = summary.get("main_topics", [])

            for keyword in keywords:
                if keyword.lower() in description:
                    score += 0.3
                if keyword in topics:
                    score += 0.5

            if score > 0:
                relevant_communities.append(
                    {
                        "community_id": summary["community_id"],
                        "relevance_score": min(score, 1.0),
                        "reason": "关键词匹配",
                    }
                )

        return sorted(
            relevant_communities, key=lambda x: x["relevance_score"], reverse=True
        )

    def _format_communities_for_prompt(self, summaries: List[Dict[str, Any]]) -> str:
        """格式化社区信息用于提示词"""
        formatted = []
        for summary in summaries:
            formatted.append(
                f"""
社区 {summary['community_id']}:
标题: {summary.get('title', '未知')}
描述: {summary.get('description', '无描述')}
主要主题: {', '.join(summary.get('main_topics', []))}
"""
            )
        return "\n".join(formatted)

    def _build_community_answer_prompt(
        self, question: str, community_contexts: List[Dict[str, Any]]
    ) -> str:
        """构建基于社区上下文的答案提示词"""
        context_info = []

        for ctx in community_contexts:
            info = f"""
社区 {ctx['community_id']} (相关性: {ctx['relevance']:.2f}):
摘要: {ctx['summary'].get('description', '无描述')}
关键实体: {', '.join(ctx['summary'].get('key_entities', []))}
关键关系: {', '.join(ctx['summary'].get('key_relations', []))}
"""
            if "subgraph" in ctx:
                subgraph = ctx["subgraph"]
                info += f"节点数: {len(subgraph.get('nodes', []))}, 关系数: {len(subgraph.get('edges', []))}\n"

            context_info.append(info)

        return f"""
基于以下社区信息回答问题：

问题: {question}

相关社区信息:
{chr(10).join(context_info)}

请基于这些社区信息给出准确、详细的答案。重点关注最相关的社区信息。
"""

    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化搜索结果"""
        formatted = []
        for result in results:
            entity = result.get("entity", "未知实体")
            entity_type = result.get("entity_type", [])
            connections = result.get("connections", [])

            info = f"实体: {entity} (类型: {', '.join(entity_type)})"
            if connections:
                conn_info = [
                    f"{c.get('target', '')}-{c.get('relation', '')}"
                    for c in connections
                    if c.get("target")
                ]
                info += f"\n关系: {', '.join(conn_info[:5])}"  # 限制显示数量

            formatted.append(info)

        return "\n\n".join(formatted)
