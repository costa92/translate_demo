import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

/**
 * 页面顶部导航栏组件
 */
const Header = () => {
  return (
    <header className="header">
      <div className="header-container">
        <div className="logo">
          <Link to="/">知识库系统</Link>
        </div>
        <nav className="nav">
          <ul>
            <li>
              <Link to="/">首页</Link>
            </li>
            <li>
              <Link to="/documents">文档</Link>
            </li>
            <li>
              <Link to="/search">搜索</Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;