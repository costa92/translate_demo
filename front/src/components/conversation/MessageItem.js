import React from 'react';
import './MessageItem.css';

/**
 * 消息项组件
 * @param {Object} props - 组件属性
 * @param {Object} props.message - 消息数据
 * @param {boolean} [props.isFirst=false] - 是否为第一条消息
 * @param {boolean} [props.isLast=false] - 是否为最后一条消息
 */
const MessageItem = ({ message, isFirst = false, isLast = false }) => {
  const { role, content, timestamp } = message;
  
  const isUser = role === 'user';
  
  // 格式化时间戳
  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    : '';
  
  return (
    <div className={`message-item ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="user-avatar">用户</div>
        ) : (
          <div className="assistant-avatar">AI</div>
        )}
      </div>
      
      <div className="message-content">
        <div className="message-bubble">
          {content && typeof content === 'string' ? 
            content.split('\n').map((paragraph, index) => (
              paragraph ? <p key={index}>{paragraph}</p> : <br key={index} />
            ))
            : 
            <p>{content || '无内容'}</p>
          }
        </div>
        
        {timestamp && <div className="message-time">{formattedTime}</div>}
      </div>
    </div>
  );
};

export default MessageItem;