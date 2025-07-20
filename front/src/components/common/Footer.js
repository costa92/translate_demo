import React from 'react';
import './Footer.css';

/**
 * 页面底部组件
 */
const Footer = () => {
  const year = new Date().getFullYear();
  
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <p>&copy; {year} 知识库系统. 保留所有权利.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;