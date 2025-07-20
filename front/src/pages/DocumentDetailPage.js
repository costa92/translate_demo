import React from 'react';
import Layout from '../components/common/Layout';
import DocumentDetail from '../components/documents/DocumentDetail';
import './DocumentDetailPage.css';

/**
 * 文档详情页面组件
 */
const DocumentDetailPage = () => {
  return (
    <Layout>
      <div className="document-detail-page">
        <DocumentDetail />
      </div>
    </Layout>
  );
};

export default DocumentDetailPage;