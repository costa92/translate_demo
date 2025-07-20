import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Layout from '../components/common/Layout';
import SearchBar from '../components/search/SearchBar';
import SearchResults from '../components/search/SearchResults';
import ConversationHistory from '../components/conversation/ConversationHistory';
import InputBox from '../components/conversation/InputBox';
import ConversationControls from '../components/conversation/ConversationControls';
import { search } from '../services/searchService';
import { sendMessage } from '../services/conversationService';
import './SearchPage.css';

/**
 * 搜索页面组件
 */
const SearchPage = () => {
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialQuery = queryParams.get('query') || '';
  
  const [searchParams, setSearchParams] = useState({
    query: initialQuery,
    metadata_filter: {}
  });
  const [searchResult, setSearchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationMode, setConversationMode] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  
  // 执行搜索
  const handleSearch = async (params) => {
    try {
      setLoading(true);
      setError(null);
      setSearchParams(params);
      
      // 更新 URL 查询参数
      const newUrl = `/search?query=${encodeURIComponent(params.query)}`;
      window.history.pushState({}, '', newUrl);
      
      const result = await search(params);
      setSearchResult(result);
      
      // 如果在对话模式下，将查询添加到消息列表
      if (conversationMode) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'user',
            content: params.query,
            timestamp: new Date().toISOString()
          }
        ]);
        
        // 如果有回答，添加到消息列表
        if (result.answer || result.message) {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: result.message || result.answer || '无回答',
              timestamp: new Date().toISOString()
            }
          ]);
        }
      }
    } catch (err) {
      setError('搜索失败，请稍后重试');
      console.error('搜索失败:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // 发送消息
  const handleSendMessage = async (content) => {
    try {
      setLoading(true);
      setError(null);
      
      // 添加用户消息到列表
      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content,
          timestamp: new Date().toISOString()
        }
      ]);
      
      // 发送消息到服务器
      const response = await sendMessage({
        query: content,
        conversation_id: conversationId
      });
      
      // 更新对话 ID
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }
      
      // 添加系统回答到列表
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.message || response.answer || '无回答',
          timestamp: new Date().toISOString()
        }
      ]);
      
      // 更新搜索结果
      setSearchResult(response);
    } catch (err) {
      setError('发送消息失败，请稍后重试');
      console.error('发送消息失败:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // 开始新对话
  const handleNewConversation = () => {
    setConversationId(null);
    setMessages([]);
    setSearchResult(null);
  };
  
  // 切换对话模式
  const handleToggleConversationMode = () => {
    setConversationMode(!conversationMode);
    
    if (!conversationMode && searchResult?.answer) {
      // 如果切换到对话模式，将当前查询和回答添加到消息列表
      setMessages([
        {
          role: 'user',
          content: searchParams.query,
          timestamp: new Date().toISOString()
        },
        {
          role: 'assistant',
          content: searchResult.message || searchResult.answer || '无回答',
          timestamp: new Date().toISOString()
        }
      ]);
    }
  };
  
  // 初始加载时执行搜索
  useEffect(() => {
    if (initialQuery) {
      handleSearch({ query: initialQuery });
    }
  }, [initialQuery]);
  
  return (
    <Layout>
      <div className="search-page">
        <div className="search-header">
          <h1>知识库搜索</h1>
          
          <div className="search-mode-toggle">
            <button
              className={`mode-button ${!conversationMode ? 'active' : ''}`}
              onClick={() => setConversationMode(false)}
            >
              标准搜索
            </button>
            <button
              className={`mode-button ${conversationMode ? 'active' : ''}`}
              onClick={() => setConversationMode(true)}
            >
              对话模式
            </button>
          </div>
        </div>
        
        {!conversationMode ? (
          // 标准搜索模式
          <>
            <SearchBar
              onSearch={handleSearch}
              initialQuery={searchParams.query}
            />
            
            <SearchResults
              result={searchResult}
              loading={loading}
              query={searchParams.query}
            />
            
            {searchResult && searchResult.answer && (
              <div className="conversation-prompt">
                <p>想要继续对话？</p>
                <button
                  className="conversation-prompt-button"
                  onClick={handleToggleConversationMode}
                >
                  切换到对话模式
                </button>
              </div>
            )}
          </>
        ) : (
          // 对话模式
          <>
            <ConversationControls
              onNewConversation={handleNewConversation}
              disabled={loading}
            />
            
            <ConversationHistory messages={messages} />
            
            <InputBox
              onSend={handleSendMessage}
              disabled={loading}
              loading={loading}
            />
            
            {searchResult && searchResult.chunks && searchResult.chunks.length > 0 && (
              <div className="search-sources">
                <h3>参考来源</h3>
                <ul className="sources-list">
                  {searchResult.chunks.map((chunk, index) => (
                    <li key={index} className="source-item">
                      {chunk.metadata.title || '未命名文档'}
                      {chunk.metadata.source && (
                        <span className="source-origin">
                          {chunk.metadata.source}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
        
        {error && <div className="search-error">{error}</div>}
      </div>
    </Layout>
  );
};

export default SearchPage;