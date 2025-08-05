# GraphRAG轻量化演示系统 - 核心功能说明

## 🎯 系统概述

GraphRAG轻量化演示系统是一个展示GraphRAG（Graph Retrieval-Augmented Generation）技术的完整平台。GraphRAG是微软研究院提出的一种新型RAG技术，通过图结构的社区检测和摘要来增强检索生成的质量。

## 🔧 核心技术架构

### GraphRAG技术栈
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

## 🚀 核心功能模块

### 1. 社区检测功能 (Community Detection)

#### 功能描述
使用图算法检测知识图谱中的社区结构，这是GraphRAG技术的基础组件。

#### 支持的算法
- **Louvain算法**: 基于模块度优化的社区检测，适用于大多数场景
- **标签传播算法**: 快速的社区检测算法，适用于大规模网络
- **Leiden算法**: Louvain的改进版本，提供更高质量的社区划分

#### 核心参数
- **分辨率参数**: 控制社区大小，值越大社区越小越多
- **算法选择**: 根据数据特点选择合适的检测算法

#### 输出结果
- 社区数量和分布
- 每个社区的节点列表
- 社区密度和连接性
- 模块度评分（衡量社区划分质量）

#### API端点
```http
POST /graphrag/detect_communities
{
  "algorithm": "louvain",
  "resolution": 1.0
}
```

### 2. 社区摘要功能 (Community Summarization)

#### 功能描述
使用AI大模型为每个检测到的社区生成智能摘要，提取社区的核心信息和特征。

#### 摘要级别
- **简要摘要**: 1-2句话概括社区主要内容
- **详细摘要**: 包含主题、关键实体、关系模式等详细信息
- **全面摘要**: 深度分析社区结构、功能和应用价值

#### 摘要内容
- **社区标题**: 基于内容生成的描述性标题
- **核心描述**: 社区的主要内容和特征
- **关键实体**: 社区中的重要实体类型
- **关键关系**: 社区中的主要关系模式
- **主要主题**: 从内容中提取的主题关键词

#### API端点
```http
POST /graphrag/generate_summary
{
  "community_id": 1,
  "level": "detailed"
}
```

### 3. GraphRAG问答功能 (GraphRAG QA)

#### 功能描述
基于社区结构的增强检索生成问答系统，这是GraphRAG技术的核心应用。

#### 搜索策略
- **社区优先搜索**: 先在相关社区内搜索，再进行全局搜索
- **全局优先搜索**: 在整个知识图谱中进行搜索
- **混合搜索策略**: 结合社区搜索和全局搜索的结果

#### 工作流程
1. **问题分析**: 分析用户问题，提取关键信息
2. **社区匹配**: 找到与问题最相关的社区
3. **信息检索**: 在相关社区中检索信息
4. **答案生成**: 使用AI模型基于检索结果生成答案
5. **结果评估**: 评估答案质量和置信度

#### 输出结果
- **AI生成答案**: 基于图结构信息的智能回答
- **信息来源**: 答案来源的社区或全局信息
- **置信度评分**: 答案可信度评估
- **相关社区**: 与问题相关的社区列表

#### API端点
```http
POST /graphrag/qa
{
  "question": "ABC公司有哪些员工？",
  "search_strategy": "community_first"
}
```

## 🎨 前端功能界面

### 1. 社区检测页面 (`/community-detection`)
- **参数配置**: 算法选择、分辨率调整
- **检测结果**: 社区统计、模块度评分
- **社区列表**: 详细的社区信息表格
- **可视化展示**: 社区结构图表

### 2. 社区摘要页面 (`/community-summary`)
- **摘要控制**: 级别选择、目标社区选择
- **摘要展示**: 卡片式社区摘要展示
- **详情查看**: 模态框显示完整摘要信息
- **批量生成**: 一键生成所有社区摘要

### 3. GraphRAG问答页面 (`/qa`)
- **问题输入**: 多行文本输入框
- **策略选择**: 搜索策略选择器
- **示例问题**: 预设的示例问题
- **答案展示**: 结构化的答案显示
- **历史记录**: 问答历史时间线

## 🔬 技术实现细节

### 社区检测算法实现
```python
# 使用NetworkX和python-louvain实现
import networkx as nx
import community as community_louvain

def detect_communities(graph_data, algorithm="louvain", resolution=1.0):
    # 构建NetworkX图
    G = nx.Graph()
    G.add_edges_from(graph_data["edges"])

    # 执行社区检测
    if algorithm == "louvain":
        communities = community_louvain.best_partition(G, resolution=resolution)

    # 计算模块度
    modularity = nx.algorithms.community.modularity(G, communities)

    return communities, modularity
```

### 社区摘要生成
```python
# 使用本地Ollama模型生成摘要
def generate_community_summary(community_data, level="detailed"):
    prompt = build_summary_prompt(community_data, level)
    response = ollama_client.generate_response(prompt)
    return parse_summary_response(response)
```

### GraphRAG问答流程
```python
# 基于社区的问答流程
def answer_question(question, strategy="community_first"):
    # 1. 找到相关社区
    relevant_communities = find_relevant_communities(question)

    # 2. 在社区中搜索信息
    community_info = search_in_communities(question, relevant_communities)

    # 3. 生成答案
    answer = generate_answer(question, community_info)

    return answer
```

## 📊 性能特点

### 算法性能
- **社区检测**: Louvain算法时间复杂度 O(n log n)
- **摘要生成**: 基于本地模型，响应时间 < 30秒
- **问答检索**: 社区优先搜索，平均响应时间 < 10秒

### 扩展性
- **图规模**: 支持万级节点的图结构
- **社区数量**: 自动适应不同规模的社区结构
- **并发处理**: 支持多用户同时使用

### 准确性
- **社区质量**: 通过模块度评估社区划分质量
- **摘要质量**: 基于大语言模型的智能摘要
- **问答准确性**: 结合图结构和语义理解

## 🛠️ 部署和使用

### 快速启动
```bash
# 1. 启动Docker服务
cd docker
docker-compose up -d

# 2. 启动本地Ollama服务
ollama serve
ollama pull qwen3:4b

# 3. 访问系统
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
# Neo4j: http://localhost:7474
```

### 使用流程
1. **数据准备**: 上传文档，构建知识图谱
2. **社区检测**: 执行社区检测算法
3. **摘要生成**: 为社区生成智能摘要
4. **问答体验**: 使用GraphRAG问答功能

## 🎯 应用场景

### 企业知识管理
- **组织架构分析**: 识别部门和团队结构
- **项目关系梳理**: 分析项目间的关联关系
- **知识社区发现**: 发现知识领域的聚集

### 学术研究
- **文献社区分析**: 识别研究领域和主题
- **合作网络分析**: 分析学者合作关系
- **知识图谱构建**: 构建领域知识图谱

### 产品推荐
- **用户群体分析**: 识别用户兴趣社区
- **商品关联分析**: 发现商品关联模式
- **个性化推荐**: 基于社区的推荐系统

## 🔮 技术优势

### GraphRAG vs 传统RAG
| 特性 | 传统RAG | GraphRAG |
|------|---------|----------|
| 检索方式 | 向量相似度 | 图结构+社区 |
| 上下文理解 | 局部文档 | 全局图结构 |
| 信息整合 | 简单拼接 | 社区摘要 |
| 答案质量 | 依赖检索质量 | 结构化增强 |

### 系统特点
- **轻量化设计**: 本地部署，无需云服务
- **模块化架构**: 组件独立，易于扩展
- **可视化界面**: 直观的操作和结果展示
- **生产就绪**: 完整的Docker化部署方案

## 📈 未来发展

### 功能扩展
- **多模态支持**: 支持图像、视频等多媒体内容
- **实时更新**: 支持图结构的实时更新和重新检测
- **高级可视化**: 3D图结构可视化和交互

### 算法优化
- **分层社区检测**: 支持多层级的社区结构
- **动态社区跟踪**: 跟踪社区的演化过程
- **自适应参数**: 自动优化算法参数

### 性能提升
- **分布式计算**: 支持大规模图的分布式处理
- **GPU加速**: 利用GPU加速图算法计算
- **缓存优化**: 智能缓存提升响应速度

---

**GraphRAG轻量化演示系统** 展示了图结构增强检索生成技术的强大潜力，为知识图谱应用提供了新的技术路径。
