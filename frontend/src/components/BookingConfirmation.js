
import React from 'react';
import './BookingConfirmation.css';

const BookingConfirmation = ({ confirmation }) => {
  const isSuccess = confirmation.status === 'confirmed';
  
  return (
    <div className={`booking-confirmation ${isSuccess ? 'success' : 'cancelled'}`}>
      <div className="confirmation-icon">
        {isSuccess ? '✅' : '❌'}
      </div>
      
      <h3>{isSuccess ? '预约成功！' : '预约已取消'}</h3>
      
      <p className="confirmation-message">{confirmation.message}</p>
      
      {isSuccess && confirmation.order_ids && confirmation.order_ids.length > 0 && (
        <div className="order-ids">
          <h4>订单信息：</h4>
          <div className="id-list">
            {confirmation.order_ids.map((id, index) => (
              <span key={index} className="order-id">{id}</span>
            ))}
          </div>
        </div>
      )}
      
      {isSuccess && confirmation.reservation_ids && confirmation.reservation_ids.length > 0 && (
        <div className="order-ids">
          <h4>预订信息：</h4>
          <div className="id-list">
            {confirmation.reservation_ids.map((id, index) => (
              <span key={index} className="order-id">{id}</span>
            ))}
          </div>
        </div>
      )}
      
      {isSuccess && (
        <div className="next-steps">
          <p>🎉 恭喜！你的活动已经安排好了！</p>
          <p className="sub-text">继续在对话框中聊天，可以调整方案或开始新的规划。</p>
        </div>
      )}
    </div>
  );
};

export default BookingConfirmation;

