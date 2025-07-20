import React from 'react';
import { Link } from 'react-router-dom';
import Card from '../common/Card';
import './DocumentItem.css';

/**
 * 文档项组件
 * @param {Object} props - 组件属性
 * @param {Object} props.document - 文档数据
 */
const DocumentItem = ({ document }) => {
  const { id, title, source, date, content } = document;
  
  // 格式化日期
  const formattedDate = date ? new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }) : '未知日期';
  
  // 截取内容摘要
  const excerpt = content && content.length > 150
    ? `${content.substring(0, 150)}...`
    : content;
  
  return (
    <Link to={`/documents/${id}`} className="document-item-link">
      <Card className="document-item">
        <h3 className="document-title">{title}</h3>
        
        <div className="document-meta">
          {source && <span className="document-source">{source}</span>}
          <span className="document-date">{formattedDate}</span>
        </div>
        
        {excerpt && <p className="document-excerpt">{excerpt}</p>}
      </Card>
    </Link>
  );
};

export default DocumentItem;