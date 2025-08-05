import React, { useState } from 'react';
import { Layout as AntLayout, Menu, theme } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  ScanOutlined,
  PartitionOutlined,
  ExperimentOutlined,
  ShareAltOutlined,
  QuestionCircleOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ClusterOutlined,
  FileTextOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = AntLayout;

const Layout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/scanner',
      icon: <ScanOutlined />,
      label: '文档扫描',
    },
    {
      key: '/schema',
      icon: <PartitionOutlined />,
      label: 'Schema展示',
    },
    {
      key: '/extraction',
      icon: <ExperimentOutlined />,
      label: '信息抽取',
    },
    {
      key: '/community-detection',
      icon: <ClusterOutlined />,
      label: '社区检测',
    },
    {
      key: '/community-summary',
      icon: <FileTextOutlined />,
      label: '社区摘要',
    },
    {
      key: '/graph',
      icon: <ShareAltOutlined />,
      label: '图谱可视化',
    },
    {
      key: '/qa',
      icon: <QuestionCircleOutlined />,
      label: 'GraphRAG问答',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="demo-logo-vertical" style={{
          height: 32,
          margin: 16,
          background: 'rgba(255, 255, 255, 0.3)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: collapsed ? '12px' : '14px'
        }}>
          {collapsed ? 'GR' : 'GraphRAG'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            padding: 0,
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              fontSize: '16px',
              padding: '0 24px',
              cursor: 'pointer',
            }}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>
          <div style={{ flex: 1, fontSize: '18px', fontWeight: 'bold' }}>
            GraphRAG轻量化演示系统
          </div>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;
