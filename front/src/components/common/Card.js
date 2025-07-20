import React from 'react';
import './Card.css';

/**
 * 卡片组件
 * @param {Object} props - 组件属性
 * @param {string} [props.title] - 卡片标题
 * @param {React.ReactNode} props.children - 卡片内容
 * @param {string} [props.className] - 额外的CSS类名
 */
const Card = ({ title, children, className = '', ...rest }) => {
  return (
    <div className={`card ${className}`} {...rest}>
      {title && <div className="card-header">{title}</div>}
      <div className="card-body">{children}</div>
    </div>
  );
};

export default Card;