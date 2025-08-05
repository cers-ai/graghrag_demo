# GraphRAG轻量化演示系统

🚀 **展示GraphRAG技术的完整平台** - 实现社区检测、社区摘要和基于图结构的增强检索生成

## 🎯 什么是GraphRAG？

GraphRAG（Graph Retrieval-Augmented Generation）是微软研究院提出的新型RAG技术，通过图结构的社区检测和摘要来增强检索生成的质量。

### GraphRAG vs 传统RAG
| 特性 | 传统RAG | GraphRAG |
|------|---------|----------|
| 检索方式 | 向量相似度 | 图结构+社区 |
| 上下文理解 | 局部文档 | 全局图结构 |
| 信息整合 | 简单拼接 | 社区摘要 |
| 答案质量 | 依赖检索质量 | 结构化增强 |

## 🌟 核心功能

### 🔍 社区检测
- **多种算法**: Louvain、标签传播、Leiden算法
- **参数调优**: 分辨率参数控制社区粒度
- **质量评估**: 模块度评分和社区统计
- **可视化展示**: 直观的社区结构展示

### 📝 社区摘要
- **AI驱动**: 基于本地Ollama模型的智能摘要
- **多级别**: 简要、详细、全面三种摘要级别
- **结构化**: 提取关键实体、关系和主题
- **批量处理**: 支持单个和批量摘要生成

### 💬 GraphRAG问答
- **多策略**: 社区优先、全局优先、混合搜索
- **智能匹配**: 基于社区结构的问题分析
- **增强生成**: 结合图结构和语义理解
- **质量评估**: 置信度评分和来源追踪

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    GraphRAG技术架构                          │
├─────────────────────────────────────────────────────────────┤
│  前端展示层    │  React + Antd + 可视化组件                  │
├─────────────────────────────────────────────────────────────┤
│  API服务层     │  FastAPI + GraphRAG核心服务                │
├─────────────────────────────────────────────────────────────┤
│  GraphRAG核心  │  社区检测 + 社区摘要 + 增强问答             │
├─────────────────────────────────────────────────────────────┤
│  图算法层      │  NetworkX + Louvain + Label Propagation    │
├─────────────────────────────────────────────────────────────┤
│  AI模型层      │  本地Ollama + qwen3:4b                     │
├─────────────────────────────────────────────────────────────┤
│  数据存储层    │  Neo4j图数据库 + 社区信息持久化             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 前置要求
- Docker Desktop
- Git
- 8GB+ 内存

### 一键启动
```bash
# 1. 克隆项目
git clone https://github.com/cers-ai/graghrag_demo.git
cd graghrag_demo

# 2. 启动Docker服务
cd docker
docker-compose up -d

# 3. 启动本地Ollama服务
ollama serve
ollama pull qwen3:4b

# 4. 访问系统
# 前端界面: http://localhost:3000
# 后端API: http://localhost:8000
# Neo4j浏览器: http://localhost:7474
```

### Windows一键启动
```batch
cd docker
start.bat
```

### Linux/Mac一键启动
```bash
cd docker
chmod +x start.sh
./start.sh
```

## 📱 功能界面

### 🏠 仪表板
- 系统状态监控
- 服务健康检查
- 统计信息展示

### 📄 文档处理
- **文档扫描**: 批量扫描本地文档
- **信息抽取**: AI驱动的实体关系抽取
- **Schema管理**: 可视化的实体关系类型定义

### 🔍 GraphRAG核心功能
- **社区检测**: 图算法驱动的社区发现
- **社区摘要**: AI生成的智能摘要
- **GraphRAG问答**: 基于图结构的增强问答

### 📊 图谱可视化
- 知识图谱结构展示
- 社区结构可视化
- 交互式图谱探索

## 🛠️ 技术栈

### 后端技术
- **FastAPI**: 现代Python Web框架
- **Neo4j**: 图数据库
- **Ollama**: 本地大语言模型服务
- **NetworkX**: 图算法库
- **python-louvain**: 社区检测算法

### 前端技术
- **React 18**: 现代前端框架
- **Ant Design**: 企业级UI组件库
- **Vite**: 快速构建工具
- **React Router**: 单页应用路由

### 部署技术
- **Docker**: 容器化部署
- **Docker Compose**: 多服务编排
- **Nginx**: 前端静态文件服务

## 📋 使用流程

### 1. 数据准备
1. 上传文档到系统
2. 执行文档扫描和解析
3. 配置实体关系Schema

### 2. 信息抽取
1. 使用AI模型抽取实体和关系
2. 构建知识图谱
3. 验证和优化抽取结果

### 3. GraphRAG分析
1. **社区检测**: 选择算法和参数，执行社区检测
2. **社区摘要**: 生成AI驱动的社区摘要
3. **智能问答**: 体验GraphRAG增强问答

## 🔧 配置说明

### 环境变量
```bash
# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b

# 应用配置
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### Docker配置
- **后端服务**: 端口8000，健康检查
- **前端服务**: 端口3000，Nginx代理
- **Neo4j数据库**: 端口7474/7687，数据持久化
- **本地Ollama**: 端口11434，非容器化

## 📊 性能特点

### 算法性能
- **社区检测**: Louvain算法 O(n log n) 时间复杂度
- **摘要生成**: 本地模型，响应时间 < 30秒
- **问答检索**: 社区优先搜索，平均响应 < 10秒

### 扩展性
- **图规模**: 支持万级节点的图结构
- **社区数量**: 自动适应不同规模的社区结构
- **并发处理**: 支持多用户同时使用

## 🎯 应用场景

### 企业知识管理
- 组织架构分析
- 项目关系梳理
- 知识社区发现

### 学术研究
- 文献社区分析
- 合作网络分析
- 知识图谱构建

### 产品推荐
- 用户群体分析
- 商品关联分析
- 个性化推荐

## 🔮 技术优势

### GraphRAG核心价值
- **结构化理解**: 通过图结构理解信息关联
- **社区发现**: 自动识别知识聚集区域
- **智能摘要**: AI驱动的社区特征提取
- **增强检索**: 基于图结构的精准信息定位

### 系统特点
- **轻量化设计**: 本地部署，无需云服务
- **模块化架构**: 组件独立，易于扩展
- **可视化界面**: 直观的操作和结果展示
- **生产就绪**: 完整的Docker化部署方案

## 📚 文档和资源

- [GraphRAG功能详解](GRAPHRAG_FEATURES.md)
- [系统架构说明](SYSTEM_SUMMARY.md)
- [Docker部署指南](docker/README.md)
- [API接口文档](http://localhost:8000/docs)

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境
```bash
# 后端开发
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 前端开发
cd frontend
npm install
npm run dev
```

## 📄 许可证

MIT License

## 🙏 致谢

- [Microsoft GraphRAG](https://github.com/microsoft/graphrag) - GraphRAG技术灵感来源
- [Neo4j](https://neo4j.com/) - 图数据库支持
- [Ollama](https://ollama.ai/) - 本地大模型服务
- [NetworkX](https://networkx.org/) - 图算法库

---

**🎉 GraphRAG轻量化演示系统 - 展示图结构增强检索生成的强大潜力！**
