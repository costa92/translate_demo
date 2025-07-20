import React from 'react';
import './Button.css';

/**
 * 按钮组件
 * @param {Object} props - 组件属性
 * @param {string} [props.type='primary'] - 按钮类型 (primary, secondary, danger)
 * @param {string} [props.size='medium'] - 按钮大小 (small, medium, large)
 * @param {boolean} [props.disabled=false] - 是否禁用
 * @param {boolean} [props.loading=false] - 是否显示加载状态
 * @param {Function} props.onClick - 点击事件处理函数
 * @param {React.ReactNode} props.children - 按钮内容
 */
const Button = ({
  type = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  onClick,
  children,
  ...rest
}) => {
  const buttonClass = `button ${type} ${size} ${disabled || loading ? 'disabled' : ''}`;
  
  const handleClick = (e) => {
    if (disabled || loading) return;
    if (onClick) onClick(e);
  };
  
  return (
    <button
      className={buttonClass}
      onClick={handleClick}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <span className="loading-spinner"></span>}
      {children}
    </button>
  );
};

export default Button;