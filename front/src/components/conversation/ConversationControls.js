import React from 'react';
import Button from '../common/Button';
import './ConversationControls.css';

/**
 * 对话控制组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onNewConversation - 开始新对话回调函数
 * @param {Function} [props.onSaveConversation] - 保存对话回调函数
 * @param {boolean} [props.disabled=false] - 是否禁用
 */
const ConversationControls = ({
  onNewConversation,
  onSaveConversation,
  disabled = false
}) => {
  return (
    <div className="conversation-controls">
      <Button
        type="secondary"
        onClick={onNewConversation}
        disabled={disabled}
      >
        开始新对话
      </Button>
      
      {onSaveConversation && (
        <Button
          type="secondary"
          onClick={onSaveConversation}
          disabled={disabled}
        >
          保存对话
        </Button>
      )}
    </div>
  );
};

export default ConversationControls;