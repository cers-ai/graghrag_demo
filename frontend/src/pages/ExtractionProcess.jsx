import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  Steps,
  Typography,
  Alert,
  Spin,
  Row,
  Col,
  Table,
  Tag,
  message,
  Switch,
  InputNumber,
} from 'antd';
import {
  ExperimentOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;
const { Step } = Steps;

const ExtractionProcess = () => {
  const [text, setText] = useState('');
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [extractionResult, setExtractionResult] = useState(null);
  const [autoImport, setAutoImport] = useState(true);
  const [chunkSize, setChunkSize] = useState(2000);
  const [chunkOverlap, setChunkOverlap] = useState(200);

  // 示例文本
  const exampleText = `张三是ABC科技公司的项目经理，负责管理知识图谱项目。
李四是该公司的高级开发工程师，参与项目的技术开发工作。
王五是产品经理，负责需求分析和产品设计。
这个项目属于技术研发部门，预计在2024年6月完成。
项目预算为100万元，目前已完成30%的开发工作。`;

  const handleExtraction = async () => {
    if (!text.trim()) {
      message.error('请输入要抽取的文本');
      return;
    }

    setLoading(true);
    setCurrentStep(1);
    setExtractionResult(null);

    try {
      let response;

      if (autoImport) {
        // 抽取并导入
        response = await apiService.extractAndImport(text, chunkSize, chunkOverlap);
        if (response.data.success) {
          setCurrentStep(3);
          message.success('信息抽取并导入成功');
          // 获取抽取结果用于显示
          const extractResponse = await apiService.extractInformation(text, chunkSize, chunkOverlap);
          if (extractResponse.data.success) {
            setExtractionResult(extractResponse.data);
          }
        } else {
          setCurrentStep(0);
          message.error('抽取失败');
        }
      } else {
        // 仅抽取
        response = await apiService.extractInformation(text, chunkSize, chunkOverlap);
        if (response.data.success) {
          setCurrentStep(2);
          setExtractionResult(response.data);
          message.success('信息抽取成功');
        } else {
          setCurrentStep(0);
          message.error('抽取失败');
        }
      }
    } catch (error) {
      setCurrentStep(0);
      message.error(`抽取失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!extractionResult) return;

    setLoading(true);
    setCurrentStep(2);

    try {
      const response = await apiService.extractAndImport(text, chunkSize, chunkOverlap);
      if (response.data.success) {
        setCurrentStep(3);
        message.success('导入成功');
      } else {
        message.error('导入失败');
      }
    } catch (error) {
      message.error(`导入失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const entityColumns = [
    {
      title: '实体类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: '实体名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '属性',
      dataIndex: 'properties',
      key: 'properties',
      render: (properties) => (
        <div>
          {Object.entries(properties).map(([key, value]) => (
            <Tag key={key} color="green" style={{ marginBottom: 2 }}>
              {key}: {value}
            </Tag>
          ))}
        </div>
      ),
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence) => `${(confidence * 100).toFixed(1)}%`,
    },
  ];

  const relationColumns = [
    {
      title: '关系类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag color="purple">{type}</Tag>,
    },
    {
      title: '源实体',
      dataIndex: 'source',
      key: 'source',
    },
    {
      title: '目标实体',
      dataIndex: 'target',
      key: 'target',
    },
    {
      title: '属性',
      dataIndex: 'properties',
      key: 'properties',
      render: (properties) => (
        <div>
          {Object.entries(properties).map(([key, value]) => (
            <Tag key={key} color="orange" style={{ marginBottom: 2 }}>
              {key}: {value}
            </Tag>
          ))}
        </div>
      ),
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence) => `${(confidence * 100).toFixed(1)}%`,
    },
  ];

  return (
    <div>
      <Title level={2}>信息抽取</Title>
      <Paragraph>
        从文本中抽取实体和关系信息，构建知识图谱。
      </Paragraph>

      {/* 抽取步骤 */}
      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep}>
          <Step title="输入文本" icon={<ExperimentOutlined />} />
          <Step
            title="信息抽取"
            icon={loading && currentStep === 1 ? <LoadingOutlined /> : <ExperimentOutlined />}
          />
          <Step
            title="结果展示"
            icon={loading && currentStep === 2 ? <LoadingOutlined /> : <CheckCircleOutlined />}
          />
          <Step
            title="导入图谱"
            icon={loading && currentStep === 2 ? <LoadingOutlined /> : <DatabaseOutlined />}
          />
        </Steps>
      </Card>

      {/* 输入区域 */}
      <Card title="文本输入" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <TextArea
              placeholder="请输入要进行信息抽取的文本..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              autoSize={{ minRows: 6, maxRows: 12 }}
            />
          </Col>

          <Col span={24}>
            <Button
              type="link"
              onClick={() => setText(exampleText)}
              style={{ padding: 0 }}
            >
              使用示例文本
            </Button>
          </Col>
        </Row>

        {/* 参数设置 */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} sm={8}>
            <div>
              <label>文本分块大小:</label>
              <InputNumber
                min={500}
                max={5000}
                value={chunkSize}
                onChange={setChunkSize}
                style={{ width: '100%', marginTop: 4 }}
              />
            </div>
          </Col>

          <Col xs={24} sm={8}>
            <div>
              <label>分块重叠:</label>
              <InputNumber
                min={0}
                max={500}
                value={chunkOverlap}
                onChange={setChunkOverlap}
                style={{ width: '100%', marginTop: 4 }}
              />
            </div>
          </Col>

          <Col xs={24} sm={8}>
            <div>
              <label>自动导入图谱:</label>
              <br />
              <Switch
                checked={autoImport}
                onChange={setAutoImport}
                style={{ marginTop: 4 }}
              />
            </div>
          </Col>
        </Row>

        <Row style={{ marginTop: 16 }}>
          <Col span={24}>
            <Button
              type="primary"
              icon={<ExperimentOutlined />}
              onClick={handleExtraction}
              loading={loading}
              disabled={!text.trim()}
              size="large"
            >
              {autoImport ? '抽取并导入' : '开始抽取'}
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 抽取结果 */}
      {extractionResult && (
        <>
          {/* 统计信息 */}
          <Card title="抽取统计" style={{ marginBottom: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                    {extractionResult.entities.length}
                  </div>
                  <div>实体数量</div>
                </div>
              </Col>

              <Col xs={12} sm={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                    {extractionResult.relations.length}
                  </div>
                  <div>关系数量</div>
                </div>
              </Col>

              <Col xs={12} sm={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
                    {Object.keys(extractionResult.stats.entity_types || {}).length}
                  </div>
                  <div>实体类型</div>
                </div>
              </Col>

              <Col xs={12} sm={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fa8c16' }}>
                    {Object.keys(extractionResult.stats.relation_types || {}).length}
                  </div>
                  <div>关系类型</div>
                </div>
              </Col>
            </Row>
          </Card>

          {/* 实体列表 */}
          <Card
            title={`抽取的实体 (${extractionResult.entities.length})`}
            style={{ marginBottom: 24 }}
          >
            <Table
              columns={entityColumns}
              dataSource={extractionResult.entities}
              rowKey={(record, index) => index}
              pagination={{ pageSize: 5 }}
              size="small"
            />
          </Card>

          {/* 关系列表 */}
          <Card title={`抽取的关系 (${extractionResult.relations.length})`}>
            <Table
              columns={relationColumns}
              dataSource={extractionResult.relations}
              rowKey={(record, index) => index}
              pagination={{ pageSize: 5 }}
              size="small"
            />

            {!autoImport && currentStep === 2 && (
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Button
                  type="primary"
                  icon={<DatabaseOutlined />}
                  onClick={handleImport}
                  loading={loading}
                  size="large"
                >
                  导入到图谱
                </Button>
              </div>
            )}
          </Card>
        </>
      )}

      {currentStep === 3 && (
        <Alert
          message="导入成功"
          description="实体和关系已成功导入到知识图谱中，您可以在图谱可视化页面查看结果。"
          type="success"
          showIcon
          style={{ marginTop: 24 }}
        />
      )}
    </div>
  );
};

export default ExtractionProcess;
