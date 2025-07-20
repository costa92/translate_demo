import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/common/Layout';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import SearchBar from '../components/search/SearchBar';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { getDocuments } from '../services/documentService';
import { getPopularSearches } from '../services/searchService';
import './HomePage.css';

/**
 * 首页组件
 */
const HomePage = () => {
  const [recentDocuments, setRecentDocuments] = useState([]);
  const [popularSearches, setPopularSearches] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 获取最近文档
        const documentsResponse = await getDocuments({
          page: 1,
          limit: 3,
          sort: 'date',
          order: 'desc'
        });
        
        setRecentDocuments(documentsResponse.documents || []);
        
        // 获取热门搜索
        try {
          const searchesResponse = await getPopularSearches();
          setPopularSearches(searchesResponse.searches || []);
        } catch (error) {
          console.error('获取热门搜索失败:', error);
          setPopularSearches([]);
        }
      } catch (error) {
        console.error('获取首页数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const handleSearch = (searchParams) => {
    // 跳转到搜索页面
    window.location.href = `/search?query=${encodeURIComponent(searchParams.query)}`;
  };
  
  return (
    <Layout>
      <div className="home-page">
        <section className="hero-section">
          <h1>知识库系统</h1>
          <p className="hero-description">
            快速搜索和管理您的知识资源
          </p>
          
          <div className="hero-search">
            <SearchBar onSearch={handleSearch} />
          </div>
        </section>
        
        <section className="features-section">
          <div className="features-grid">
            <Card className="feature-card">
              <h3>浏览文档</h3>
              <p>查看和管理知识库中的所有文档</p>
              <Link to="/documents">
                <Button>查看文档</Button>
              </Link>
            </Card>
            
            <Card className="feature-card">
              <h3>添加知识</h3>
              <p>向知识库添加新的文档和信息</p>
              <Link to="/documents/add">
                <Button>添加文档</Button>
              </Link>
            </Card>
            
            <Card className="feature-card">
              <h3>智能搜索</h3>
              <p>使用自然语言查询知识库</p>
              <Link to="/search">
                <Button>开始搜索</Button>
              </Link>
            </Card>
          </div>
        </section>
        
        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            {recentDocuments.length > 0 && (
              <section className="recent-documents-section">
                <h2>最近添加的文档</h2>
                <div className="recent-documents-list">
                  {recentDocuments.map((document) => (
                    <Card key={document.id} className="recent-document-card">
                      <h3>
                        <Link to={`/documents/${document.id}`}>
                          {document.title}
                        </Link>
                      </h3>
                      <div className="document-meta">
                        {document.source && (
                          <span className="document-source">{document.source}</span>
                        )}
                        <span className="document-date">
                          {new Date(document.date).toLocaleDateString('zh-CN')}
                        </span>
                      </div>
                    </Card>
                  ))}
                </div>
                <div className="view-all-link">
                  <Link to="/documents">查看所有文档</Link>
                </div>
              </section>
            )}
            
            {popularSearches.length > 0 && (
              <section className="popular-searches-section">
                <h2>热门搜索</h2>
                <div className="popular-searches-list">
                  {popularSearches.map((search, index) => (
                    <Link
                      key={index}
                      to={`/search?query=${encodeURIComponent(search.query)}`}
                      className="popular-search-item"
                    >
                      {search.query}
                    </Link>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </Layout>
  );
};

export default HomePage;