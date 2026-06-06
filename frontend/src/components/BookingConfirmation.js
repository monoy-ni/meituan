import React from 'react';
import './BookingConfirmation.css';

const BookingConfirmation = ({ confirmation }) => {
  const isSuccess = confirmation.status === 'confirmed';
  const title = isSuccess ? '预约已确认' : '预约未执行';

  return (
    <section className={`booking-confirmation ${isSuccess ? 'success' : 'cancelled'}`}>
      <div className="confirmation-header">
        <p>{confirmation.status}</p>
        <h3>{title}</h3>
      </div>

      <p className="confirmation-message">{confirmation.message}</p>

      {isSuccess && confirmation.order_ids?.length > 0 && (
        <div className="order-ids">
          <h4>订单信息</h4>
          <div className="id-list">
            {confirmation.order_ids.map((id) => (
              <span key={id} className="order-id">{id}</span>
            ))}
          </div>
        </div>
      )}

      {isSuccess && confirmation.reservation_ids?.length > 0 && (
        <div className="order-ids">
          <h4>预订信息</h4>
          <div className="id-list">
            {confirmation.reservation_ids.map((id) => (
              <span key={id} className="order-id">{id}</span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

export default BookingConfirmation;
