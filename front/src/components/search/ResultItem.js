import React from 'react';
import { Link } from 'react-router-dom';
import './ResultItem.css';

/**
 * 搜索结果项组件
 * @param {Object} props - 组件属性
 * @param {Object} props.chunk - 文本块数据
 * @param {string} props.query - 搜索查询
 */
const ResultItem = ({ chunk, query }) => {
  const { chunk_id, text, metadata, document_id } = chunk;
  
  // 高亮显示匹配文本
  const highlightText = (text, query) => {
    if (!query) return text;
    
    const queryWords = query.toLowerCase().split(/\s+/).filter(word => word.length > 2);
    
    if (queryWords.length === 0) return text;
    
    let result = text;
    
    queryWords.forEach(word => {
      const regex = new RegExp(`(${word})`, 'gi');
      result = result.replace(regex, '<mark>$1</mark>');
    });
    
    return result;
  };
  
  const highlightedText = highlightText(text, query);
  
  return (
    <div className="result-item">
      <div className="result-content">
        <div
          className="result-text"
          dangerouslySetInnerHTML={{ __html: highlightedText }}
        />
        
        {metadata && (
          <div className="result-metadata">
            {metadata.title && <span className="result-title">{metadata.title}</span>}
            {metadata.source && <span className="result-source">{metadata.source}</span>}
            {metadata.date && (
              <span className="result-date">
                {new Date(metadata.date).toLocaleDateString('zh-CN')}
              </span>
            )}
          </div>
        )}
      </div>
      
      {document_id && (
        <div className="result-actions">
          <Link to={`/documents/${document_id}`} className="view-document-link">
            查看完整文档
          </Link>
        </div>
      )}
    </div>
  );
};

export default ResultItem;