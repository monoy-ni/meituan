import React from 'react';
import './ActivityCard.css';

const TYPE_LABELS = {
  dining: '吃',
  activity: '玩',
  checkin: '打卡',
  relax: '收尾',
  nightlife: '夜间',
  hotel: '夜宿',
  gift: '礼物',
};

const confidenceLabel = {
  seed: 'Seed 估算',
  cache: '缓存估算',
  realtime: '实时确认',
};

const ActivityCard = ({ option, isSelected, refreshNote, onSelect, onRefresh, onBook, isLoading }) => {
  const firstCluster = option.timeline_items?.find((item) => item.area_cluster)?.area_cluster || 'hangzhou';
  const experienceCard = option.experience_card || {};
  const experienceFlow = Array.isArray(experienceCard.flow) ? experienceCard.flow : [];
  const vibeTags = Array.isArray(experienceCard.vibe_tags) ? experienceCard.vibe_tags : [];
  const signatureMoments = Array.isArray(experienceCard.signature_moments) ? experienceCard.signature_moments : [];
  const hostTips = Array.isArray(experienceCard.host_tips) ? experienceCard.host_tips : [];

  return (
    <article className={`activity-card ${isSelected ? 'selected' : ''}`}>
      <div className="card-topline">
        <span className="cluster-pill">{firstCluster.replaceAll('_', ' ')}</span>
        <span className="confidence-pill">{confidenceLabel[option.data_confidence] || option.data_confidence}</span>
      </div>

      <div className="card-title-row">
        <h3>{option.theme_name}</h3>
        <strong>¥{option.estimated_cost_per_person}/人</strong>
      </div>

      <p className="route-story">{option.route_story || option.emotional_hook}</p>

      <div className="route-metrics">
        <span>{option.effort_level}体力</span>
        <span>{option.total_distance}km</span>
        <span>{option.booking_readiness}</span>
      </div>

      <ol className="timeline-list">
        {(option.timeline_items || []).map((item) => (
          <li key={`${option.id}-${item.merchant_id}-${item.start_time}`}>
            <time>{item.start_time}-{item.end_time}</time>
            <div>
              <span className="type-tag">{TYPE_LABELS[item.type] || item.type}</span>
              <strong>{item.merchant_name}</strong>
              <p>{item.why_this_fits}</p>
              {item.checkin_hint && <small>{item.checkin_hint}</small>}
            </div>
            <b>¥{item.price_estimate}</b>
          </li>
        ))}
      </ol>

      {experienceCard.title && (
        <section className="experience-card-panel">
          <div className="experience-heading">
            <span>{experienceCard.designer === 'couple-date-designer' ? '约会玩法卡' : '主题局玩法卡'}</span>
            <strong>{experienceCard.title}</strong>
          </div>
          {experienceCard.theme_line && <p className="experience-line">{experienceCard.theme_line}</p>}
          {vibeTags.length > 0 && (
            <div className="experience-tags">
              {vibeTags.slice(0, 4).map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>
          )}
          {experienceCard.play_style && (
            <div className="experience-style">
              <span>玩法</span>
              <p>{experienceCard.play_style}</p>
            </div>
          )}
          {experienceFlow.length > 0 && (
            <ol className="experience-flow">
              {experienceFlow.slice(0, 4).map((flowItem) => (
                <li key={`${option.id}-${flowItem.merchant_id}-${flowItem.role}`}>
                  <span>{flowItem.role}</span>
                  <p>{flowItem.experience}</p>
                </li>
              ))}
            </ol>
          )}
          {signatureMoments.length > 0 && (
            <div className="experience-style">
              <span>记忆点</span>
              <p>{signatureMoments.slice(0, 3).join(' / ')}</p>
            </div>
          )}
          {hostTips.length > 0 && (
            <div className="experience-style">
              <span>{experienceCard.designer === 'couple-date-designer' ? '提醒' : '组局'}</span>
              <p>{hostTips.slice(0, 3).join(' / ')}</p>
            </div>
          )}
        </section>
      )}

      <div className="info-block">
        <span>通勤</span>
        <p>{option.transport_summary}</p>
      </div>

      {option.gain_points?.length > 0 && (
        <div className="tag-row">
          {option.gain_points.slice(0, 3).map((point) => (
            <span key={point}>{point}</span>
          ))}
        </div>
      )}

      {option.checkin_points?.length > 0 && (
        <div className="info-block">
          <span>打卡点</span>
          <p>{option.checkin_points.join(' / ')}</p>
        </div>
      )}

      {option.fallbacks?.length > 0 && (
        <div className="fallback-list">
          {option.fallbacks.slice(0, 3).map((fallback) => (
            <p key={fallback}>{fallback}</p>
          ))}
        </div>
      )}

      {option.risk_notes?.length > 0 && (
        <div className="data-note">{option.risk_notes[0]}</div>
      )}

      {refreshNote && <div className="refresh-note">{refreshNote}</div>}

      <div className="card-actions">
        <button type="button" className="secondary-action" onClick={onRefresh} disabled={isLoading}>
          刷新
        </button>
        <button type="button" className="secondary-action" onClick={onSelect} disabled={isLoading}>
          {isSelected ? '已选择' : '选择'}
        </button>
        <button type="button" className="primary-action" onClick={onBook} disabled={isLoading}>
          预约草稿
        </button>
      </div>
    </article>
  );
};

export default ActivityCard;
