# 离线文档知识图谱自动构建与问答系统

## 项目简介

这是一个完全本地离线运行的知识图谱系统，能够自动扫描本地Word/Excel文档，按预设Schema抽取结构化知识，构建Neo4j图数据库，并提供图谱可视化展示和GraphRAG问答功能。

## 项目结构

```
graghrag_demo/
├── backend/                    # 后端服务
│   ├── app/                   # 应用主目录
│   │   ├── api/              # API接口
│   │   ├── core/             # 核心模块
│   │   ├── models/           # 数据模型
│   │   └── services/         # 业务服务
│   ├── tests/                # 后端测试
│   ├── requirements.txt      # Python依赖
│   └── main.py              # 应用入口
├── frontend/                  # 前端应用
│   ├── src/                  # 源代码
│   │   ├── components/       # React组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API服务
│   │   └── utils/           # 工具函数
│   ├── public/              # 静态资源
│   └── package.json         # 前端依赖
├── config/                   # 配置文件
│   ├── schema.yaml          # 知识图谱Schema定义
│   ├── config.yaml          # 系统配置
│   └── prompts/             # LLM提示词模板
├── data/                     # 数据目录
│   ├── documents/           # 待处理文档
│   ├── processed/           # 已处理文档
│   └── exports/             # 导出数据
├── docs/                     # 项目文档
├── scripts/                  # 脚本工具
└── docker/                   # Docker配置
```

## 技术栈

- **后端**: Python + FastAPI
- **前端**: React + Vite + TypeScript
- **数据库**: Neo4j
- **AI模型**: Ollama (qwen3:4b)
- **图谱可视化**: neovis.js

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 18
- Neo4j >= 5.0
- Ollama

### 安装步骤

1. 克隆项目
2. 安装后端依赖
3. 安装前端依赖
4. 配置数据库
5. 启动服务

详细安装说明请参考 `docs/installation.md`

## 功能特性

- 📁 自动文档扫描与监控
- 🧠 基于LLM的智能信息抽取
- 🕸️ 知识图谱自动构建
- 🎨 交互式图谱可视化
- 🤖 GraphRAG智能问答
- ⚙️ 可配置Schema管理

## 开发状态

项目正在积极开发中，当前版本：v0.1.0-alpha

## 许可证

MIT License
