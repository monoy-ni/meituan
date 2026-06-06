
import React from 'react';
import './BookingDraft.css';

const BookingDraft = ({ draft, onConfirm, onCancel, isLoading }) => {
  return (
    <div className="booking-draft">
      <div className="draft-header">
        <h3>📝 预约确认</h3>
      </div>
      
      <div className="safety-notice">
        {draft.safety_notice}
      </div>
      
      <div className="draft-items">
        {draft.items.map((item, index) => (
          <div key={index} className="draft-item">
            <div className="item-info">
              <span className="item-type">{item.type}</span>
              <span className="item-name">{item.merchant_name}</span>
            </div>
            <div className="item-action">{item.action}</div>
            <div className="item-price">¥{item.estimated_price_per_person}</div>
          </div>
        ))}
      </div>
      
      <div className="draft-footer">
        <div className="payment-mode">
          支付方式：{draft.pay_mode === 'AA_PREPAY' ? 'AA 制预付' : '单人支付'}
        </div>
        
        <div className="draft-actions">
          <button 
            className="btn btn-secondary" 
            onClick={onCancel}
            disabled={isLoading}
          >
            取消
          </button>
          <button 
            className="btn btn-primary" 
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? '确认中...' : '确认预约'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BookingDraft;

