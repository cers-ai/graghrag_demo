import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Select,
  InputNumber,
  Typography,
  Alert,
  Spin,
  Row,
  Col,
  List,
  Tag,
  message,
  Modal,
  Descriptions,
  Empty,
  Space,
} from 'antd';
import {
  FileTextOutlined,
  BulbOutlined,
  TagsOutlined,
  LoadingOutlined,
  EyeOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const CommunitySummary = () => {
  const [loading, setLoading] = useState(false);
  const [communities, setCommunities] = useState([]);
  const [summaries, setSummaries] = useState({});
  const [selectedCommunity, setSelectedCommunity] = useState(null);
  const [summaryLevel, setSummaryLevel] = useState('detailed');
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState(null);

  useEffect(() => {
    loadCommunities();
  }, []);

  const loadCommunities = async () => {
    try {
      const response = await apiService.get('/graphrag/communities');
      if (response.data.success) {
        setCommunities(response.data.data.communities || []);
      }
    } catch (error) {
      console.error('加载社区信息失败:', error);
    }
  };

  const generateSummary = async (communityId = null) => {
    setLoading(true);
    try {
      const response = await apiService.post('/graphrag/generate_summary', {
        community_id: communityId,
        level: summaryLevel,
      });

      if (response.data.success) {
        const result = response.data.data;

        if (communityId) {
          // 单个社区摘要
          setSummaries(prev => ({
            ...prev,
            [communityId]: result
          }));
          message.success(`社区 ${communityId} 摘要生成完成`);
        } else {
          // 所有社区摘要
          const newSummaries = {};
          Object.entries(result.summaries).forEach(([id, summary]) => {
            newSummaries[id] = summary;
          });
          setSummaries(newSummaries);
          message.success(`成功生成 ${result.successful_summaries} 个社区摘要`);
        }
      } else {
        message.error('摘要生成失败');
      }
    } catch (error) {
      message.error(`摘要生成失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const viewSummaryDetail = (summary) => {
    setSelectedSummary(summary);
    setDetailModalVisible(true);
  };

  const renderSummaryCard = (community, summary) => {
    if (!summary) {
      return (
        <Card
          size="small"
          title={`社区 ${community.id}`}
          extra={
            <Button
              type="primary"
              size="small"
              icon={<RobotOutlined />}
              onClick={() => generateSummary(community.id)}
              loading={loading}
            >
              生成摘要
            </Button>
          }
        >
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无摘要，点击生成"
          />
        </Card>
      );
    }

    return (
      <Card
        size="small"
        title={
          <Space>
            <Tag color="blue">社区 {summary.community_id}</Tag>
            <Tag color="green">{summary.level}</Tag>
          </Space>
        }
        extra={
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => viewSummaryDetail(summary)}
          >
            查看详情
          </Button>
        }
        hoverable
      >
        <div style={{ marginBottom: 12 }}>
          <Text strong>{summary.summary?.title || '社区摘要'}</Text>
        </div>

        <Paragraph
          ellipsis={{ rows: 3, expandable: false }}
          style={{ marginBottom: 12, fontSize: '14px' }}
        >
          {summary.summary?.description || '暂无描述'}
        </Paragraph>

        <div style={{ marginBottom: 8 }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>关键实体:</Text>
          <div style={{ marginTop: 4 }}>
            {(summary.summary?.key_entities || []).slice(0, 3).map((entity, index) => (
              <Tag key={index} color="cyan" size="small">
                {entity}
              </Tag>
            ))}
            {(summary.summary?.key_entities || []).length > 3 && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                等{summary.summary.key_entities.length}个
              </Text>
            )}
          </div>
        </div>

        <div>
          <Text type="secondary" style={{ fontSize: '12px' }}>关键关系:</Text>
          <div style={{ marginTop: 4 }}>
            {(summary.summary?.key_relations || []).slice(0, 3).map((relation, index) => (
              <Tag key={index} color="orange" size="small">
                {relation}
              </Tag>
            ))}
            {(summary.summary?.key_relations || []).length > 3 && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                等{summary.summary.key_relations.length}个
              </Text>
            )}
          </div>
        </div>

        <div style={{ marginTop: 12, textAlign: 'right' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            节点: {summary.node_count} | 边: {summary.edge_count}
          </Text>
        </div>
      </Card>
    );
  };

  return (
    <div>
      <Title level={2}>
        <FileTextOutlined /> 社区摘要
      </Title>
      <Paragraph>
        使用AI大模型为每个社区生成智能摘要，这是GraphRAG技术的关键组件。
      </Paragraph>

      {/* 摘要生成控制 */}
      <Card title="摘要生成控制" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <div>
              <label>摘要级别:</label>
              <Select
                value={summaryLevel}
                onChange={setSummaryLevel}
                style={{ width: '100%', marginTop: 4 }}
              >
                <Option value="brief">简要摘要</Option>
                <Option value="detailed">详细摘要</Option>
                <Option value="comprehensive">全面摘要</Option>
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={8}>
            <div>
              <label>目标社区:</label>
              <Select
                value={selectedCommunity}
                onChange={setSelectedCommunity}
                style={{ width: '100%', marginTop: 4 }}
                placeholder="选择社区或留空生成所有"
                allowClear
              >
                {communities.map(community => (
                  <Option key={community.id} value={community.id}>
                    社区 {community.id} ({community.size}个节点)
                  </Option>
                ))}
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={8}>
            <div style={{ marginTop: 24 }}>
              <Button
                type="primary"
                icon={<RobotOutlined />}
                onClick={() => generateSummary(selectedCommunity)}
                loading={loading}
                size="large"
                block
              >
                {selectedCommunity ? '生成单个摘要' : '生成所有摘要'}
              </Button>
            </div>
          </Col>
        </Row>

        <Alert
          message="摘要级别说明"
          description={
            <div>
              <div><strong>简要摘要:</strong> 1-2句话概括社区主要内容</div>
              <div><strong>详细摘要:</strong> 包含主题、关键实体、关系模式等详细信息</div>
              <div><strong>全面摘要:</strong> 深度分析社区结构、功能和应用价值</div>
            </div>
          }
          type="info"
          style={{ marginTop: 16 }}
        />
      </Card>

      {/* 社区摘要展示 */}
      <Card
        title={`社区摘要展示 (${Object.keys(summaries).length}/${communities.length})`}
        extra={
          <Button
            icon={<FileTextOutlined />}
            onClick={loadCommunities}
          >
            刷新社区
          </Button>
        }
      >
        {communities.length > 0 ? (
          <Row gutter={[16, 16]}>
            {communities.map(community => (
              <Col xs={24} sm={12} lg={8} key={community.id}>
                {renderSummaryCard(community, summaries[community.id])}
              </Col>
            ))}
          </Row>
        ) : (
          <Empty
            description="暂无社区数据，请先执行社区检测"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>

      {/* 摘要详情模态框 */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            社区摘要详情
            {selectedSummary && (
              <Tag color="blue">社区 {selectedSummary.community_id}</Tag>
            )}
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedSummary && (
          <div>
            <Descriptions bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="社区ID" span={1}>
                {selectedSummary.community_id}
              </Descriptions.Item>
              <Descriptions.Item label="摘要级别" span={1}>
                <Tag color="green">{selectedSummary.level}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="节点数量" span={1}>
                {selectedSummary.node_count}
              </Descriptions.Item>
              <Descriptions.Item label="边数量" span={3}>
                {selectedSummary.edge_count}
              </Descriptions.Item>
            </Descriptions>

            <Card size="small" title="摘要内容" style={{ marginBottom: 16 }}>
              <Title level={5}>{selectedSummary.summary?.title}</Title>
              <Paragraph>{selectedSummary.summary?.description}</Paragraph>
            </Card>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12}>
                <Card size="small" title={<><TagsOutlined /> 关键实体</>}>
                  <div>
                    {(selectedSummary.summary?.key_entities || []).map((entity, index) => (
                      <Tag key={index} color="cyan" style={{ marginBottom: 4 }}>
                        {entity}
                      </Tag>
                    ))}
                  </div>
                </Card>
              </Col>

              <Col xs={24} sm={12}>
                <Card size="small" title={<><BulbOutlined /> 关键关系</>}>
                  <div>
                    {(selectedSummary.summary?.key_relations || []).map((relation, index) => (
                      <Tag key={index} color="orange" style={{ marginBottom: 4 }}>
                        {relation}
                      </Tag>
                    ))}
                  </div>
                </Card>
              </Col>
            </Row>

            {selectedSummary.summary?.main_topics && (
              <Card size="small" title="主要主题" style={{ marginTop: 16 }}>
                <div>
                  {selectedSummary.summary.main_topics.map((topic, index) => (
                    <Tag key={index} color="purple" style={{ marginBottom: 4 }}>
                      {topic}
                    </Tag>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default CommunitySummary;
