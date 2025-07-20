import React from 'react';
import './ErrorMessage.css';

/**
 * 错误消息组件
 * @param {Object} props - 组件属性
 * @param {string} props.message - 错误消息
 * @param {Function} [props.onRetry] - 重试回调函数
 */
const ErrorMessage = ({ message, onRetry }) => {
  return (
    <div className="error-container">
      <div className="error-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
          <path fill="none" d="M0 0h24v24H0z" />
          <path
            fill="currentColor"
            d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm-1-5h2v2h-2v-2zm0-8h2v6h-2V7z"
          />
        </svg>
      </div>
      <div className="error-message">{message}</div>
      {onRetry && (
        <button className="error-retry" onClick={onRetry}>
          重试
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;