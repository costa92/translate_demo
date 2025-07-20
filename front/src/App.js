import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import DocumentsPage from './pages/DocumentsPage';
import AddDocumentPage from './pages/AddDocumentPage';
import DocumentDetailPage from './pages/DocumentDetailPage';
import SearchPage from './pages/SearchPage';
import './App.css';

/**
 * 应用程序主组件
 */
const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/documents/add" element={<AddDocumentPage />} />
        <Route path="/documents/:id" element={<DocumentDetailPage />} />
        <Route path="/search" element={<SearchPage />} />
      </Routes>
    </Router>
  );
};

export default App;