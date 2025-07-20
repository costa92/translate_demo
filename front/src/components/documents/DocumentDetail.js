import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { getDocument } from '../../services/documentService';
import './DocumentDetail.css';

/**
 * 文档详情组件
 */
const DocumentDetail = () => {
  const { id } = useParams();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await getDocument(id);
        setDocument(data);
      } catch (err) {
        setError('获取文档详情失败，请稍后重试');
        console.error('获取文档详情失败:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDocument();
  }, [id]);
  
  if (loading) {
    return <LoadingSpinner text="加载文档中..." />;
  }
  
  if (error) {
    return <ErrorMessage message={error} />;
  }
  
  if (!document) {
    return <ErrorMessage message="文档不存在" />;
  }
  
  const { title, content, source, date, metadata = {} } = document;
  
  // 过滤掉已经显示的元数据
  const filteredMetadata = { ...metadata };
  delete filteredMetadata.title;
  delete filteredMetadata.source;
  delete filteredMetadata.created_at;
  
  // 格式化日期
  const formattedDate = new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  
  return (
    <div className="document-detail">
      <div className="document-detail-header">
        <h1 className="document-detail-title">{title}</h1>
        
        <div className="document-detail-meta">
          {source && <span className="document-detail-source">来源: {source}</span>}
          <span className="document-detail-date">日期: {formattedDate}</span>
        </div>
      </div>
      
      <div className="document-detail-content">
        {content.split('\n').map((paragraph, index) => (
          paragraph ? <p key={index}>{paragraph}</p> : <br key={index} />
        ))}
      </div>
      
      {Object.keys(filteredMetadata).length > 0 && (
        <div className="document-detail-metadata">
          <h3>元数据</h3>
          <ul>
            {Object.entries(filteredMetadata).map(([key, value]) => (
              <li key={key}>
                <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : value}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="document-detail-actions">
        <Link to="/documents">
          <Button type="secondary">返回文档列表</Button>
        </Link>
      </div>
    </div>
  );
};

export default DocumentDetail;