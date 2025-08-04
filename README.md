# GraphRAG轻量化演示系统

一个轻量化的GraphRAG演示系统，展示如何结合图数据库和大语言模型构建知识图谱，支持文档解析、信息抽取、图谱构建和智能问答。

## 🌟 系统特点

- **完全离线运行**: 所有组件都在本地环境中运行，无需互联网连接
- **多格式文档支持**: 支持Word (.docx)、Excel (.xlsx)、PDF、文本文件等格式
- **智能信息抽取**: 基于Ollama本地大模型进行实体和关系抽取
- **图数据库存储**: 使用Neo4j存储和管理知识图谱
- **可视化界面**: 提供直观的Web界面进行操作和查看
- **模块化设计**: 清晰的架构，易于扩展和维护

## 🏗️ 系统架构

```
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── services/       # 核心服务模块
│   │   │   ├── document_scanner.py      # 文档扫描
│   │   │   ├── document_parser.py       # 文档解析
│   │   │   ├── schema_manager.py        # Schema管理
│   │   │   ├── ollama_client.py         # Ollama集成
│   │   │   ├── information_extractor.py # 信息抽取
│   │   │   └── neo4j_manager.py         # Neo4j操作
│   │   └── main.py         # FastAPI主应用
│   └── tests/              # 单元测试
├── frontend/               # 前端界面
│   ├── src/
│   │   ├── components/     # 通用组件
│   │   ├── pages/          # 页面组件
│   │   └── services/       # API服务
├── config/                 # 配置文件
│   ├── schema.yaml         # 知识图谱Schema定义
│   └── prompts/            # 提示词模板
├── scripts/                # 工具脚本
└── docs/                   # 文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- Neo4j 5.0+
- Ollama服务

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/cers-ai/graghrag_demo.git
cd graghrag_demo
```

2. **安装Python依赖**
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r backend/requirements.txt
```

3. **安装前端依赖**
```bash
cd frontend
npm install
cd ..
```

4. **启动Neo4j数据库**
```bash
# 确保Neo4j服务运行在 bolt://localhost:7687
# 默认用户名: neo4j, 密码: graghrag123
```

5. **启动Ollama服务**
```bash
# 确保Ollama服务运行在 http://localhost:11434
# 并已下载qwen3:4b模型
ollama pull qwen3:4b
```

### 运行系统

1. **启动后端API服务**
```bash
python run_api.py
```
后端服务将运行在 http://localhost:8000

2. **启动前端服务**
```bash
cd frontend
npm run dev
```
前端界面将运行在 http://localhost:5173

3. **访问系统**
- 前端界面: http://localhost:5173 (开发模式) 或 http://localhost:3000 (Docker部署)
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 📖 使用指南

### 1. 文档扫描
- 在"文档扫描"页面输入本地目录路径
- 系统会自动扫描支持的文档格式
- 也可以直接上传文档文件

### 2. Schema管理
- 在"Schema展示"页面查看当前的实体和关系定义
- 可以在 `config/schema.yaml` 中自定义Schema

### 3. 信息抽取
- 在"信息抽取"页面输入文本或选择文档
- 系统会自动抽取实体和关系
- 可以选择是否自动导入到图数据库

### 4. 图谱查看
- 在"图谱可视化"页面查看构建的知识图谱
- 支持交互式浏览和搜索

### 5. 智能问答
- 在"问答系统"页面进行自然语言问答
- 基于构建的知识图谱提供答案

## 🔧 配置说明

### Schema配置 (config/schema.yaml)
定义知识图谱的实体类型和关系类型：

```yaml
version: "1.0.0"
description: "离线文档知识图谱Schema定义"

entities:
  Person:
    description: "人员实体"
    properties:
      name:
        type: "string"
        required: true
      title:
        type: "string"
        required: false
    # ...

relations:
  WORKS_FOR:
    description: "工作关系"
    source: "Person"
    target: "Organization"
    # ...
```

### 提示词模板 (config/prompts/)
自定义信息抽取的提示词模板，支持变量替换。

## 🧪 测试

### 运行单元测试
```bash
# 测试所有模块
pytest backend/tests/ -v

# 测试特定模块
pytest backend/tests/test_document_scanner.py -v
```

### 运行系统验证
```bash
# 验证系统功能
python verify_system.py
```

### 功能测试
```bash
# 测试文档扫描
python scripts/scan_documents.py test

# 测试信息抽取
python scripts/extract_information.py test

# 测试Neo4j操作
python scripts/manage_neo4j.py connect
```

## 📊 系统监控

### 健康检查
访问 http://localhost:8000/health 查看各服务状态：
- Schema管理器状态
- Ollama模型状态
- Neo4j数据库状态

### 图谱统计
访问仪表板查看：
- 节点和关系数量
- 类型分布统计
- 系统运行状态

## 🔍 故障排除

### 常见问题

1. **Neo4j连接失败**
   - 检查Neo4j服务是否启动
   - 确认连接参数正确
   - 检查防火墙设置

2. **Ollama模型调用失败**
   - 确认Ollama服务运行
   - 检查模型是否已下载
   - 验证网络连接

3. **前端无法连接后端**
   - 确认后端API服务启动
   - 检查端口是否被占用
   - 验证CORS配置

### 日志查看
- 后端日志：控制台输出
- 前端日志：浏览器开发者工具
- Neo4j日志：Neo4j安装目录/logs/

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Neo4j](https://neo4j.com/) - 图数据库
- [Ollama](https://ollama.ai/) - 本地大模型服务
- [FastAPI](https://fastapi.tiangolo.com/) - 后端API框架
- [React](https://reactjs.org/) - 前端框架
- [Ant Design](https://ant.design/) - UI组件库

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue: https://github.com/cers-ai/graghrag_demo/issues
- 项目主页: https://github.com/cers-ai/graghrag_demo

---

**GraphRAG轻量化演示系统** - 展示GraphRAG技术的强大能力 🚀
