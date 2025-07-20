import api from './api';

/**
 * 执行搜索查询
 * @param {Object} params - 查询参数
 * @param {string} params.query - 搜索查询
 * @param {Object} params.metadata_filter - 元数据过滤条件
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 * @returns {Promise} - 搜索结果
 */
export const search = async (params) => {
  try {
    // 转换参数以匹配API
    const apiParams = {
      query: params.query,
      metadata_filter: params.metadata_filter || {}
    };
    
    const response = await api.post('/query', apiParams);
    
    // 转换响应格式以匹配前端期望的格式
    const chunks = response.chunks || [];
    
    // 处理搜索结果，从metadata中提取title和source
    const processedResults = chunks.map(chunk => ({
      id: chunk.document_id,
      title: chunk.metadata?.title || '无标题',
      content: chunk.text,
      source: chunk.metadata?.source || '未知来源',
      score: 1.0,
      metadata: chunk.metadata || {},
      highlight: chunk.text
    }));
    
    return {
      results: processedResults,
      total: chunks.length,
      query: params.query,
      answer: response.answer
    };
  } catch (error) {
    console.error('搜索查询失败:', error);
    throw error;
  }
};

/**
 * 获取搜索建议
 * @param {string} query - 部分查询
 * @returns {Promise} - 搜索建议列表
 */
export const getSuggestions = async (query) => {
  try {
    // 由于API可能没有提供搜索建议功能，我们返回一个空数组
    // 如果后端实现了这个功能，可以替换为实际的API调用
    return { suggestions: [] };
  } catch (error) {
    console.error('获取搜索建议失败:', error);
    throw error;
  }
};

/**
 * 获取热门搜索
 * @returns {Promise} - 热门搜索列表
 */
export const getPopularSearches = async () => {
  try {
    // 由于API可能没有提供热门搜索功能，我们返回一个空数组
    // 如果后端实现了这个功能，可以替换为实际的API调用
    return { popular: [] };
  } catch (error) {
    console.error('获取热门搜索失败:', error);
    throw error;
  }
};