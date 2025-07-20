import api from './api';

/**
 * 获取文档列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 * @param {string} params.sort - 排序字段
 * @param {string} params.order - 排序顺序 (asc/desc)
 * @returns {Promise} - 文档列表和分页信息
 */
export const getDocuments = async (params = {}) => {
  try {
    // 由于简化版API不支持文档列表，我们返回一个空列表
    return {
      documents: [],
      totalPages: 0,
      total: 0
    };
  } catch (error) {
    console.error('获取文档列表失败:', error);
    throw error;
  }
};

/**
 * 获取单个文档
 * @param {string} id - 文档ID
 * @returns {Promise} - 文档详情
 */
export const getDocument = async (id) => {
  try {
    // 由于简化版API不支持获取单个文档，我们返回一个模拟文档
    return {
      id: id,
      title: '文档不可用',
      content: '简化版API不支持获取单个文档',
      source: '系统',
      date: new Date().toISOString(),
      metadata: {}
    };
  } catch (error) {
    console.error(`获取文档 ${id} 失败:`, error);
    throw error;
  }
};

/**
 * 添加新文档
 * @param {Object} document - 文档数据
 * @param {string} document.title - 文档标题 (将存储在metadata中)
 * @param {string} document.content - 文档内容
 * @param {string} document.source - 文档来源 (将存储在metadata中)
 * @param {Object} document.metadata - 文档元数据
 * @returns {Promise} - 新添加的文档
 */
export const addDocument = async (document) => {
  try {
    // 将title和source移到metadata中
    const metadata = {
      ...document.metadata,
      title: document.title,
    };
    
    if (document.source) {
      metadata.source = document.source;
    }
    
    // 构建符合API要求的文档对象
    const apiDocument = {
      content: document.content,
      type: "text",
      metadata: metadata
    };
    
    // 使用简化版API，直接添加文档
    return await api.post('/add_document', apiDocument);
  } catch (error) {
    console.error('添加文档失败:', error);
    throw error;
  }
};

/**
 * 更新文档
 * @param {string} id - 文档ID
 * @param {Object} document - 文档数据
 * @returns {Promise} - 更新后的文档
 */
export const updateDocument = async (id, document) => {
  try {
    // 由于简化版API不支持更新文档，我们返回一个成功响应
    return {
      success: true,
      message: '文档已更新（模拟）'
    };
  } catch (error) {
    console.error(`更新文档 ${id} 失败:`, error);
    throw error;
  }
};

/**
 * 删除文档
 * @param {string} id - 文档ID
 * @returns {Promise} - 删除结果
 */
export const deleteDocument = async (id) => {
  try {
    // 由于简化版API不支持删除文档，我们返回一个成功响应
    return {
      success: true,
      message: '文档已删除（模拟）'
    };
  } catch (error) {
    console.error(`删除文档 ${id} 失败:`, error);
    throw error;
  }
};