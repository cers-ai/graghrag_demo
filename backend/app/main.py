"""
FastAPI主应用程序
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .services.community_detector import CommunityDetector
from .services.community_summarizer import CommunitySummarizer
from .services.document_parser import DocumentParser
from .services.document_scanner import DocumentScanner
from .services.graphrag_qa import GraphRAGQA
from .services.information_extractor import InformationExtractor
from .services.neo4j_manager import Neo4jManager
from .services.ollama_client import OllamaClient
from .services.schema_manager import SchemaManager

# 创建FastAPI应用
app = FastAPI(
    title="GraphRAG轻量化演示系统", description="展示GraphRAG技术的轻量化演示平台", version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
document_scanner = None
document_parser = None
schema_manager = None
ollama_client = None
information_extractor = None
neo4j_manager = None
community_detector = None
community_summarizer = None
graphrag_qa = None


# 请求/响应模型
class DocumentScanRequest(BaseModel):
    directory: str
    file_types: List[str] = [".docx", ".xlsx"]


class ExtractionRequest(BaseModel):
    text: str
    chunk_size: int = 2000
    chunk_overlap: int = 200


class QueryRequest(BaseModel):
    query: str
    parameters: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    entity_type: Optional[str] = None
    name_pattern: Optional[str] = None
    limit: int = 100


# 响应模型
class StatusResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime


class DocumentInfo(BaseModel):
    file_path: str
    title: str
    file_type: str
    size: int
    modified_time: datetime


class ExtractionResponse(BaseModel):
    success: bool
    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    stats: Dict[str, Any]
    error_message: str = ""


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global document_scanner, document_parser, schema_manager
    global ollama_client, information_extractor, neo4j_manager
    global community_detector, community_summarizer, graphrag_qa

    try:
        # 初始化基础服务
        document_scanner = DocumentScanner(scan_directories=[])  # 空目录列表，运行时动态指定
        document_parser = DocumentParser()
        schema_manager = SchemaManager("config/schema.yaml")
        ollama_client = OllamaClient()
        information_extractor = InformationExtractor(schema_manager, ollama_client)
        neo4j_manager = Neo4jManager()

        # 初始化GraphRAG服务
        community_detector = CommunityDetector(neo4j_manager)
        community_summarizer = CommunitySummarizer(ollama_client, neo4j_manager)
        graphrag_qa = GraphRAGQA(ollama_client, neo4j_manager)

        # 加载Schema
        schema_manager.load_schema()

        # 测试Neo4j连接
        neo4j_manager.connect()

        print("✅ 所有服务初始化成功，包括GraphRAG核心功能")

    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    if neo4j_manager:
        neo4j_manager.disconnect()
    print("🔄 应用已关闭")


@app.get("/", response_model=StatusResponse)
async def root():
    """根路径，返回系统状态"""
    return StatusResponse(
        status="running", message="离线文档知识图谱系统正在运行", timestamp=datetime.now()
    )


@app.get("/health")
async def health_check():
    """健康检查接口"""
    health_status = {"status": "healthy", "timestamp": datetime.now(), "services": {}}

    # 检查各个服务状态
    try:
        # 检查Schema管理器
        schema = schema_manager.get_schema()
        health_status["services"]["schema_manager"] = {
            "status": "healthy" if schema else "error",
            "entities": len(schema.entities) if schema else 0,
            "relations": len(schema.relations) if schema else 0,
        }
    except Exception as e:
        health_status["services"]["schema_manager"] = {
            "status": "error",
            "error": str(e),
        }

    try:
        # 检查Ollama连接
        ollama_available = ollama_client.test_connection()
        health_status["services"]["ollama"] = {
            "status": "healthy" if ollama_available else "error",
            "model": ollama_client.model,
        }
    except Exception as e:
        health_status["services"]["ollama"] = {"status": "error", "error": str(e)}

    try:
        # 检查Neo4j连接
        stats = neo4j_manager.get_graph_stats()
        health_status["services"]["neo4j"] = {
            "status": "healthy" if stats else "error",
            "nodes": stats.total_nodes if stats else 0,
            "relationships": stats.total_relationships if stats else 0,
        }
    except Exception as e:
        health_status["services"]["neo4j"] = {"status": "error", "error": str(e)}

    return health_status


@app.post("/documents/scan")
async def scan_documents(request: DocumentScanRequest):
    """扫描指定目录中的文档"""
    try:
        if not os.path.exists(request.directory):
            raise HTTPException(status_code=400, detail="目录不存在")

        documents = document_scanner.scan_directory(
            request.directory, file_types=request.file_types
        )

        document_list = []
        for doc in documents:
            document_list.append(
                DocumentInfo(
                    file_path=doc.file_path,
                    title=doc.title,
                    file_type=doc.file_type,
                    size=doc.size,
                    modified_time=doc.modified_time,
                )
            )

        return {
            "success": True,
            "count": len(document_list),
            "documents": document_list,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档文件"""
    try:
        # 检查文件类型
        if not file.filename.endswith((".docx", ".xlsx", ".txt", ".md")):
            raise HTTPException(status_code=400, detail="不支持的文件类型")

        # 保存临时文件
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # 解析文档
            parsed_doc = document_parser.parse_document(tmp_file_path)

            if not parsed_doc.success:
                raise HTTPException(
                    status_code=400, detail=f"文档解析失败: {parsed_doc.error_message}"
                )

            return {
                "success": True,
                "document": {
                    "title": parsed_doc.title,
                    "file_type": parsed_doc.file_type,
                    "content_length": len(parsed_doc.content),
                    "metadata": parsed_doc.metadata,
                },
                "content": parsed_doc.content,
            }

        finally:
            # 清理临时文件
            os.unlink(tmp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/parse")
async def parse_document(file_path: str):
    """解析指定路径的文档"""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="文件不存在")

        parsed_doc = document_parser.parse_document(file_path)

        if not parsed_doc.success:
            raise HTTPException(
                status_code=400, detail=f"文档解析失败: {parsed_doc.error_message}"
            )

        return {
            "success": True,
            "document": {
                "file_path": parsed_doc.file_path,
                "title": parsed_doc.title,
                "file_type": parsed_doc.file_type,
                "content_length": len(parsed_doc.content),
                "metadata": parsed_doc.metadata,
            },
            "content": parsed_doc.content,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extraction/extract", response_model=ExtractionResponse)
async def extract_information(request: ExtractionRequest):
    """从文本中抽取信息"""
    try:
        # 配置抽取器参数
        information_extractor.chunk_size = request.chunk_size
        information_extractor.chunk_overlap = request.chunk_overlap

        # 执行抽取
        result = information_extractor.extract_from_text(request.text)

        # 转换实体和关系为字典格式
        entities = []
        for entity in result.entities:
            entities.append(
                {
                    "type": entity.type,
                    "name": entity.name,
                    "properties": entity.properties,
                    "confidence": entity.confidence,
                }
            )

        relations = []
        for relation in result.relations:
            relations.append(
                {
                    "type": relation.type,
                    "source": relation.source,
                    "target": relation.target,
                    "properties": relation.properties,
                    "confidence": relation.confidence,
                }
            )

        # 获取统计信息
        stats = information_extractor.get_extraction_stats(result)

        return ExtractionResponse(
            success=result.success,
            entities=entities,
            relations=relations,
            stats=stats,
            error_message=result.error_message,
        )

    except Exception as e:
        return ExtractionResponse(
            success=False, entities=[], relations=[], stats={}, error_message=str(e)
        )


@app.post("/extraction/extract-and-import")
async def extract_and_import(
    request: ExtractionRequest, background_tasks: BackgroundTasks
):
    """抽取信息并导入到图数据库"""
    try:
        # 执行抽取
        result = information_extractor.extract_from_text(request.text)

        if not result.success:
            raise HTTPException(
                status_code=400, detail=f"信息抽取失败: {result.error_message}"
            )

        # 后台任务导入到Neo4j
        background_tasks.add_task(import_to_neo4j, result)

        return {
            "success": True,
            "message": "抽取完成，正在后台导入到图数据库",
            "entities_count": len(result.entities),
            "relations_count": len(result.relations),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def import_to_neo4j(extraction_result):
    """后台任务：导入抽取结果到Neo4j"""
    try:
        entity_count, relation_count = neo4j_manager.import_extraction_result(
            extraction_result
        )
        print(f"✅ 导入完成: 实体 {entity_count}, 关系 {relation_count}")
    except Exception as e:
        print(f"❌ 导入失败: {e}")


@app.get("/graph/stats")
async def get_graph_stats():
    """获取图谱统计信息"""
    try:
        stats = neo4j_manager.get_graph_stats()

        if not stats:
            raise HTTPException(status_code=500, detail="获取统计信息失败")

        return {
            "success": True,
            "stats": {
                "total_nodes": stats.total_nodes,
                "total_relationships": stats.total_relationships,
                "node_types": stats.node_types,
                "relationship_types": stats.relationship_types,
                "last_updated": stats.last_updated,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/query")
async def execute_graph_query(request: QueryRequest):
    """执行图数据库查询"""
    try:
        result = neo4j_manager.execute_query(request.query, request.parameters)

        return {
            "success": result.success,
            "records": result.records,
            "summary": result.summary,
            "execution_time": result.execution_time,
            "error_message": result.error_message,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/search")
async def search_entities(request: SearchRequest):
    """搜索实体"""
    try:
        entities = neo4j_manager.search_entities(
            entity_type=request.entity_type,
            name_pattern=request.name_pattern,
            limit=request.limit,
        )

        return {"success": True, "count": len(entities), "entities": entities}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
async def get_schema():
    """获取当前Schema定义"""
    try:
        schema = schema_manager.get_schema()

        if not schema:
            raise HTTPException(status_code=500, detail="Schema未加载")

        return {
            "success": True,
            "schema": {
                "version": schema.version,
                "description": schema.description,
                "entities": {
                    name: {
                        "description": entity.description,
                        "properties": entity.properties,
                        "required_properties": list(entity.required_properties),
                    }
                    for name, entity in schema.entities.items()
                },
                "relations": {
                    name: {
                        "description": relation.description,
                        "source": relation.source,
                        "target": relation.target,
                        "properties": relation.properties,
                    }
                    for name, relation in schema.relations.items()
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# GraphRAG相关请求模型
class CommunityDetectionRequest(BaseModel):
    algorithm: str = "louvain"
    resolution: float = 1.0


class CommunitySummaryRequest(BaseModel):
    community_id: Optional[int] = None
    level: str = "detailed"


class GraphRAGQARequest(BaseModel):
    question: str
    search_strategy: str = "community_first"


# GraphRAG API端点
@app.post("/graphrag/detect_communities")
async def detect_communities(request: CommunityDetectionRequest):
    """检测图中的社区结构"""
    try:
        if not community_detector:
            raise HTTPException(status_code=503, detail="社区检测服务未初始化")

        result = community_detector.detect_communities(
            algorithm=request.algorithm, resolution=request.resolution
        )

        if result["success"]:
            return {"success": True, "message": "社区检测完成", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "社区检测失败"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graphrag/generate_summary")
async def generate_community_summary(request: CommunitySummaryRequest):
    """生成社区摘要"""
    try:
        if not community_summarizer:
            raise HTTPException(status_code=503, detail="社区摘要服务未初始化")

        if request.community_id is not None:
            # 生成单个社区摘要
            result = community_summarizer.generate_community_summary(
                community_id=request.community_id, level=request.level
            )
        else:
            # 生成所有社区摘要
            result = community_summarizer.generate_all_communities_summary(
                level=request.level
            )

        if result["success"]:
            return {"success": True, "message": "社区摘要生成完成", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "摘要生成失败"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graphrag/qa")
async def graphrag_question_answer(request: GraphRAGQARequest):
    """GraphRAG问答"""
    try:
        if not graphrag_qa:
            raise HTTPException(status_code=503, detail="GraphRAG问答服务未初始化")

        result = graphrag_qa.answer_question(
            question=request.question, search_strategy=request.search_strategy
        )

        if result["success"]:
            return {"success": True, "message": "问答完成", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "问答失败"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graphrag/communities")
async def get_communities_summary():
    """获取所有社区摘要信息"""
    try:
        if not community_detector:
            raise HTTPException(status_code=503, detail="社区检测服务未初始化")

        result = community_detector.get_all_communities_summary()

        if result["success"]:
            return {"success": True, "message": "获取社区信息成功", "data": result["data"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "获取社区信息失败"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graphrag/community/{community_id}")
async def get_community_detail(community_id: int):
    """获取指定社区的详细信息"""
    try:
        if not community_detector or not community_summarizer:
            raise HTTPException(status_code=503, detail="GraphRAG服务未初始化")

        # 获取社区子图
        subgraph = community_detector.get_community_subgraph(community_id)

        # 获取社区摘要
        summary = community_summarizer.get_community_summary(community_id)

        return {
            "success": True,
            "message": "获取社区详情成功",
            "data": {
                "community_id": community_id,
                "subgraph": subgraph,
                "summary": summary,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
