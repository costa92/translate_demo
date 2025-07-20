import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import Layout from '../components/common/Layout';
import DocumentList from '../components/documents/DocumentList';
import './DocumentsPage.css';

/**
 * 文档页面组件
 */
const DocumentsPage = () => {
  const location = useLocation();
  const [notification, setNotification] = useState(null);
  
  // 处理来自其他页面的通知
  useEffect(() => {
    if (location.state?.success) {
      setNotification({
        type: 'success',
        message: location.state.success
      });
      
      // 5秒后自动关闭通知
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [location.state]);
  
  const handleCloseNotification = () => {
    setNotification(null);
  };
  
  return (
    <Layout>
      <div className="documents-page">
        <h1>文档库</h1>
        
        {notification && (
          <div className={`notification ${notification.type}`}>
            <span>{notification.message}</span>
            <button
              className="notification-close"
              onClick={handleCloseNotification}
            >
              &times;
            </button>
          </div>
        )}
        
        <DocumentList />
      </div>
    </Layout>
  );
};

export default DocumentsPage;