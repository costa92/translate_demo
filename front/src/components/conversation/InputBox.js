import React, { useState } from 'react';
import Button from '../common/Button';
import './InputBox.css';

/**
 * 输入框组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onSend - 发送消息回调函数
 * @param {boolean} [props.disabled=false] - 是否禁用
 * @param {boolean} [props.loading=false] - 是否正在加载
 */
const InputBox = ({ onSend, disabled = false, loading = false }) => {
  const [message, setMessage] = useState('');
  
  const handleChange = (e) => {
    setMessage(e.target.value);
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!message.trim() || disabled || loading) {
      return;
    }
    
    onSend(message.trim());
    setMessage('');
  };
  
  // 处理按下 Enter 键发送消息（Shift+Enter 换行）
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <form className="input-box" onSubmit={handleSubmit}>
      <textarea
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="输入您的问题..."
        className="input-textarea"
        disabled={disabled || loading}
      />
      
      <div className="input-actions">
        <span className="input-tip">按 Enter 发送，Shift+Enter 换行</span>
        <Button
          type="primary"
          disabled={!message.trim() || disabled}
          loading={loading}
        >
          发送
        </Button>
      </div>
    </form>
  );
};

export default InputBox;