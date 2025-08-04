#!/bin/bash

# GraphRAG轻量化演示系统 - Docker启动脚本

set -e

echo "🚀 启动GraphRAG轻量化演示系统..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 进入docker目录
cd "$(dirname "$0")"

echo "📋 检查配置文件..."
if [ ! -f "../config/schema.yaml" ]; then
    echo "❌ 配置文件不存在: config/schema.yaml"
    exit 1
fi

echo "🔧 构建Docker镜像..."
docker-compose build --no-cache

echo "🏃 启动服务..."
docker-compose up -d

echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 检查本地Ollama服务
echo "🤖 检查本地Ollama服务..."
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ 本地Ollama服务正常运行"
else
    echo "❌ 本地Ollama服务未启动，请先启动Ollama服务"
    echo "   启动命令: ollama serve"
    echo "   下载模型: ollama pull qwen3:4b"
fi

echo "🔍 验证服务健康状态..."

# 检查Neo4j
echo "检查Neo4j..."
if curl -f http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Neo4j正常运行"
else
    echo "❌ Neo4j启动失败"
fi

# 检查Ollama
echo "检查Ollama..."
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama正常运行"
else
    echo "❌ Ollama启动失败"
fi

# 检查后端API
echo "检查后端API..."
sleep 10
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端API正常运行"
else
    echo "❌ 后端API启动失败"
fi

# 检查前端
echo "检查前端..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端正常运行"
else
    echo "❌ 前端启动失败"
fi

echo ""
echo "🎉 系统启动完成！"
echo ""
echo "📍 访问地址:"
echo "  前端界面: http://localhost:3000"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  Neo4j浏览器: http://localhost:7474"
echo ""
echo "🔑 Neo4j登录信息:"
echo "  用户名: neo4j"
echo "  密码: graghrag123"
echo ""
echo "📝 查看日志:"
echo "  docker-compose logs -f [service_name]"
echo ""
echo "🛑 停止系统:"
echo "  docker-compose down"
