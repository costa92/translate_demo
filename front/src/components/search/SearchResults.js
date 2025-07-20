import React from 'react';
import ResultItem from './ResultItem';
import EmptyState from '../common/EmptyState';
import LoadingSpinner from '../common/LoadingSpinner';
import './SearchResults.css';

/**
 * 搜索结果组件
 * @param {Object} props - 组件属性
 * @param {Object} props.result - 搜索结果
 * @param {boolean} props.loading - 是否正在加载
 * @param {string} props.query - 搜索查询
 */
const SearchResults = ({ result, loading, query }) => {
  if (loading && (!result || !result.chunks || result.chunks.length === 0)) {
    return <LoadingSpinner text="搜索中..." />;
  }
  
  if (!result || !result.chunks || result.chunks.length === 0) {
    return (
      <EmptyState
        message={query ? `没有找到与"${query}"相关的结果` : '请输入搜索查询'}
      />
    );
  }
  
  const { answer, chunks } = result;
  
  return (
    <div className="search-results">
      {answer && (
        <div className="search-answer">
          <h3>回答</h3>
          <div className="answer-content">
            {answer.split('\n').map((paragraph, index) => (
              paragraph ? <p key={index}>{paragraph}</p> : <br key={index} />
            ))}
          </div>
        </div>
      )}
      
      <div className="search-chunks">
        <h3>相关文档 ({chunks.length})</h3>
        
        {chunks.map((chunk) => (
          <ResultItem key={chunk.chunk_id} chunk={chunk} query={query} />
        ))}
      </div>
      
      {loading && <LoadingSpinner size="small" />}
    </div>
  );
};

export default SearchResults;