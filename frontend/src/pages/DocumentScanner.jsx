import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  Table,
  Upload,
  message,
  Space,
  Typography,
  Tag,
  Divider,
  Row,
  Col,
  Alert,
  Modal,
} from 'antd';
import {
  FolderOpenOutlined,
  ScanOutlined,
  UploadOutlined,
  FileTextOutlined,
  EyeOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const DocumentScanner = () => {
  const [directory, setDirectory] = useState('');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');

  // 扫描目录
  const handleScan = async () => {
    if (!directory.trim()) {
      message.error('请输入目录路径');
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.scanDocuments(directory.trim());
      if (response.data.success) {
        setDocuments(response.data.documents);
        message.success(`扫描完成，找到 ${response.data.count} 个文档`);
      } else {
        message.error('扫描失败');
      }
    } catch (error) {
      message.error(`扫描失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 文件上传
  const handleUpload = async (file) => {
    setUploadLoading(true);
    try {
      const response = await apiService.uploadDocument(file);
      if (response.data.success) {
        message.success('文档上传成功');
        // 添加到文档列表
        const newDoc = {
          file_path: file.name,
          title: response.data.document.title,
          file_type: response.data.document.file_type,
          size: file.size,
          modified_time: new Date().toISOString(),
          content: response.data.content,
        };
        setDocuments(prev => [newDoc, ...prev]);
      } else {
        message.error('文档上传失败');
      }
    } catch (error) {
      message.error(`上传失败: ${error.message}`);
    } finally {
      setUploadLoading(false);
    }
    return false; // 阻止默认上传行为
  };

  // 预览文档
  const handlePreview = async (record) => {
    try {
      let content = record.content;

      if (!content) {
        // 如果没有内容，尝试解析文档
        const response = await apiService.parseDocument(record.file_path);
        if (response.data.success) {
          content = response.data.content;
        } else {
          message.error('文档解析失败');
          return;
        }
      }

      setPreviewTitle(record.title);
      setPreviewContent(content);
      setPreviewVisible(true);
    } catch (error) {
      message.error(`预览失败: ${error.message}`);
    }
  };

  // 删除文档
  const handleDelete = (index) => {
    const newDocuments = documents.filter((_, i) => i !== index);
    setDocuments(newDocuments);
    message.success('文档已从列表中移除');
  };

  // 表格列定义
  const columns = [
    {
      title: '文档名称',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type) => {
        const color = type === '.docx' ? 'blue' : type === '.xlsx' ? 'green' : 'default';
        return <Tag color={color}>{type}</Tag>;
      },
    },
    {
      title: '文件大小',
      dataIndex: 'size',
      key: 'size',
      render: (size) => {
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
      },
    },
    {
      title: '修改时间',
      dataIndex: 'modified_time',
      key: 'modified_time',
      render: (time) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record, index) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
          >
            预览
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(index)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>文档扫描</Title>
      <Paragraph>
        扫描本地目录中的文档文件，或直接上传文档进行处理。
      </Paragraph>

      {/* 目录扫描 */}
      <Card title="目录扫描" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={18}>
            <Input
              placeholder="请输入要扫描的目录路径，例如: D:\Documents"
              value={directory}
              onChange={(e) => setDirectory(e.target.value)}
              prefix={<FolderOpenOutlined />}
              onPressEnter={handleScan}
            />
          </Col>
          <Col xs={24} md={6}>
            <Button
              type="primary"
              icon={<ScanOutlined />}
              onClick={handleScan}
              loading={loading}
              block
            >
              扫描目录
            </Button>
          </Col>
        </Row>

        <Alert
          message="支持的文件类型"
          description="目前支持 .docx (Word文档) 和 .xlsx (Excel表格) 文件格式"
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </Card>

      {/* 文件上传 */}
      <Card title="文件上传" style={{ marginBottom: 24 }}>
        <Upload.Dragger
          accept=".docx,.xlsx,.txt,.md"
          beforeUpload={handleUpload}
          showUploadList={false}
          loading={uploadLoading}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 .docx, .xlsx, .txt, .md 格式文件
          </p>
        </Upload.Dragger>
      </Card>

      <Divider />

      {/* 文档列表 */}
      <Card
        title={`文档列表 (${documents.length})`}
        extra={
          documents.length > 0 && (
            <Button
              danger
              onClick={() => {
                setDocuments([]);
                message.success('已清空文档列表');
              }}
            >
              清空列表
            </Button>
          )
        }
      >
        <Table
          columns={columns}
          dataSource={documents}
          rowKey={(record, index) => index}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个文档`,
          }}
          locale={{
            emptyText: '暂无文档，请扫描目录或上传文件',
          }}
        />
      </Card>

      {/* 预览模态框 */}
      <Modal
        title={`文档预览 - ${previewTitle}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>,
        ]}
        width="80%"
        style={{ top: 20 }}
      >
        <TextArea
          value={previewContent}
          readOnly
          autoSize={{ minRows: 20, maxRows: 30 }}
          style={{ fontFamily: 'monospace' }}
        />
      </Modal>
    </div>
  );
};

export default DocumentScanner;
