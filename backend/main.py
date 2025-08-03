"""
离线文档知识图谱系统 - 后端服务入口

这是系统的主要入口文件，负责启动FastAPI应用服务器。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 创建FastAPI应用实例
app = FastAPI(
    title="离线文档知识图谱系统",
    description="自动构建文档知识图谱并提供GraphRAG问答服务",
    version="0.1.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径健康检查"""
    return {"message": "离线文档知识图谱系统后端服务正在运行"}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "graghrag-backend"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
