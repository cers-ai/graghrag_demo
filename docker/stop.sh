#!/bin/bash

# GraphRAG轻量化演示系统 - Docker停止脚本

set -e

echo "🛑 停止GraphRAG轻量化演示系统..."

# 进入docker目录
cd "$(dirname "$0")"

# 停止所有服务
echo "📋 停止所有服务..."
docker-compose down

echo "🧹 清理资源..."
# 可选：清理未使用的镜像和容器
# docker system prune -f

echo "📊 当前容器状态:"
docker-compose ps

echo "✅ 系统已停止"
