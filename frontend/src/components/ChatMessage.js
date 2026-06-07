import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ role, content }) => {
  const isUser = role === 'user';

  return (
    <div className={`chat-message ${role}`}>
      <div className="message-avatar" aria-hidden="true">
        {isUser ? '你' : 'AI'}
      </div>
      <div className="message-content">
        <span className="message-role">{isUser ? '你' : '策划助理'}</span>
        <div className="message-text">{content}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
