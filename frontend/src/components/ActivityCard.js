
import React from 'react';
import './ActivityCard.css';

const ActivityCard = ({ option, isSelected, onSelect }) => {
  return (
    <div className={`activity-card ${isSelected ? 'selected' : ''}`} onClick={onSelect}>
      <div className="card-header">
        <h4>{option.theme_name}</h4>
        <div className="price-tag">
          ¥{option.estimated_cost_per_person}/人
        </div>
      </div>
      
      <p className="emotional-hook">{option.emotional_hook}</p>
      
      <div className="timeline">
        {option.timeline_items.map((item, index) => (
          <div key={index} className="timeline-item">
            <span className="time">{item.start_time}-{item.end_time}</span>
            <span className="merchant">{item.merchant_name}</span>
            <span className="price">¥{item.price_estimate}</span>
          </div>
        ))}
      </div>
      
      {option.risk_notes && option.risk_notes.length > 0 && (
        <div className="risk-notes">
          ⚠️ {option.risk_notes[0]}
        </div>
      )}
      
      {option.dating_tips && option.dating_tips.length > 0 && (
        <div className="dating-tips">
          💡 {option.dating_tips[0]}
        </div>
      )}
      
      <div className="distance-info">
        📍 全程约 {option.total_distance} 公里
      </div>
    </div>
  );
};

export default ActivityCard;

