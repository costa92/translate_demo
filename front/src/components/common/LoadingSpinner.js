import React from 'react';
import './LoadingSpinner.css';

/**
 * 加载中指示器组件
 * @param {Object} props - 组件属性
 * @param {string} [props.size='medium'] - 大小 (small, medium, large)
 * @param {string} [props.text] - 加载文本
 */
const LoadingSpinner = ({ size = 'medium', text }) => {
  return (
    <div className="loading-container">
      <div className={`spinner ${size}`}></div>
      {text && <div className="loading-text">{text}</div>}
    </div>
  );
};

export default LoadingSpinner;