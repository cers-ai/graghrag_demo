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
  Table,
  Tag,
  message,
  Statistic,
  Progress,
  Divider,
} from 'antd';
import {
  ClusterOutlined,
  BarChartOutlined,
  NodeIndexOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const CommunityDetection = () => {
  const [loading, setLoading] = useState(false);
  const [algorithm, setAlgorithm] = useState('louvain');
  const [resolution, setResolution] = useState(1.0);
  const [detectionResult, setDetectionResult] = useState(null);
  const [communities, setCommunities] = useState([]);

  useEffect(() => {
    loadExistingCommunities();
  }, []);

  const loadExistingCommunities = async () => {
    try {
      const response = await apiService.get('/graphrag/communities');
      if (response.data.success) {
        setCommunities(response.data.data.communities || []);
      }
    } catch (error) {
      console.error('加载社区信息失败:', error);
    }
  };

  const handleDetection = async () => {
    setLoading(true);
    try {
      const response = await apiService.post('/graphrag/detect_communities', {
        algorithm,
        resolution,
      });

      if (response.data.success) {
        setDetectionResult(response.data.data);
        message.success('社区检测完成');
        // 重新加载社区列表
        await loadExistingCommunities();
      } else {
        message.error('社区检测失败');
      }
    } catch (error) {
      message.error(`社区检测失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const communityColumns = [
    {
      title: '社区ID',
      dataIndex: 'id',
      key: 'id',
      render: (id) => <Tag color="blue">社区 {id}</Tag>,
    },
    {
      title: '节点数量',
      dataIndex: 'size',
      key: 'size',
      sorter: (a, b) => a.size - b.size,
    },
    {
      title: '密度',
      dataIndex: 'density',
      key: 'density',
      render: (density) => (
        <div>
          <Progress
            percent={Math.round(density * 100)}
            size="small"
            format={() => density.toFixed(3)}
          />
        </div>
      ),
    },
    {
      title: '内部边',
      dataIndex: 'internal_edges',
      key: 'internal_edges',
    },
    {
      title: '外部边',
      dataIndex: 'external_edges',
      key: 'external_edges',
    },
    {
      title: '主要节点',
      dataIndex: 'nodes',
      key: 'nodes',
      render: (nodes) => (
        <div>
          {nodes.slice(0, 3).map((node, index) => (
            <Tag key={index} color="green" style={{ marginBottom: 2 }}>
              {node}
            </Tag>
          ))}
          {nodes.length > 3 && <Text type="secondary">等{nodes.length}个</Text>}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          onClick={() => viewCommunityDetail(record.id)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  const viewCommunityDetail = (communityId) => {
    // 这里可以跳转到社区详情页面或打开模态框
    message.info(`查看社区 ${communityId} 详情功能开发中`);
  };

  return (
    <div>
      <Title level={2}>
        <ClusterOutlined /> 社区检测
      </Title>
      <Paragraph>
        使用图算法检测知识图谱中的社区结构，这是GraphRAG技术的核心组件。
      </Paragraph>

      {/* 检测参数配置 */}
      <Card title="检测参数配置" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <div>
              <label>检测算法:</label>
              <Select
                value={algorithm}
                onChange={setAlgorithm}
                style={{ width: '100%', marginTop: 4 }}
              >
                <Option value="louvain">Louvain算法</Option>
                <Option value="label_propagation">标签传播算法</Option>
                <Option value="leiden">Leiden算法</Option>
              </Select>
            </div>
          </Col>

          <Col xs={24} sm={8}>
            <div>
              <label>分辨率参数:</label>
              <InputNumber
                min={0.1}
                max={5.0}
                step={0.1}
                value={resolution}
                onChange={setResolution}
                style={{ width: '100%', marginTop: 4 }}
              />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                值越大，社区越小越多
              </Text>
            </div>
          </Col>

          <Col xs={24} sm={8}>
            <div style={{ marginTop: 24 }}>
              <Button
                type="primary"
                icon={<ClusterOutlined />}
                onClick={handleDetection}
                loading={loading}
                size="large"
                block
              >
                开始检测
              </Button>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 检测结果统计 */}
      {detectionResult && (
        <Card title="检测结果统计" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={12} sm={6}>
              <Statistic
                title="社区数量"
                value={detectionResult.total_communities}
                prefix={<ClusterOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>

            <Col xs={12} sm={6}>
              <Statistic
                title="节点总数"
                value={detectionResult.total_nodes}
                prefix={<NodeIndexOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>

            <Col xs={12} sm={6}>
              <Statistic
                title="边总数"
                value={detectionResult.total_edges}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>

            <Col xs={12} sm={6}>
              <Statistic
                title="模块度"
                value={detectionResult.modularity}
                precision={3}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Col>
          </Row>

          <Divider />

          <Alert
            message="检测完成"
            description={`使用${detectionResult.algorithm}算法，分辨率${detectionResult.resolution}，成功检测到${detectionResult.total_communities}个社区。模块度为${detectionResult.modularity?.toFixed(3)}，表示社区划分质量。`}
            type="success"
            showIcon
          />
        </Card>
      )}

      {/* 社区列表 */}
      <Card
        title={`社区列表 ${communities.length > 0 ? `(${communities.length}个社区)` : ''}`}
        extra={
          <Button
            icon={<ClusterOutlined />}
            onClick={loadExistingCommunities}
            loading={loading}
          >
            刷新
          </Button>
        }
      >
        {communities.length > 0 ? (
          <Table
            columns={communityColumns}
            dataSource={communities}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 个社区`
            }}
            size="small"
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <ClusterOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
            <div style={{ marginTop: 16, color: '#999' }}>
              暂无社区数据，请先执行社区检测
            </div>
          </div>
        )}
      </Card>

      {/* 算法说明 */}
      <Card title="算法说明" style={{ marginTop: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card size="small" title="Louvain算法" bordered={false}>
              <Paragraph style={{ fontSize: '14px' }}>
                基于模块度优化的社区检测算法，能够快速发现大规模网络中的社区结构。
                适用于大多数场景，是默认推荐算法。
              </Paragraph>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card size="small" title="标签传播算法" bordered={false}>
              <Paragraph style={{ fontSize: '14px' }}>
                基于节点标签传播的社区检测算法，计算速度快，
                适用于大规模网络，但结果可能不够稳定。
              </Paragraph>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card size="small" title="Leiden算法" bordered={false}>
              <Paragraph style={{ fontSize: '14px' }}>
                Louvain算法的改进版本，能够发现更高质量的社区结构，
                但计算复杂度相对较高。
              </Paragraph>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default CommunityDetection;
