
import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ role, content }) => {
  return (
    <div className={`chat-message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? '你' : 'AI'}
      </div>
      <div className="message-content">
        <div className="message-text">{content}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
