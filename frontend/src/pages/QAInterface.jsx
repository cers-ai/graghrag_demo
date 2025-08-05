import React, { useState, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  Select,
  Typography,
  Alert,
  Spin,
  Row,
  Col,
  List,
  Tag,
  message,
  Divider,
  Space,
  Timeline,
} from 'antd';
import {
  QuestionCircleOutlined,
  RobotOutlined,
  SearchOutlined,
  BulbOutlined,
  ClusterOutlined,
  GlobalOutlined,
  SendOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const QAInterface = () => {
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState('');
  const [searchStrategy, setSearchStrategy] = useState('community_first');
  const [qaHistory, setQaHistory] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState(null);

  // 示例问题
  const exampleQuestions = [
    "张三在哪个公司工作？",
    "ABC公司有哪些员工？",
    "项目经理都有谁？",
    "知识图谱项目的相关信息",
    "技术研发部门的组织结构"
  ];

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      message.error('请输入问题');
      return;
    }

    setLoading(true);
    setCurrentAnswer(null);

    try {
      const response = await apiService.post('/graphrag/qa', {
        question: question.trim(),
        search_strategy: searchStrategy,
      });

      if (response.data.success) {
        const result = response.data.data;
        setCurrentAnswer(result);

        // 添加到历史记录
        const newQA = {
          id: Date.now(),
          question: question.trim(),
          answer: result,
          timestamp: new Date().toLocaleString(),
        };
        setQaHistory(prev => [newQA, ...prev.slice(0, 9)]); // 保留最近10条

        message.success('问答完成');
      } else {
        message.error('问答失败');
      }
    } catch (error) {
      message.error(`问答失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const useExampleQuestion = (exampleQ) => {
    setQuestion(exampleQ);
  };

  const renderAnswer = (answer) => {
    if (!answer) return null;

    const getStrategyIcon = (strategy) => {
      switch (strategy) {
        case 'community_first':
          return <ClusterOutlined />;
        case 'global_first':
          return <GlobalOutlined />;
        case 'hybrid':
          return <SearchOutlined />;
        default:
          return <BulbOutlined />;
      }
    };

    const getStrategyName = (strategy) => {
      switch (strategy) {
        case 'community_first':
          return '社区优先搜索';
        case 'global_first':
          return '全局优先搜索';
        case 'hybrid':
          return '混合搜索';
        default:
          return '未知策略';
      }
    };

    const getConfidenceColor = (confidence) => {
      if (confidence >= 0.8) return 'green';
      if (confidence >= 0.6) return 'orange';
      return 'red';
    };

    return (
      <Card
        title={
          <Space>
            <RobotOutlined />
            AI回答
            <Tag color="blue" icon={getStrategyIcon(answer.strategy)}>
              {getStrategyName(answer.strategy)}
            </Tag>
          </Space>
        }
        style={{ marginTop: 16 }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ fontSize: '16px' }}>
            {answer.question}
          </Text>
        </div>

        <div style={{
          background: '#f6f8fa',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '16px'
        }}>
          <Paragraph style={{ margin: 0, fontSize: '15px', lineHeight: '1.6' }}>
            {answer.answer}
          </Paragraph>
        </div>

        <Row gutter={[16, 8]}>
          <Col xs={24} sm={12}>
            <div>
              <Text type="secondary">信息来源:</Text>
              <div style={{ marginTop: 4 }}>
                {answer.sources.map((source, index) => (
                  <Tag key={index} color="cyan">
                    {source}
                  </Tag>
                ))}
              </div>
            </div>
          </Col>

          <Col xs={24} sm={12}>
            <div>
              <Text type="secondary">置信度:</Text>
              <div style={{ marginTop: 4 }}>
                <Tag color={getConfidenceColor(answer.confidence)}>
                  {(answer.confidence * 100).toFixed(1)}%
                </Tag>
              </div>
            </div>
          </Col>
        </Row>

        {answer.relevant_communities && answer.relevant_communities.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">相关社区:</Text>
            <div style={{ marginTop: 4 }}>
              {answer.relevant_communities.map((community, index) => (
                <Tag key={index} color="purple">
                  社区 {community.community_id} (相关性: {(community.relevance_score * 100).toFixed(1)}%)
                </Tag>
              ))}
            </div>
          </div>
        )}
      </Card>
    );
  };

  return (
    <div>
      <Title level={2}>
        <QuestionCircleOutlined /> GraphRAG问答系统
      </Title>
      <Paragraph>
        基于社区结构的增强检索生成问答系统，这是GraphRAG技术的核心应用。
      </Paragraph>

      {/* 问答输入区域 */}
      <Card title="提出问题" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <TextArea
              placeholder="请输入您的问题..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              autoSize={{ minRows: 3, maxRows: 6 }}
              onPressEnter={(e) => {
                if (e.ctrlKey || e.metaKey) {
                  handleAskQuestion();
                }
              }}
            />
          </Col>

          <Col xs={24} sm={12}>
            <div>
              <label>搜索策略:</label>
              <Select
                value={searchStrategy}
                onChange={setSearchStrategy}
                style={{ width: '100%', marginTop: 4 }}
              >
                <Option value="community_first">
                  <ClusterOutlined /> 社区优先搜索
                </Option>
                <Option value="global_first">
                  <GlobalOutlined /> 全局优先搜索
                </Option>
                <Option value="hybrid">
                  <SearchOutlined /> 混合搜索策略
                </Option>
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={12}>
            <div style={{ marginTop: 24 }}>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleAskQuestion}
                loading={loading}
                size="large"
                block
                disabled={!question.trim()}
              >
                提问
              </Button>
            </div>
          </Col>
        </Row>

        {/* 示例问题 */}
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">示例问题:</Text>
          <div style={{ marginTop: 8 }}>
            {exampleQuestions.map((exampleQ, index) => (
              <Tag
                key={index}
                color="blue"
                style={{ marginBottom: 4, cursor: 'pointer' }}
                onClick={() => useExampleQuestion(exampleQ)}
              >
                {exampleQ}
              </Tag>
            ))}
          </div>
        </div>
      </Card>

      {/* 搜索策略说明 */}
      <Card title="搜索策略说明" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card size="small" bordered={false}>
              <div style={{ textAlign: 'center', marginBottom: 8 }}>
                <ClusterOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
              </div>
              <Title level={5} style={{ textAlign: 'center' }}>社区优先搜索</Title>
              <Paragraph style={{ fontSize: '14px' }}>
                先在相关社区内搜索信息，再进行全局搜索。适合针对特定领域的问题。
              </Paragraph>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card size="small" bordered={false}>
              <div style={{ textAlign: 'center', marginBottom: 8 }}>
                <GlobalOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
              </div>
              <Title level={5} style={{ textAlign: 'center' }}>全局优先搜索</Title>
              <Paragraph style={{ fontSize: '14px' }}>
                在整个知识图谱中进行搜索。适合需要全面信息的问题。
              </Paragraph>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card size="small" bordered={false}>
              <div style={{ textAlign: 'center', marginBottom: 8 }}>
                <SearchOutlined style={{ fontSize: '24px', color: '#722ed1' }} />
              </div>
              <Title level={5} style={{ textAlign: 'center' }}>混合搜索策略</Title>
              <Paragraph style={{ fontSize: '14px' }}>
                结合社区搜索和全局搜索的结果。提供最全面的答案。
              </Paragraph>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* 当前回答 */}
      {loading && (
        <Card style={{ textAlign: 'center', marginBottom: 24 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>AI正在分析问题并生成回答...</Text>
          </div>
        </Card>
      )}

      {currentAnswer && renderAnswer(currentAnswer)}

      {/* 问答历史 */}
      {qaHistory.length > 0 && (
        <Card title="问答历史" style={{ marginTop: 24 }}>
          <Timeline>
            {qaHistory.map((qa) => (
              <Timeline.Item key={qa.id}>
                <div>
                  <Text strong>{qa.question}</Text>
                  <div style={{ marginTop: 4, marginBottom: 8 }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {qa.timestamp} | {qa.answer.strategy} | 置信度: {(qa.answer.confidence * 100).toFixed(1)}%
                    </Text>
                  </div>
                  <div style={{
                    background: '#fafafa',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}>
                    {qa.answer.answer.length > 100
                      ? `${qa.answer.answer.substring(0, 100)}...`
                      : qa.answer.answer
                    }
                  </div>
                </div>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      )}
    </div>
  );
};

export default QAInterface;
