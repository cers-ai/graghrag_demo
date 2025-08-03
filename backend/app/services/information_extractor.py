"""
信息抽取服务模块
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from .schema_manager import SchemaManager, KnowledgeGraphSchema
from .ollama_client import OllamaClient, ModelResponse


@dataclass
class ExtractedEntity:
    """抽取的实体"""
    type: str
    name: str
    properties: Dict[str, Any]
    confidence: float = 1.0
    source_text: str = ""


@dataclass
class ExtractedRelation:
    """抽取的关系"""
    type: str
    source: str
    target: str
    properties: Dict[str, Any]
    confidence: float = 1.0
    source_text: str = ""


@dataclass
class ExtractionResult:
    """抽取结果"""
    entities: List[ExtractedEntity]
    relations: List[ExtractedRelation]
    source_text: str
    extraction_time: datetime
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = None


class InformationExtractor:
    """信息抽取器"""

    def __init__(self,
                 schema_manager: SchemaManager,
                 ollama_client: OllamaClient,
                 chunk_size: int = 2000,
                 chunk_overlap: int = 200):
        """
        初始化信息抽取器

        Args:
            schema_manager: Schema管理器
            ollama_client: Ollama客户端
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠大小
        """
        self.schema_manager = schema_manager
        self.ollama_client = ollama_client
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        logger.info("信息抽取器初始化完成")
        logger.info(f"文本分块大小: {chunk_size}")
        logger.info(f"分块重叠: {chunk_overlap}")

    def extract_from_text(self, text: str) -> ExtractionResult:
        """
        从文本中抽取信息

        Args:
            text: 输入文本

        Returns:
            ExtractionResult: 抽取结果
        """
        logger.info(f"开始信息抽取，文本长度: {len(text)}")

        start_time = datetime.now()

        try:
            # 获取Schema
            schema = self.schema_manager.get_schema()
            if not schema:
                return ExtractionResult(
                    entities=[],
                    relations=[],
                    source_text=text,
                    extraction_time=start_time,
                    success=False,
                    error_message="Schema未加载"
                )

            # 文本分块处理
            chunks = self._split_text(text)
            logger.info(f"文本分为 {len(chunks)} 个块")

            all_entities = []
            all_relations = []
            success_count = 0

            # 处理每个文本块
            for i, chunk in enumerate(chunks):
                logger.debug(f"处理第 {i+1}/{len(chunks)} 个文本块")

                chunk_result = self._extract_from_chunk(chunk, schema)

                if chunk_result.success:
                    all_entities.extend(chunk_result.entities)
                    all_relations.extend(chunk_result.relations)
                    success_count += 1
                else:
                    logger.warning(f"第 {i+1} 个文本块抽取失败: {chunk_result.error_message}")

            # 合并和去重
            merged_entities = self._merge_entities(all_entities)
            merged_relations = self._merge_relations(all_relations)

            end_time = datetime.now()

            # 检查是否有成功的抽取结果
            overall_success = success_count > 0

            logger.info(f"信息抽取完成: 实体 {len(merged_entities)} 个, 关系 {len(merged_relations)} 个")

            return ExtractionResult(
                entities=merged_entities,
                relations=merged_relations,
                source_text=text,
                extraction_time=end_time,
                success=overall_success,
                error_message="" if overall_success else "所有文本块抽取失败",
                metadata={
                    'chunks_count': len(chunks),
                    'success_chunks': success_count,
                    'processing_time': (end_time - start_time).total_seconds(),
                    'entities_before_merge': len(all_entities),
                    'relations_before_merge': len(all_relations)
                }
            )

        except Exception as e:
            logger.error(f"信息抽取失败: {e}")
            return ExtractionResult(
                entities=[],
                relations=[],
                source_text=text,
                extraction_time=datetime.now(),
                success=False,
                error_message=str(e)
            )

    def _split_text(self, text: str) -> List[str]:
        """将文本分块"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            # 尝试在句号、换行符等位置分割
            chunk_text = text[start:end]

            # 寻找最佳分割点
            split_points = [
                chunk_text.rfind('。'),
                chunk_text.rfind('\n'),
                chunk_text.rfind('！'),
                chunk_text.rfind('？'),
                chunk_text.rfind(';'),
                chunk_text.rfind('.')
            ]

            best_split = max([p for p in split_points if p > self.chunk_size // 2], default=-1)

            if best_split > 0:
                chunks.append(text[start:start + best_split + 1])
                start = start + best_split + 1 - self.chunk_overlap
            else:
                chunks.append(chunk_text)
                start = end - self.chunk_overlap

        return chunks

    def _extract_from_chunk(self, text: str, schema: KnowledgeGraphSchema) -> ExtractionResult:
        """从单个文本块抽取信息"""
        try:
            # 准备Schema信息
            schema_info = self._format_schema_for_prompt(schema)

            # 使用模板生成提示词
            response = self.ollama_client.generate_with_template(
                template_name="entity_extraction",
                variables={
                    "schema": schema_info,
                    "text": text
                },
                options={
                    "temperature": 0.1,  # 降低温度以获得更一致的结果
                    "num_predict": 1000
                }
            )

            if not response.success:
                return ExtractionResult(
                    entities=[],
                    relations=[],
                    source_text=text,
                    extraction_time=datetime.now(),
                    success=False,
                    error_message=f"模型调用失败: {response.error_message}"
                )

            # 解析模型响应
            entities, relations = self._parse_model_response(response.content, text)

            return ExtractionResult(
                entities=entities,
                relations=relations,
                source_text=text,
                extraction_time=datetime.now(),
                success=True
            )

        except Exception as e:
            return ExtractionResult(
                entities=[],
                relations=[],
                source_text=text,
                extraction_time=datetime.now(),
                success=False,
                error_message=str(e)
            )

    def _format_schema_for_prompt(self, schema: KnowledgeGraphSchema) -> str:
        """格式化Schema信息用于提示词"""
        schema_parts = []

        # 实体类型
        schema_parts.append("实体类型:")
        for entity_name, entity in schema.entities.items():
            props = []
            for prop_name, prop_config in entity.properties.items():
                required = "必需" if prop_name in entity.required_properties else "可选"
                props.append(f"{prop_name}({prop_config['type']}, {required})")

            schema_parts.append(f"- {entity_name}: {entity.description}")
            if props:
                schema_parts.append(f"  属性: {', '.join(props)}")

        # 关系类型
        schema_parts.append("\n关系类型:")
        for relation_name, relation in schema.relations.items():
            schema_parts.append(f"- {relation_name}: {relation.source} -> {relation.target}")
            schema_parts.append(f"  描述: {relation.description}")

        return "\n".join(schema_parts)

    def _parse_model_response(self, response: str, source_text: str) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        """解析模型响应"""
        entities = []
        relations = []

        try:
            # 尝试提取JSON内容
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有代码块，尝试直接解析
                json_str = response.strip()

            # 解析JSON
            data = json.loads(json_str)

            # 解析实体
            for entity_data in data.get('entities', []):
                entity = ExtractedEntity(
                    type=entity_data.get('type', ''),
                    name=entity_data.get('name', ''),
                    properties=entity_data.get('properties', {}),
                    confidence=entity_data.get('confidence', 1.0),
                    source_text=source_text
                )
                entities.append(entity)

            # 解析关系
            for relation_data in data.get('relations', []):
                relation = ExtractedRelation(
                    type=relation_data.get('type', ''),
                    source=relation_data.get('source', ''),
                    target=relation_data.get('target', ''),
                    properties=relation_data.get('properties', {}),
                    confidence=relation_data.get('confidence', 1.0),
                    source_text=source_text
                )
                relations.append(relation)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            logger.debug(f"原始响应: {response}")

            # 尝试简单的文本解析作为备选方案
            entities, relations = self._fallback_text_parsing(response, source_text)

        except Exception as e:
            logger.error(f"响应解析失败: {e}")

        return entities, relations

    def _fallback_text_parsing(self, response: str, source_text: str) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        """备选的文本解析方法"""
        entities = []
        relations = []

        # 简单的实体识别（基于常见模式）
        # 这里可以实现更复杂的文本解析逻辑

        logger.debug("使用备选文本解析方法")

        return entities, relations

    def _merge_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """合并重复的实体"""
        merged = {}

        for entity in entities:
            key = (entity.type, entity.name.lower())

            if key in merged:
                # 合并属性，保留置信度更高的
                existing = merged[key]
                if entity.confidence > existing.confidence:
                    existing.properties.update(entity.properties)
                    existing.confidence = entity.confidence
                else:
                    entity.properties.update(existing.properties)
                    merged[key] = entity
            else:
                merged[key] = entity

        return list(merged.values())

    def _merge_relations(self, relations: List[ExtractedRelation]) -> List[ExtractedRelation]:
        """合并重复的关系"""
        merged = {}

        for relation in relations:
            key = (relation.type, relation.source.lower(), relation.target.lower())

            if key in merged:
                # 合并属性，保留置信度更高的
                existing = merged[key]
                if relation.confidence > existing.confidence:
                    existing.properties.update(relation.properties)
                    existing.confidence = relation.confidence
                else:
                    relation.properties.update(existing.properties)
                    merged[key] = relation
            else:
                merged[key] = relation

        return list(merged.values())

    def validate_extraction_result(self, result: ExtractionResult) -> List[str]:
        """验证抽取结果"""
        errors = []

        schema = self.schema_manager.get_schema()
        if not schema:
            errors.append("Schema未加载，无法验证")
            return errors

        # 验证实体
        for entity in result.entities:
            entity_errors = self.schema_manager.validate_entity_data(
                entity.type,
                {"name": entity.name, **entity.properties}
            )
            errors.extend([f"实体 {entity.name}: {error}" for error in entity_errors])

        # 验证关系
        for relation in result.relations:
            relation_errors = self.schema_manager.validate_relation_data(
                relation.type,
                relation.properties
            )
            errors.extend([f"关系 {relation.type}: {error}" for error in relation_errors])

        return errors

    def get_extraction_stats(self, result: ExtractionResult) -> Dict[str, Any]:
        """获取抽取统计信息"""
        entity_types = {}
        relation_types = {}

        for entity in result.entities:
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1

        for relation in result.relations:
            relation_types[relation.type] = relation_types.get(relation.type, 0) + 1

        return {
            'total_entities': len(result.entities),
            'total_relations': len(result.relations),
            'entity_types': entity_types,
            'relation_types': relation_types,
            'success': result.success,
            'extraction_time': result.extraction_time,
            'metadata': result.metadata or {}
        }
