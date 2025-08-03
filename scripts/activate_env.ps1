# 激活Python虚拟环境的PowerShell脚本

Write-Host "正在激活Python虚拟环境..." -ForegroundColor Green

# 激活虚拟环境
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "虚拟环境已激活！" -ForegroundColor Green
Write-Host "Python版本："
python --version

Write-Host ""
Write-Host "已安装的主要包："
pip list | Select-String "fastapi|uvicorn|neo4j|ollama|pydantic"

Write-Host ""
Write-Host "使用方法：" -ForegroundColor Yellow
Write-Host "  启动后端服务: python backend\main.py"
Write-Host "  运行测试: pytest backend\tests\"
Write-Host "  代码格式化: black backend\"
Write-Host ""
