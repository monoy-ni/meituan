import React from 'react';
import './BookingDraft.css';

const payModeLabel = (mode) => {
  const normalized = String(mode || '').toLowerCase();
  if (normalized === 'aa_prepay') return 'AA 制预付';
  if (normalized === 'pay_later') return '到店后支付';
  return '单人支付';
};

const BookingDraft = ({ draft, onConfirm, onCancel, isLoading }) => {
  return (
    <section className="booking-draft">
      <div className="draft-header">
        <div className="draft-title-lockup">
          <span className="draft-icon" aria-hidden="true">安</span>
          <div>
            <p className="draft-kicker">确认前安全检查</p>
            <h3>预约草稿已生成</h3>
          </div>
        </div>
        <span className="draft-status">{draft.data_confidence || 'seed'}</span>
      </div>

      <div className="safety-notice">
        <span>{draft.safety_notice}</span>
      </div>

      <div className="draft-meta">
        <span>{payModeLabel(draft.pay_mode)}</span>
        <span>{draft.data_source || 'seed/mock'}</span>
        {draft.expires_at && <span>{draft.expires_at}</span>}
        {draft.updated_at && <span>{draft.updated_at}</span>}
      </div>

      <div className="draft-items">
        {draft.items.map((item) => (
          <div key={`${item.merchant_id}-${item.type}`} className="draft-item">
            <div className="item-info">
              <span className="item-type">{item.type}</span>
              <strong>{item.merchant_name}</strong>
              <p>{item.action}</p>
            </div>
            <div className="item-price">¥{item.estimated_price_per_person}</div>
          </div>
        ))}
      </div>

      <div className="draft-actions">
        <button type="button" className="btn-secondary" onClick={onCancel} disabled={isLoading}>
          取消
        </button>
        <button type="button" className="btn-primary" onClick={onConfirm} disabled={isLoading}>
          {isLoading ? '确认中' : '确认预约'}
        </button>
      </div>
    </section>
  );
};

export default BookingDraft;
