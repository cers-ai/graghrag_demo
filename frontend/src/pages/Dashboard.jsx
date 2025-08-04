import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Button, Typography } from 'antd';
import {
  DatabaseOutlined,
  ShareAltOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Paragraph } = Typography;

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [healthData, setHealthData] = useState(null);
  const [graphStats, setGraphStats] = useState(null);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 获取健康状态
      const healthResponse = await apiService.healthCheck();
      setHealthData(healthResponse.data);

      // 获取图谱统计
      try {
        const statsResponse = await apiService.getGraphStats();
        if (statsResponse.data.success) {
          setGraphStats(statsResponse.data.stats);
        }
      } catch (statsError) {
        console.warn('获取图谱统计失败:', statsError);
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getServiceStatus = (service) => {
    if (!healthData?.services?.[service]) return 'unknown';
    return healthData.services[service].status;
  };

  const getServiceIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载系统状态...</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} style={{ margin: 0 }}>系统仪表板</Title>
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchData}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      {error && (
        <Alert
          message="连接错误"
          description={`无法连接到后端服务: ${error}`}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 系统状态卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Schema管理器"
              value={getServiceStatus('schema_manager')}
              prefix={getServiceIcon(getServiceStatus('schema_manager'))}
              valueStyle={{
                color: getServiceStatus('schema_manager') === 'healthy' ? '#3f8600' : '#cf1322'
              }}
            />
            {healthData?.services?.schema_manager && (
              <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                实体: {healthData.services.schema_manager.entities || 0} 个<br/>
                关系: {healthData.services.schema_manager.relations || 0} 个
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Ollama模型"
              value={getServiceStatus('ollama')}
              prefix={getServiceIcon(getServiceStatus('ollama'))}
              valueStyle={{
                color: getServiceStatus('ollama') === 'healthy' ? '#3f8600' : '#cf1322'
              }}
            />
            {healthData?.services?.ollama && (
              <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                模型: {healthData.services.ollama.model || 'Unknown'}
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Neo4j数据库"
              value={getServiceStatus('neo4j')}
              prefix={getServiceIcon(getServiceStatus('neo4j'))}
              valueStyle={{
                color: getServiceStatus('neo4j') === 'healthy' ? '#3f8600' : '#cf1322'
              }}
            />
            {healthData?.services?.neo4j && (
              <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                节点: {healthData.services.neo4j.nodes || 0} 个<br/>
                关系: {healthData.services.neo4j.relationships || 0} 个
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 图谱统计 */}
      {graphStats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总节点数"
                value={graphStats.total_nodes}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总关系数"
                value={graphStats.total_relationships}
                prefix={<ShareAltOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="节点类型"
                value={Object.keys(graphStats.node_types || {}).length}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="关系类型"
                value={Object.keys(graphStats.relationship_types || {}).length}
                prefix={<ShareAltOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 节点类型分布 */}
      {graphStats?.node_types && Object.keys(graphStats.node_types).length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} md={12}>
            <Card title="节点类型分布" size="small">
              {Object.entries(graphStats.node_types).map(([type, count]) => (
                <div key={type} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '4px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}>
                  <span>{type}</span>
                  <span style={{ fontWeight: 'bold', color: '#1890ff' }}>{count}</span>
                </div>
              ))}
            </Card>
          </Col>

          <Col xs={24} md={12}>
            <Card title="关系类型分布" size="small">
              {Object.entries(graphStats.relationship_types || {}).map(([type, count]) => (
                <div key={type} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '4px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}>
                  <span>{type}</span>
                  <span style={{ fontWeight: 'bold', color: '#52c41a' }}>{count}</span>
                </div>
              ))}
            </Card>
          </Col>
        </Row>
      )}

      {/* 系统信息 */}
      <Card title="系统信息" size="small">
        <Paragraph>
          <strong>GraphRAG轻量化演示系统</strong> - 展示GraphRAG技术的轻量化演示平台
        </Paragraph>
        <Paragraph>
          • 支持Word和Excel文档解析<br/>
          • 基于Ollama本地大模型进行信息抽取<br/>
          • 使用Neo4j图数据库存储知识图谱<br/>
          • 提供可视化图谱展示和智能问答功能
        </Paragraph>
        {healthData?.timestamp && (
          <Paragraph type="secondary">
            最后更新时间: {new Date(healthData.timestamp).toLocaleString()}
          </Paragraph>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;
