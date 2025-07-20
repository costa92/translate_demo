import React from 'react';
import './Input.css';

/**
 * 输入框组件
 * @param {Object} props - 组件属性
 * @param {string} props.label - 输入框标签
 * @param {string} props.type - 输入框类型
 * @param {string} props.value - 输入框值
 * @param {Function} props.onChange - 值变化处理函数
 * @param {string} [props.placeholder] - 占位符
 * @param {string} [props.error] - 错误信息
 * @param {boolean} [props.required] - 是否必填
 */
const Input = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  required = false,
  ...rest
}) => {
  const id = `input-${label?.toLowerCase().replace(/\s+/g, '-') || Math.random().toString(36).substring(2, 9)}`;
  
  return (
    <div className={`input-container ${error ? 'has-error' : ''}`}>
      {label && (
        <label htmlFor={id} className="input-label">
          {label}
          {required && <span className="required-mark">*</span>}
        </label>
      )}
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="input-field"
        required={required}
        {...rest}
      />
      {error && <div className="input-error">{error}</div>}
    </div>
  );
};

export default Input;