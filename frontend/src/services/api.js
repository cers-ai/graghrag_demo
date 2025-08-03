import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// API方法
export const apiService = {
  // 健康检查
  healthCheck: () => api.get('/health'),

  // 获取系统状态
  getStatus: () => api.get('/'),

  // Schema相关
  getSchema: () => api.get('/schema'),

  // 文档扫描
  scanDocuments: (directory, fileTypes = ['.docx', '.xlsx']) =>
    api.post('/documents/scan', { directory, file_types: fileTypes }),

  // 文档上传
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // 文档解析
  parseDocument: (filePath) =>
    api.post('/documents/parse', null, { params: { file_path: filePath } }),

  // 信息抽取
  extractInformation: (text, chunkSize = 2000, chunkOverlap = 200) =>
    api.post('/extraction/extract', {
      text,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
    }),

  // 抽取并导入
  extractAndImport: (text, chunkSize = 2000, chunkOverlap = 200) =>
    api.post('/extraction/extract-and-import', {
      text,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
    }),

  // 图谱统计
  getGraphStats: () => api.get('/graph/stats'),

  // 图谱查询
  queryGraph: (query, parameters = null) =>
    api.post('/graph/query', { query, parameters }),

  // 搜索实体
  searchEntities: (entityType = null, namePattern = null, limit = 100) =>
    api.post('/graph/search', {
      entity_type: entityType,
      name_pattern: namePattern,
      limit,
    }),
};

export default api;
