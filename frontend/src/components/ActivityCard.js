import React from 'react';
import './ActivityCard.css';

const TYPE_META = {
  dining: { label: '吃' },
  activity: { label: '玩' },
  checkin: { label: '打卡' },
  relax: { label: '收尾' },
  nightlife: { label: '夜间' },
  hotel: { label: '夜宿' },
  gift: { label: '礼物' },
};

const confidenceLabel = {
  seed: 'Seed 估算',
  cache: '缓存估算',
  realtime: '实时确认',
};

const readinessLabel = {
  ready: '可预约',
  needs_confirmation: '需确认',
  partial: '部分可约',
};

const formatCluster = (cluster) => String(cluster || 'hangzhou').replaceAll('_', ' ');

const ActivityCard = ({ option, isSelected, refreshNote, onSelect, onRefresh, onBook, isLoading }) => {
  const timelineItems = Array.isArray(option.timeline_items) ? option.timeline_items : [];
  const firstCluster = timelineItems.find((item) => item.area_cluster)?.area_cluster || 'hangzhou';
  const experienceCard = option.experience_card || {};
  const experienceFlow = Array.isArray(experienceCard.flow) ? experienceCard.flow : [];
  const vibeTags = Array.isArray(experienceCard.vibe_tags) ? experienceCard.vibe_tags : [];
  const signatureMoments = Array.isArray(experienceCard.signature_moments) ? experienceCard.signature_moments : [];
  const hostTips = Array.isArray(experienceCard.host_tips) ? experienceCard.host_tips : [];
  const readiness = readinessLabel[option.booking_readiness] || option.booking_readiness || '待确认';

  return (
    <article className={`activity-card ${isSelected ? 'selected' : ''}`}>
      <div className="card-topline">
        <span className="cluster-pill">{formatCluster(firstCluster)}</span>
        <span className="confidence-pill">{confidenceLabel[option.data_confidence] || option.data_confidence || '估算'}</span>
      </div>

      <div className="card-title-row">
        <div>
          <h3>{option.theme_name}</h3>
          <p className="route-story">{option.route_story || option.emotional_hook}</p>
        </div>
        <strong className="price-lockup">¥{option.estimated_cost_per_person}/人</strong>
      </div>

      <div className="route-metrics">
        <span>{option.effort_level}体力</span>
        <span>{option.total_distance}km</span>
        <span>{readiness}</span>
      </div>

      <ol className="timeline-rail" aria-label="路线时间线">
        {timelineItems.map((item, index) => {
          const typeMeta = TYPE_META[item.type] || { label: item.type };
          return (
            <li key={`${option.id}-${item.merchant_id}-${item.start_time}`}>
              <div className="rail-marker" aria-hidden="true">{index + 1}</div>
              <div className="timeline-main">
                <div className="timeline-time">
                  <time>{item.start_time}-{item.end_time}</time>
                </div>
                <div className="timeline-title-row">
                  <span className="type-tag">{typeMeta.label}</span>
                  <strong>{item.merchant_name}</strong>
                  <b>¥{item.price_estimate}</b>
                </div>
                <p>{item.why_this_fits}</p>
                {item.checkin_hint && <small>{item.checkin_hint}</small>}
              </div>
            </li>
          );
        })}
      </ol>

      {experienceCard.title && (
        <section className="experience-card-panel">
          <div className="experience-heading">
            <span>{experienceCard.designer === 'couple-date-designer' ? '约会玩法亮点' : '主题局玩法亮点'}</span>
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

      <div className="detail-grid">
        {option.transport_summary && (
          <div className="info-block">
            <span>通勤</span>
            <p>{option.transport_summary}</p>
          </div>
        )}

        {option.checkin_points?.length > 0 && (
          <div className="info-block">
            <span>打卡</span>
            <p>{option.checkin_points.join(' / ')}</p>
          </div>
        )}
      </div>

      {option.gain_points?.length > 0 && (
        <div className="tag-row">
          {option.gain_points.slice(0, 3).map((point) => (
            <span key={point}>{point}</span>
          ))}
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
