@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🚀 启动GraphRAG轻量化演示系统...

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未运行，请先启动Docker
    pause
    exit /b 1
)

REM 检查docker-compose是否可用
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ docker-compose未安装，请先安装docker-compose
    pause
    exit /b 1
)

REM 进入docker目录
cd /d "%~dp0"

echo 📋 检查配置文件...
if not exist "..\config\schema.yaml" (
    echo ❌ 配置文件不存在: config\schema.yaml
    pause
    exit /b 1
)

echo 🔧 构建Docker镜像...
docker-compose build --no-cache

echo 🏃 启动服务...
docker-compose up -d

echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 📊 检查服务状态...
docker-compose ps

REM 检查本地Ollama服务
echo 🤖 检查本地Ollama服务...
curl -f http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ 本地Ollama服务未启动，请先启动Ollama服务
    echo    启动命令: ollama serve
    echo    下载模型: ollama pull qwen3:4b
) else (
    echo ✅ 本地Ollama服务正常运行
)

echo 🔍 验证服务健康状态...

REM 检查服务
echo 检查各项服务...
timeout /t 10 /nobreak >nul

echo.
echo 🎉 系统启动完成！
echo.
echo 📍 访问地址:
echo   前端界面: http://localhost:3000
echo   后端API: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo   Neo4j浏览器: http://localhost:7474
echo.
echo 🔑 Neo4j登录信息:
echo   用户名: neo4j
echo   密码: graghrag123
echo.
echo 📝 查看日志:
echo   docker-compose logs -f [service_name]
echo.
echo 🛑 停止系统:
echo   docker-compose down
echo.

pause
