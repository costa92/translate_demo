import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DocumentItem from './DocumentItem';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import EmptyState from '../common/EmptyState';
import { getDocuments } from '../../services/documentService';
import './DocumentList.css';

/**
 * 文档列表组件
 */
const DocumentList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sort, setSort] = useState('date');
  const [order, setOrder] = useState('desc');
  
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getDocuments({
        page,
        limit: 10,
        sort,
        order
      });
      
      setDocuments(response.documents || []);
      setTotalPages(response.totalPages || 1);
    } catch (err) {
      setError('获取文档列表失败，请稍后重试');
      console.error('获取文档列表失败:', err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchDocuments();
  }, [page, sort, order]);
  
  const handleSortChange = (newSort) => {
    if (newSort === sort) {
      // 如果点击当前排序字段，则切换排序顺序
      setOrder(order === 'asc' ? 'desc' : 'asc');
    } else {
      // 如果点击新的排序字段，则设置为降序
      setSort(newSort);
      setOrder('desc');
    }
    
    // 重置页码
    setPage(1);
  };
  
  const handlePageChange = (newPage) => {
    setPage(newPage);
  };
  
  if (loading && documents.length === 0) {
    return <LoadingSpinner text="加载文档中..." />;
  }
  
  if (error && documents.length === 0) {
    return <ErrorMessage message={error} onRetry={fetchDocuments} />;
  }
  
  if (documents.length === 0) {
    return (
      <EmptyState
        message="暂无文档"
        action={
          <Link to="/documents/add">
            <Button>添加文档</Button>
          </Link>
        }
      />
    );
  }
  
  return (
    <div className="document-list">
      <div className="document-list-header">
        <h2>文档列表</h2>
        <Link to="/documents/add">
          <Button>添加文档</Button>
        </Link>
      </div>
      
      <div className="document-list-sort">
        <span>排序:</span>
        <button
          className={`sort-button ${sort === 'title' ? 'active' : ''}`}
          onClick={() => handleSortChange('title')}
        >
          标题 {sort === 'title' && (order === 'asc' ? '↑' : '↓')}
        </button>
        <button
          className={`sort-button ${sort === 'source' ? 'active' : ''}`}
          onClick={() => handleSortChange('source')}
        >
          来源 {sort === 'source' && (order === 'asc' ? '↑' : '↓')}
        </button>
        <button
          className={`sort-button ${sort === 'date' ? 'active' : ''}`}
          onClick={() => handleSortChange('date')}
        >
          日期 {sort === 'date' && (order === 'asc' ? '↑' : '↓')}
        </button>
      </div>
      
      <div className="document-items">
        {documents.map((document) => (
          <DocumentItem key={document.id} document={document} />
        ))}
      </div>
      
      {loading && <LoadingSpinner size="small" />}
      
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-button"
            disabled={page === 1}
            onClick={() => handlePageChange(page - 1)}
          >
            上一页
          </button>
          
          <span className="pagination-info">
            第 {page} 页，共 {totalPages} 页
          </span>
          
          <button
            className="pagination-button"
            disabled={page === totalPages}
            onClick={() => handlePageChange(page + 1)}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentList;