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
        <div>
          <p className="draft-kicker">预约草稿</p>
          <h3>确认前不会支付或下不可逆订单</h3>
        </div>
        <span>{draft.data_confidence || 'seed'}</span>
      </div>

      <div className="safety-notice">{draft.safety_notice}</div>

      <div className="draft-meta">
        <span>支付方式：{payModeLabel(draft.pay_mode)}</span>
        <span>数据来源：{draft.data_source || 'seed/mock'}</span>
        {draft.updated_at && <span>更新时间：{draft.updated_at}</span>}
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
