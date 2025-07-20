import React, { useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import './ConversationHistory.css';

/**
 * 对话历史组件
 * @param {Object} props - 组件属性
 * @param {Array} props.messages - 消息列表
 */
const ConversationHistory = ({ messages = [] }) => {
  const messagesEndRef = useRef(null);
  
  // 自动滚动到最新消息
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  if (messages.length === 0) {
    return (
      <div className="empty-conversation">
        <p>开始新的对话</p>
      </div>
    );
  }
  
  return (
    <div className="conversation-history">
      {messages.map((message, index) => (
        <MessageItem
          key={index}
          message={message}
          isFirst={index === 0}
          isLast={index === messages.length - 1}
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ConversationHistory;