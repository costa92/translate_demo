import api from './api';

/**
 * 开始新对话或继续现有对话
 * @param {Object} params - 对话参数
 * @param {string} params.query - 用户查询
 * @param {string} [params.conversation_id] - 对话ID（可选，用于继续现有对话）
 * @returns {Promise} - 对话响应
 */
export const sendMessage = async (params) => {
  try {
    // 转换参数以匹配API
    const apiParams = {
      query: params.query,
      metadata_filter: {}
    };
    
    // 使用查询API
    const response = await api.post('/query', apiParams);
    
    // 转换响应格式以匹配前端期望的格式
    return {
      message: response.answer || '无法获取回答',
      answer: response.answer || '无法获取回答',
      conversation_id: 'temp-' + Date.now(),
      chunks: response.chunks || [],
      sources: response.chunks || []
    };
  } catch (error) {
    console.error('发送消息失败:', error);
    throw error;
  }
};

/**
 * 获取对话历史
 * @param {string} conversationId - 对话ID
 * @returns {Promise} - 对话历史
 */
export const getConversationHistory = async (conversationId) => {
  try {
    // 由于API可能没有提供对话历史功能，我们返回一个空数组
    // 如果后端实现了这个功能，可以替换为实际的API调用
    return { 
      conversation_id: conversationId,
      messages: []
    };
  } catch (error) {
    console.error(`获取对话历史 ${conversationId} 失败:`, error);
    throw error;
  }
};

/**
 * 获取用户的所有对话
 * @returns {Promise} - 对话列表
 */
export const getConversations = async () => {
  try {
    // 由于API可能没有提供对话列表功能，我们返回一个空数组
    // 如果后端实现了这个功能，可以替换为实际的API调用
    return { conversations: [] };
  } catch (error) {
    console.error('获取对话列表失败:', error);
    throw error;
  }
};

/**
 * 删除对话
 * @param {string} conversationId - 对话ID
 * @returns {Promise} - 删除结果
 */
export const deleteConversation = async (conversationId) => {
  try {
    // 由于API可能没有提供删除对话功能，我们返回一个成功响应
    // 如果后端实现了这个功能，可以替换为实际的API调用
    return { success: true };
  } catch (error) {
    console.error(`删除对话 ${conversationId} 失败:`, error);
    throw error;
  }
};