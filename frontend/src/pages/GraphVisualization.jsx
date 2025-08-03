import React from 'react';
import { Card, Typography, Alert } from 'antd';

const { Title, Paragraph } = Typography;

const GraphVisualization = () => {
  return (
    <div>
      <Title level={2}>图谱可视化</Title>
      <Paragraph>
        交互式知识图谱可视化展示。
      </Paragraph>

      <Card>
        <Alert
          message="功能开发中"
          description="图谱可视化功能正在开发中，敬请期待。"
          type="info"
          showIcon
        />
      </Card>
    </div>
  );
};

export default GraphVisualization;
