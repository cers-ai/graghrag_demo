@echo off
REM 激活Python虚拟环境的批处理脚本

echo 正在激活Python虚拟环境...
call venv\Scripts\activate.bat

echo.
echo 虚拟环境已激活！
echo Python版本：
python --version

echo.
echo 已安装的主要包：
pip list | findstr "fastapi\|uvicorn\|neo4j\|ollama\|pydantic"

echo.
echo 使用方法：
echo   启动后端服务: python backend\main.py
echo   运行测试: pytest backend\tests\
echo   代码格式化: black backend\
echo.
