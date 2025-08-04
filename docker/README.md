# Docker部署指南

本目录包含GraphRAG轻量化演示系统的完整Docker化部署方案。

## 🏗️ 架构概述

Docker部署包含以下服务：

- **Neo4j**: 图数据库服务 (端口7474/7687) - Docker容器
- **Backend**: FastAPI后端服务 (端口8000) - Docker容器
- **Frontend**: React前端应用 (端口3000) - Docker容器
- **Ollama**: 本地AI模型服务 (端口11434) - 本地服务，非容器化

## 🚀 快速启动

### 方式1: 使用启动脚本 (推荐)

**Windows:**
```bash
cd docker
start.bat
```

**Linux/Mac:**
```bash
cd docker
chmod +x start.sh
./start.sh
```

### 方式2: 手动启动

```bash
cd docker

# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 注意：Ollama服务需要在本地单独启动
# ollama serve
# ollama pull qwen3:4b

# 查看状态
docker-compose ps
```

## 📋 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少4GB可用内存
- 至少10GB可用磁盘空间

## 🔧 配置说明

### 服务端口

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|----------|----------|------|
| Frontend | 80 | 3000 | Web界面 |
| Backend | 8000 | 8000 | API服务 |
| Neo4j HTTP | 7474 | 7474 | 数据库管理界面 |
| Neo4j Bolt | 7687 | 7687 | 数据库连接 |
| Ollama | 11434 | 11434 | AI模型服务 |

### 环境变量

主要环境变量在`.env.docker`文件中配置：

- `NEO4J_AUTH`: Neo4j认证信息
- `OLLAMA_MODEL`: 使用的AI模型
- `BACKEND_PORT`: 后端服务端口
- `LOG_LEVEL`: 日志级别

### 数据持久化

以下数据会持久化存储：

- `neo4j_data`: Neo4j数据库文件
- `ollama_data`: Ollama模型文件
- `backend_uploads`: 上传的文档文件

## 🔍 服务验证

启动完成后，可以通过以下地址验证服务：

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000/health
- **API文档**: http://localhost:8000/docs
- **Neo4j浏览器**: http://localhost:7474

### Neo4j登录信息
- 用户名: `neo4j`
- 密码: `graghrag123`

## 📝 常用命令

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f neo4j
docker-compose logs -f ollama
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 进入容器
```bash
# 进入后端容器
docker exec -it graghrag-backend bash

# 进入Neo4j容器
docker exec -it graghrag-neo4j bash
```

### 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

## 🛠️ 故障排除

### 常见问题

1. **端口冲突**
   - 检查端口是否被占用: `netstat -tulpn | grep :8000`
   - 修改docker-compose.yml中的端口映射

2. **内存不足**
   - 调整Neo4j内存配置
   - 增加Docker可用内存

3. **模型下载失败**
   - 检查网络连接
   - 手动下载模型: `docker exec graghrag-ollama ollama pull qwen3:4b`

4. **服务启动失败**
   - 查看服务日志: `docker-compose logs [service_name]`
   - 检查配置文件是否正确

### 重置系统

如果需要完全重置系统：

```bash
# 停止并删除所有容器和数据
docker-compose down -v

# 删除镜像
docker-compose down --rmi all

# 重新构建和启动
docker-compose build --no-cache
docker-compose up -d
```

## 🔄 更新部署

更新代码后重新部署：

```bash
# 停止服务
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

## 📊 监控和维护

### 健康检查

所有服务都配置了健康检查，可以通过以下命令查看：

```bash
docker-compose ps
```

### 备份数据

```bash
# 备份Neo4j数据
docker exec graghrag-neo4j neo4j-admin dump --database=neo4j --to=/tmp/backup.dump
docker cp graghrag-neo4j:/tmp/backup.dump ./neo4j-backup.dump

# 备份Ollama模型
docker cp graghrag-ollama:/root/.ollama ./ollama-backup
```

### 恢复数据

```bash
# 恢复Neo4j数据
docker cp ./neo4j-backup.dump graghrag-neo4j:/tmp/backup.dump
docker exec graghrag-neo4j neo4j-admin load --from=/tmp/backup.dump --database=neo4j --force
```

## 🚀 生产环境部署

生产环境部署建议：

1. **安全配置**
   - 修改默认密码
   - 配置HTTPS
   - 限制网络访问

2. **性能优化**
   - 调整内存配置
   - 配置日志轮转
   - 启用监控

3. **高可用性**
   - 配置数据备份
   - 设置服务重启策略
   - 配置负载均衡

---

更多信息请参考项目主README.md文件。
