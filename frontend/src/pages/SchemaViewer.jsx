import React, { useState, useEffect } from 'react';
import { Card, Typography, Spin, Alert, Descriptions, Tag, Divider } from 'antd';
import { apiService } from '../services/api';

const { Title, Paragraph } = Typography;

const SchemaViewer = () => {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSchema();
  }, []);

  const fetchSchema = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getSchema();
      if (response.data.success) {
        setSchema(response.data.schema);
      } else {
        setError('获取Schema失败');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载Schema...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="加载失败"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  return (
    <div>
      <Title level={2}>Schema展示</Title>
      <Paragraph>
        查看当前系统的实体和关系类型定义。
      </Paragraph>

      {schema && (
        <>
          <Descriptions title="Schema信息" bordered>
            <Descriptions.Item label="版本">{schema.version}</Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{schema.description}</Descriptions.Item>
            <Descriptions.Item label="实体类型数量">{Object.keys(schema.entities).length}</Descriptions.Item>
            <Descriptions.Item label="关系类型数量">{Object.keys(schema.relations).length}</Descriptions.Item>
          </Descriptions>

          <Divider />

          {/* 实体类型 */}
          <Title level={3}>实体类型</Title>
          {Object.entries(schema.entities).map(([name, entity]) => (
            <Card key={name} title={name} style={{ marginBottom: 16 }} size="small">
              <Paragraph>{entity.description}</Paragraph>

              <div style={{ marginBottom: 8 }}>
                <strong>属性:</strong>
              </div>
              {Object.entries(entity.properties).map(([propName, propConfig]) => (
                <Tag
                  key={propName}
                  color={entity.required_properties.includes(propName) ? 'red' : 'blue'}
                  style={{ marginBottom: 4 }}
                >
                  {propName} ({propConfig.type})
                  {entity.required_properties.includes(propName) && ' *'}
                </Tag>
              ))}

              {entity.required_properties.length > 0 && (
                <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                  * 必需属性
                </div>
              )}
            </Card>
          ))}

          <Divider />

          {/* 关系类型 */}
          <Title level={3}>关系类型</Title>
          {Object.entries(schema.relations).map(([name, relation]) => (
            <Card key={name} title={name} style={{ marginBottom: 16 }} size="small">
              <Paragraph>{relation.description}</Paragraph>

              <div style={{ marginBottom: 8 }}>
                <strong>关系方向:</strong>
                <Tag color="green" style={{ marginLeft: 8 }}>{relation.source}</Tag>
                <span style={{ margin: '0 8px' }}>→</span>
                <Tag color="orange">{relation.target}</Tag>
              </div>

              {Object.keys(relation.properties).length > 0 && (
                <>
                  <div style={{ marginBottom: 8 }}>
                    <strong>关系属性:</strong>
                  </div>
                  {Object.entries(relation.properties).map(([propName, propConfig]) => (
                    <Tag key={propName} color="purple" style={{ marginBottom: 4 }}>
                      {propName} ({propConfig.type})
                    </Tag>
                  ))}
                </>
              )}
            </Card>
          ))}
        </>
      )}
    </div>
  );
};

export default SchemaViewer;
