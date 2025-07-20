import React from 'react';
import Layout from '../components/common/Layout';
import AddDocumentForm from '../components/documents/AddDocumentForm';
import './AddDocumentPage.css';

/**
 * 添加文档页面组件
 */
const AddDocumentPage = () => {
  return (
    <Layout>
      <div className="add-document-page">
        <AddDocumentForm />
      </div>
    </Layout>
  );
};

export default AddDocumentPage;