@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🛑 停止GraphRAG轻量化演示系统...

REM 进入docker目录
cd /d "%~dp0"

REM 停止所有服务
echo 📋 停止所有服务...
docker-compose down

echo 🧹 清理资源...
REM 可选：清理未使用的镜像和容器
REM docker system prune -f

echo 📊 当前容器状态:
docker-compose ps

echo ✅ 系统已停止

pause
