import React from 'react';
import './EmptyState.css';

/**
 * 空状态组件
 * @param {Object} props - 组件属性
 * @param {string} props.message - 显示消息
 * @param {React.ReactNode} [props.icon] - 自定义图标
 * @param {React.ReactNode} [props.action] - 操作按钮或链接
 */
const EmptyState = ({ message, icon, action }) => {
  return (
    <div className="empty-state">
      {icon || (
        <div className="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48">
            <path fill="none" d="M0 0h24v24H0z" />
            <path
              fill="currentColor"
              d="M20 2a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1h16zm-1 2H5v16h14V4zM8 7h8v2H8V7zm0 4h8v2H8v-2zm0 4h5v2H8v-2z"
            />
          </svg>
        </div>
      )}
      <div className="empty-message">{message}</div>
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
};

export default EmptyState;