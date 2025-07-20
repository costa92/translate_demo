import React from 'react';
import Header from './Header';
import Footer from './Footer';
import './Layout.css';

/**
 * 页面布局组件
 * @param {Object} props - 组件属性
 * @param {React.ReactNode} props.children - 子组件
 */
const Layout = ({ children }) => {
  return (
    <div className="layout">
      <Header />
      <main className="main-content">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;