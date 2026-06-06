
import React, { useState, useEffect, useRef } from 'react';
import { createSession, sendChatMessage, selectOption, createBookingDraft, confirmBooking } from './api';
import ChatMessage from './components/ChatMessage';
import ActivityCard from './components/ActivityCard';
import BookingDraft from './components/BookingDraft';
import BookingConfirmation from './components/BookingConfirmation';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [bookingDraft, setBookingDraft] = useState(null);
  const [bookingConfirmation, setBookingConfirmation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    try {
      const data = await createSession();
      setSessionId(data.session_id);
      
      setMessages([{
        role: 'assistant',
        content: '你好！我是你的活动规划助手。想和朋友聚聚，还是想安排约会？告诉我你的想法，我来帮你规划！'
      }]);
    } catch (error) {
      console.error('初始化会话失败:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage = { role: 'user', content: inputText };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(sessionId, inputText);
      
      const assistantMessage = {
        role: 'assistant',
        content: response.message
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      if (response.options && response.options.length > 0) {
        setOptions(response.options);
      } else {
        setOptions([]);
      }
      
      setBookingDraft(null);
      setBookingConfirmation(null);
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectOption = async (option) => {
    setSelectedOption(option);
    setIsLoading(true);
    
    try {
      const response = await selectOption(sessionId, option.id);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message
      }]);
      
    } catch (error) {
      console.error('选择方案失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBook = async () => {
    if (!selectedOption) return;
    
    setIsLoading(true);
    try {
      const draft = await createBookingDraft(sessionId, selectedOption.id);
      setBookingDraft(draft);
    } catch (error) {
      console.error('创建预约失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmBooking = async (confirm) => {
    if (!bookingDraft) return;
    
    setIsLoading(true);
    try {
      const confirmation = await confirmBooking(sessionId, bookingDraft.draft_id, confirm);
      setBookingConfirmation(confirmation);
      setBookingDraft(null);
    } catch (error) {
      console.error('确认预约失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="app-container">
        <header className="app-header">
          <h1>🎉 智能活动规划助手</h1>
          <p>为朋友聚会和情侣约会提供最佳方案</p>
        </header>

        <div className="chat-container">
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <ChatMessage key={index} role={msg.role} content={msg.content} />
            ))}
            
            {options.length > 0 && !bookingDraft && !bookingConfirmation && (
              <div className="options-container">
                <h3>为你推荐的活动方案：</h3>
                <div className="activity-cards">
                  {options.map((option, index) => (
                    <ActivityCard
                      key={option.id}
                      option={option}
                      isSelected={selectedOption?.id === option.id}
                      onSelect={() => handleSelectOption(option)}
                    />
                  ))}
                </div>
                {selectedOption && (
                  <div className="action-buttons">
                    <button className="btn btn-primary" onClick={handleBook} disabled={isLoading}>
                      {isLoading ? '处理中...' : '立即预约'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {bookingDraft && (
              <BookingDraft
                draft={bookingDraft}
                onConfirm={() => handleConfirmBooking(true)}
                onCancel={() => handleConfirmBooking(false)}
                isLoading={isLoading}
              />
            )}

            {bookingConfirmation && (
              <BookingConfirmation confirmation={bookingConfirmation} />
            )}

            {isLoading && (
              <div className="loading-indicator">
                <div className="spinner"></div>
                <span>AI 正在思考中...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-input-form" onSubmit={handleSendMessage}>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="告诉我你的想法，比如：今晚想找朋友聚聚..."
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !inputText.trim()}>
              发送
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;

