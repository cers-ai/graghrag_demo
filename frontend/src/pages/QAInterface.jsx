import React from 'react';
import { Card, Typography, Alert } from 'antd';

const { Title, Paragraph } = Typography;

const QAInterface = () => {
  return (
    <div>
      <Title level={2}>问答系统</Title>
      <Paragraph>
        基于知识图谱的智能问答系统。
      </Paragraph>

      <Card>
        <Alert
          message="功能开发中"
          description="问答系统功能正在开发中，敬请期待。"
          type="info"
          showIcon
        />
      </Card>
    </div>
  );
};

export default QAInterface;
