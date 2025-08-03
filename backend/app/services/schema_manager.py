"""
Schema管理服务模块
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class EntitySchema:
    """实体Schema定义"""
    name: str
    description: str
    properties: Dict[str, Dict[str, Any]]
    required_properties: Set[str]


@dataclass
class RelationSchema:
    """关系Schema定义"""
    name: str
    description: str
    source: str
    target: str
    properties: Dict[str, Dict[str, Any]]


@dataclass
class KnowledgeGraphSchema:
    """知识图谱Schema"""
    version: str
    description: str
    entities: Dict[str, EntitySchema]
    relations: Dict[str, RelationSchema]
    load_time: datetime
    file_path: str


class SchemaValidationError(Exception):
    """Schema验证错误"""
    pass


class SchemaManager:
    """Schema管理器"""

    def __init__(self, schema_file: str = "config/schema.yaml"):
        """
        初始化Schema管理器

        Args:
            schema_file: Schema文件路径
        """
        self.schema_file = Path(schema_file)
        self.schema: Optional[KnowledgeGraphSchema] = None
        self._file_mtime: Optional[float] = None

        logger.info(f"Schema管理器初始化完成，Schema文件: {self.schema_file}")

    def load_schema(self, force_reload: bool = False) -> KnowledgeGraphSchema:
        """
        加载Schema文件

        Args:
            force_reload: 是否强制重新加载

        Returns:
            KnowledgeGraphSchema: 加载的Schema

        Raises:
            SchemaValidationError: Schema验证失败
            FileNotFoundError: Schema文件不存在
        """
        if not self.schema_file.exists():
            raise FileNotFoundError(f"Schema文件不存在: {self.schema_file}")

        current_mtime = self.schema_file.stat().st_mtime

        # 检查是否需要重新加载
        if (not force_reload and
            self.schema is not None and
            self._file_mtime == current_mtime):
            logger.debug("Schema文件未修改，使用缓存的Schema")
            return self.schema

        logger.info(f"加载Schema文件: {self.schema_file}")

        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                schema_data = yaml.safe_load(f)

            # 验证Schema格式
            self._validate_schema_format(schema_data)

            # 解析Schema
            schema = self._parse_schema(schema_data)

            # 验证Schema逻辑
            self._validate_schema_logic(schema)

            self.schema = schema
            self._file_mtime = current_mtime

            logger.info(f"Schema加载成功: {schema.version} - {schema.description}")
            logger.info(f"实体类型: {len(schema.entities)} 个")
            logger.info(f"关系类型: {len(schema.relations)} 个")

            return schema

        except yaml.YAMLError as e:
            raise SchemaValidationError(f"Schema文件YAML格式错误: {e}")
        except Exception as e:
            raise SchemaValidationError(f"Schema加载失败: {e}")

    def _validate_schema_format(self, schema_data: Dict[str, Any]):
        """验证Schema文件格式"""
        required_fields = ['version', 'description', 'entities', 'relations']

        for field in required_fields:
            if field not in schema_data:
                raise SchemaValidationError(f"Schema缺少必需字段: {field}")

        if not isinstance(schema_data['entities'], dict):
            raise SchemaValidationError("entities字段必须是字典类型")

        if not isinstance(schema_data['relations'], dict):
            raise SchemaValidationError("relations字段必须是字典类型")

    def _parse_schema(self, schema_data: Dict[str, Any]) -> KnowledgeGraphSchema:
        """解析Schema数据"""
        # 解析实体
        entities = {}
        for entity_name, entity_config in schema_data['entities'].items():
            entity = self._parse_entity(entity_name, entity_config)
            entities[entity_name] = entity

        # 解析关系
        relations = {}
        for relation_name, relation_config in schema_data['relations'].items():
            relation = self._parse_relation(relation_name, relation_config)
            relations[relation_name] = relation

        return KnowledgeGraphSchema(
            version=schema_data['version'],
            description=schema_data['description'],
            entities=entities,
            relations=relations,
            load_time=datetime.now(),
            file_path=str(self.schema_file)
        )

    def _parse_entity(self, name: str, config: Dict[str, Any]) -> EntitySchema:
        """解析实体配置"""
        if 'description' not in config:
            raise SchemaValidationError(f"实体 {name} 缺少description字段")

        properties = config.get('properties', {})
        required_properties = set()

        # 解析属性
        for prop_name, prop_config in properties.items():
            if not isinstance(prop_config, dict):
                raise SchemaValidationError(f"实体 {name} 的属性 {prop_name} 配置必须是字典")

            if 'type' not in prop_config:
                raise SchemaValidationError(f"实体 {name} 的属性 {prop_name} 缺少type字段")

            if prop_config.get('required', False):
                required_properties.add(prop_name)

        return EntitySchema(
            name=name,
            description=config['description'],
            properties=properties,
            required_properties=required_properties
        )

    def _parse_relation(self, name: str, config: Dict[str, Any]) -> RelationSchema:
        """解析关系配置"""
        required_fields = ['description', 'source', 'target']

        for field in required_fields:
            if field not in config:
                raise SchemaValidationError(f"关系 {name} 缺少{field}字段")

        properties = config.get('properties', {})

        # 验证属性配置
        for prop_name, prop_config in properties.items():
            if not isinstance(prop_config, dict):
                raise SchemaValidationError(f"关系 {name} 的属性 {prop_name} 配置必须是字典")

            if 'type' not in prop_config:
                raise SchemaValidationError(f"关系 {name} 的属性 {prop_name} 缺少type字段")

        return RelationSchema(
            name=name,
            description=config['description'],
            source=config['source'],
            target=config['target'],
            properties=properties
        )

    def _validate_schema_logic(self, schema: KnowledgeGraphSchema):
        """验证Schema逻辑一致性"""
        # 检查关系的源和目标实体是否存在
        for relation_name, relation in schema.relations.items():
            if relation.source not in schema.entities:
                raise SchemaValidationError(
                    f"关系 {relation_name} 的源实体 {relation.source} 未定义"
                )

            if relation.target not in schema.entities:
                raise SchemaValidationError(
                    f"关系 {relation_name} 的目标实体 {relation.target} 未定义"
                )

        # 检查是否有循环依赖（可选）
        # 这里可以添加更多的逻辑验证

    def get_schema(self) -> Optional[KnowledgeGraphSchema]:
        """获取当前Schema"""
        return self.schema

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
        """获取指定实体的Schema"""
        if self.schema and entity_name in self.schema.entities:
            return self.schema.entities[entity_name]
        return None

    def get_relation_schema(self, relation_name: str) -> Optional[RelationSchema]:
        """获取指定关系的Schema"""
        if self.schema and relation_name in self.schema.relations:
            return self.schema.relations[relation_name]
        return None

    def get_entity_names(self) -> List[str]:
        """获取所有实体名称"""
        if self.schema:
            return list(self.schema.entities.keys())
        return []

    def get_relation_names(self) -> List[str]:
        """获取所有关系名称"""
        if self.schema:
            return list(self.schema.relations.keys())
        return []

    def validate_entity_data(self, entity_name: str, data: Dict[str, Any]) -> List[str]:
        """
        验证实体数据

        Args:
            entity_name: 实体名称
            data: 实体数据

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        entity_schema = self.get_entity_schema(entity_name)
        if not entity_schema:
            errors.append(f"未知的实体类型: {entity_name}")
            return errors

        # 检查必需属性
        for required_prop in entity_schema.required_properties:
            if required_prop not in data or data[required_prop] is None:
                errors.append(f"缺少必需属性: {required_prop}")

        # 检查属性类型（简单验证）
        for prop_name, prop_value in data.items():
            if prop_name in entity_schema.properties:
                prop_config = entity_schema.properties[prop_name]
                expected_type = prop_config.get('type', 'string')

                if not self._validate_property_type(prop_value, expected_type):
                    errors.append(f"属性 {prop_name} 类型错误，期望: {expected_type}")

        return errors

    def validate_relation_data(self, relation_name: str, data: Dict[str, Any]) -> List[str]:
        """
        验证关系数据

        Args:
            relation_name: 关系名称
            data: 关系数据

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        relation_schema = self.get_relation_schema(relation_name)
        if not relation_schema:
            errors.append(f"未知的关系类型: {relation_name}")
            return errors

        # 验证关系属性
        for prop_name, prop_value in data.items():
            if prop_name in relation_schema.properties:
                prop_config = relation_schema.properties[prop_name]
                expected_type = prop_config.get('type', 'string')

                if not self._validate_property_type(prop_value, expected_type):
                    errors.append(f"关系属性 {prop_name} 类型错误，期望: {expected_type}")

        return errors

    def _validate_property_type(self, value: Any, expected_type: str) -> bool:
        """验证属性类型"""
        if value is None:
            return True

        type_mapping = {
            'string': str,
            'integer': int,
            'float': (int, float),
            'boolean': bool,
            'date': str,  # 简化处理，实际可以更严格
            'datetime': str
        }

        expected_python_type = type_mapping.get(expected_type, str)
        return isinstance(value, expected_python_type)

    def get_schema_summary(self) -> Dict[str, Any]:
        """获取Schema摘要信息"""
        if not self.schema:
            return {}

        return {
            'version': self.schema.version,
            'description': self.schema.description,
            'entities_count': len(self.schema.entities),
            'relations_count': len(self.schema.relations),
            'entity_names': list(self.schema.entities.keys()),
            'relation_names': list(self.schema.relations.keys()),
            'load_time': self.schema.load_time,
            'file_path': self.schema.file_path
        }

    def export_schema_json(self) -> Dict[str, Any]:
        """导出Schema为JSON格式"""
        if not self.schema:
            return {}

        entities_json = {}
        for name, entity in self.schema.entities.items():
            entities_json[name] = {
                'description': entity.description,
                'properties': entity.properties,
                'required_properties': list(entity.required_properties)
            }

        relations_json = {}
        for name, relation in self.schema.relations.items():
            relations_json[name] = {
                'description': relation.description,
                'source': relation.source,
                'target': relation.target,
                'properties': relation.properties
            }

        return {
            'version': self.schema.version,
            'description': self.schema.description,
            'entities': entities_json,
            'relations': relations_json,
            'metadata': {
                'load_time': self.schema.load_time.isoformat(),
                'file_path': self.schema.file_path
            }
        }

    def reload_if_changed(self) -> bool:
        """如果文件已修改则重新加载Schema"""
        if not self.schema_file.exists():
            return False

        current_mtime = self.schema_file.stat().st_mtime

        if self._file_mtime != current_mtime:
            try:
                self.load_schema(force_reload=True)
                return True
            except Exception as e:
                logger.error(f"重新加载Schema失败: {e}")
                return False

        return False
