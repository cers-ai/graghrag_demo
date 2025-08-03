# 离线文档知识图谱系统 Makefile

.PHONY: help install dev test lint format clean docker-up docker-down

# 默认目标
help:
	@echo "离线文档知识图谱系统 - 开发命令"
	@echo ""
	@echo "环境管理:"
	@echo "  install     安装依赖"
	@echo "  dev         启动开发环境"
	@echo "  clean       清理临时文件"
	@echo ""
	@echo "代码质量:"
	@echo "  format      格式化代码"
	@echo "  lint        代码检查"
	@echo "  test        运行测试"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up   启动Docker服务"
	@echo "  docker-down 停止Docker服务"
	@echo ""
	@echo "数据库:"
	@echo "  db-init     初始化数据库"
	@echo "  db-test     测试数据库连接"
	@echo ""
	@echo "模型:"
	@echo "  model-test  测试Ollama模型"

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install -r backend/requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install

# 启动开发环境
dev:
	@echo "启动后端服务..."
	cd backend && python main.py

# 代码格式化
format:
	@echo "格式化Python代码..."
	black backend/ scripts/
	@echo "格式化完成"

# 代码检查
lint:
	@echo "检查Python代码..."
	flake8 backend/ scripts/
	@echo "检查完成"

# 运行测试
test:
	@echo "运行Python测试..."
	pytest backend/tests/ -v
	@echo "测试完成"

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf backend/dist/
	rm -rf backend/build/
	rm -rf backend/*.egg-info/
	@echo "清理完成"

# 启动Docker服务
docker-up:
	@echo "启动Docker服务..."
	cd docker && docker-compose up -d
	@echo "Docker服务已启动"

# 停止Docker服务
docker-down:
	@echo "停止Docker服务..."
	cd docker && docker-compose down
	@echo "Docker服务已停止"

# 初始化数据库
db-init:
	@echo "初始化Neo4j数据库..."
	python scripts/init_neo4j.py
	@echo "数据库初始化完成"

# 测试数据库连接
db-test:
	@echo "测试Neo4j数据库连接..."
	python scripts/test_neo4j.py
	@echo "数据库测试完成"

# 测试Ollama模型
model-test:
	@echo "测试Ollama模型..."
	python scripts/test_ollama.py
	@echo "模型测试完成"

# 验证配置
config-validate:
	@echo "验证配置文件..."
	python scripts/validate_config.py
	@echo "配置验证完成"

# 完整的开发环境检查
check-all:
	@echo "运行完整的环境检查..."
	python scripts/dev_tools.py all
	@echo "环境检查完成"
