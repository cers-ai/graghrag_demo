import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DocumentScanner from './pages/DocumentScanner';
import SchemaViewer from './pages/SchemaViewer';
import ExtractionProcess from './pages/ExtractionProcess';
import GraphVisualization from './pages/GraphVisualization';
import QAInterface from './pages/QAInterface';
import CommunityDetection from './pages/CommunityDetection';
import CommunitySummary from './pages/CommunitySummary';
import './App.css';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scanner" element={<DocumentScanner />} />
            <Route path="/schema" element={<SchemaViewer />} />
            <Route path="/extraction" element={<ExtractionProcess />} />
            <Route path="/community-detection" element={<CommunityDetection />} />
            <Route path="/community-summary" element={<CommunitySummary />} />
            <Route path="/graph" element={<GraphVisualization />} />
            <Route path="/qa" element={<QAInterface />} />
          </Routes>
        </Layout>
      </Router>
    </ConfigProvider>
  );
}

export default App;
