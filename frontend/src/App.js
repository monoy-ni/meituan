import React, { useMemo, useState } from 'react';
import {
  confirmBooking,
  createBookingDraft,
  createSession,
  refreshItinerary,
  selectOption,
  sendGuidedChatMessage,
} from './api';
import ActivityCard from './components/ActivityCard';
import BookingConfirmation from './components/BookingConfirmation';
import BookingDraft from './components/BookingDraft';
import ChatMessage from './components/ChatMessage';
import './App.css';

const SCENE_CHOICES = [
  {
    id: 'friends',
    title: '朋友局',
    marker: '局',
    kicker: '3-6 人组局',
    subtitle: '先定这局是回血、热闹、出片、聊天还是省钱。',
    promise: '适合把松散想法快速整理成一条可执行路线。',
    checkpoints: ['玩法定位', '预算边界', '集合范围'],
    userText: '我想安排朋友局',
    bootstrap: '朋友局',
  },
  {
    id: 'couple',
    title: '情侣约会',
    marker: '约',
    kicker: '两人节奏',
    subtitle: '不直接问关系阶段，通过聊天判断是升温还是日常出行。',
    promise: '适合把氛围、体力、仪式感和预约安全一起平衡。',
    checkpoints: ['关系温度', '约会节奏', '安全边界'],
    userText: '我想安排情侣约会',
    bootstrap: '情侣约会',
  },
];

const QUICK_TUNES = [
  { label: '更近一点', message: '更近一点' },
  { label: '便宜点', message: '便宜点' },
  { label: '少走路', message: '少走路，不想太累' },
  { label: '改室内', message: '改室内，雨天也稳' },
  { label: '加拍照点', message: '加拍照点' },
];

const SUGGESTIONS = {
  friends: {
    ask_mood: ['轻松聊聊天', '放松回血', '热闹一点', '拍照出片', '省钱但完整'],
    ask_budget: ['人均150', '人均200', '人均300'],
    ask_time: ['今晚', '明晚', '周末下午'],
  },
  couple: {
    ask_couple_feeling: ['轻松自然一点', '有点怕尴尬', '想升温', '日常放松', '纪念日有仪式感'],
    ask_budget: ['人均200', '人均300', '人均500'],
    ask_time: ['周末下午', '今晚', '明晚'],
  },
};

const STEP_LABELS = {
  entry: '选择人群',
  chatting: '需求确认',
  options: '方案卡片',
  refining: '选择与调整',
  booking_draft: '预约草稿',
  booking_confirmation: '预约结果',
};

const STEP_FLOW = [
  { id: 'chatting', label: '确认' },
  { id: 'options', label: '方案' },
  { id: 'refining', label: '调整' },
  { id: 'booking_draft', label: '草稿' },
  { id: 'booking_confirmation', label: '结果' },
];

const isBookingIntent = (text) => (
  ['预约', '预定', '订', '下单', '就这个', '帮我订', '帮我定'].some((word) => text.includes(word))
);

const inferOptionFromText = (text, optionList) => {
  if (!optionList.length) return null;
  if (['第一个', '第一条', '方案一', '1号', '一号', 'A', 'a'].some((word) => text.includes(word))) return optionList[0];
  if (['第二个', '第二条', '方案二', '2号', '二号', 'B', 'b'].some((word) => text.includes(word))) return optionList[1] || null;
  if (['第三个', '第三条', '方案三', '3号', '三号', 'C', 'c'].some((word) => text.includes(word))) return optionList[2] || null;
  return null;
};

const makeMessage = (role, content) => ({
  id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
  role,
  content,
});

const getCostRange = (optionList) => {
  if (!optionList.length) return '待生成';
  const costs = optionList.map((option) => option.estimated_cost_per_person).filter(Number.isFinite);
  if (!costs.length) return '待确认';
  const min = Math.min(...costs);
  const max = Math.max(...costs);
  return min === max ? `¥${min}/人` : `¥${min}-${max}/人`;
};

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [scene, setScene] = useState(null);
  const [appStep, setAppStep] = useState('entry');
  const [messages, setMessages] = useState([]);
  const [conversation, setConversation] = useState(null);
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [bookingDraft, setBookingDraft] = useState(null);
  const [bookingConfirmation, setBookingConfirmation] = useState(null);
  const [refreshNotes, setRefreshNotes] = useState({});
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState('');
  const [retryAction, setRetryAction] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const visibleOptions = useMemo(() => options.slice(0, 3), [options]);
  const currentScene = useMemo(
    () => SCENE_CHOICES.find((choice) => choice.id === scene) || null,
    [scene],
  );
  const costRange = useMemo(() => getCostRange(visibleOptions), [visibleOptions]);

  const replySuggestions = useMemo(() => {
    if (!scene || options.length > 0) return [];
    const nextStep = conversation?.next_step;
    return SUGGESTIONS[scene]?.[nextStep] || [];
  }, [conversation, options.length, scene]);

  const flowIndex = useMemo(() => {
    const index = STEP_FLOW.findIndex((step) => step.id === appStep);
    if (index >= 0) return index;
    if (appStep === 'entry') return -1;
    return 0;
  }, [appStep]);

  const addMessage = (role, content) => {
    setMessages((current) => [...current, makeMessage(role, content)]);
  };

  const ensureSession = async () => {
    if (sessionId) return sessionId;
    const session = await createSession();
    setSessionId(session.session_id);
    return session.session_id;
  };

  const applyGuidedResponse = (response) => {
    setConversation(response.conversation || null);
    const nextOptions = response.options || [];
    if (nextOptions.length > 0) {
      setOptions(nextOptions);
      setSelectedOption(null);
      setBookingDraft(null);
      setBookingConfirmation(null);
      setRefreshNotes({});
      setAppStep('options');
      return;
    }
    if (!bookingDraft && !bookingConfirmation) {
      setAppStep('chatting');
    }
  };

  const sendGuided = async (
    message,
    { sceneHint = scene, userText = message, appendUser = true, retryable = true } = {},
  ) => {
    const trimmed = message.trim();
    if (!trimmed || isLoading) return null;

    setIsLoading(true);
    setError('');
    if (appendUser) {
      addMessage('user', userText);
    }

    try {
      const nextSessionId = await ensureSession();
      const response = await sendGuidedChatMessage({
        sessionId: nextSessionId,
        message: trimmed,
        sceneHint,
      });
      if (response.message) {
        addMessage('assistant', response.message);
      }
      applyGuidedResponse(response);
      setRetryAction(null);
      return response;
    } catch (err) {
      setError(err.message);
      if (retryable) {
        setRetryAction(() => () => sendGuided(trimmed, {
          sceneHint,
          userText,
          appendUser: false,
          retryable: false,
        }));
      }
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const handleSceneSelect = async (choice) => {
    if (isLoading) return;
    setScene(choice.id);
    setAppStep('chatting');
    setMessages([]);
    setConversation(null);
    setOptions([]);
    setSelectedOption(null);
    setBookingDraft(null);
    setBookingConfirmation(null);
    setRefreshNotes({});
    await sendGuided(choice.bootstrap, {
      sceneHint: choice.id,
      userText: choice.userText,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const text = inputText.trim();
    if (!text) return;
    setInputText('');
    const inferredOption = inferOptionFromText(text, visibleOptions);

    if (isBookingIntent(text)) {
      const targetOption = selectedOption || inferredOption || (visibleOptions.length === 1 ? visibleOptions[0] : null);
      addMessage('user', text);
      if (targetOption) {
        await handleCreateDraft(targetOption, { appendAssistant: true });
      } else {
        setError('先选一个方案，我才能生成预约草稿。');
      }
      return;
    }

    if (inferredOption) {
      addMessage('user', text);
      await handleSelectOption(inferredOption);
      return;
    }

    await sendGuided(text);
  };

  const handleSelectOption = async (option) => {
    if (!sessionId || isLoading) return;
    setIsLoading(true);
    setError('');
    setSelectedOption(option);
    setBookingDraft(null);
    setBookingConfirmation(null);
    setAppStep('refining');
    try {
      await selectOption(sessionId, option.id);
      addMessage('assistant', `已选“${option.theme_name}”。你可以继续说哪里要改，也可以让我生成预约草稿。`);
      setRetryAction(null);
    } catch (err) {
      setError(err.message);
      setRetryAction(() => () => handleSelectOption(option));
    } finally {
      setIsLoading(false);
    }
  };

  const handleTune = async (message) => {
    if (!sessionId || isLoading) return;
    setSelectedOption(null);
    setBookingDraft(null);
    setBookingConfirmation(null);
    setAppStep('refining');
    await sendGuided(message);
  };

  const handleRefresh = async (option) => {
    if (!sessionId || isLoading) return;
    setIsLoading(true);
    setError('');
    try {
      const result = await refreshItinerary(sessionId, option.id);
      setRefreshNotes((current) => ({
        ...current,
        [option.id]: result.message || result.route?.message || '已刷新',
      }));
      setRetryAction(null);
    } catch (err) {
      setError(err.message);
      setRetryAction(() => () => handleRefresh(option));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDraft = async (option = selectedOption, { appendAssistant = true } = {}) => {
    if (!option || isLoading) return;
    setIsLoading(true);
    setError('');
    try {
      const nextSessionId = await ensureSession();
      if (selectedOption?.id !== option.id) {
        await selectOption(nextSessionId, option.id);
        setSelectedOption(option);
      }
      const draft = await createBookingDraft(nextSessionId, option.id);
      setBookingDraft(draft);
      setBookingConfirmation(null);
      setAppStep('booking_draft');
      if (appendAssistant) {
        addMessage('assistant', '我先把预约草稿列出来了，确认前不会支付或下不可逆订单。');
      }
      setRetryAction(null);
    } catch (err) {
      setError(err.message);
      setRetryAction(() => () => handleCreateDraft(option, { appendAssistant: false }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmBooking = async (confirm) => {
    if (!sessionId || !bookingDraft || isLoading) return;
    setIsLoading(true);
    setError('');
    try {
      const confirmation = await confirmBooking(sessionId, bookingDraft.draft_id, confirm);
      setBookingConfirmation(confirmation);
      setBookingDraft(null);
      setAppStep('booking_confirmation');
      addMessage('assistant', confirm ? '预约已 mock 确认，订单信息在右侧。' : '已取消，未执行预约或支付动作。');
      setRetryAction(null);
    } catch (err) {
      setError(err.message);
      setRetryAction(() => () => handleConfirmBooking(confirm));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (retryAction) {
      retryAction();
    } else {
      setError('');
    }
  };

  const resetFlow = () => {
    setSessionId(null);
    setScene(null);
    setAppStep('entry');
    setMessages([]);
    setConversation(null);
    setOptions([]);
    setSelectedOption(null);
    setBookingDraft(null);
    setBookingConfirmation(null);
    setRefreshNotes({});
    setInputText('');
    setError('');
    setRetryAction(null);
  };

  return (
    <div className="app">
      <main className="app-shell">
        <header className="product-bar">
          <div className="brand-lockup">
            <div className="brand-mark" aria-hidden="true">HZ</div>
            <div>
              <p>杭州本地生活 Agent</p>
              <h1>杭州主题局策划台</h1>
            </div>
          </div>

          <div className="status-strip" aria-label="系统状态">
            <span>杭州</span>
            <span>Mock 预约</span>
            <span>后端 v1.5.0</span>
            <span>前端 v0.6.0</span>
            {appStep !== 'entry' && (
              <button type="button" className="ghost-action" onClick={resetFlow} disabled={isLoading}>
                重新开始
              </button>
            )}
          </div>
        </header>

        {error && (
          <section className="error-banner" role="alert">
            <span>{error}</span>
            <button type="button" onClick={handleRetry}>重试</button>
          </section>
        )}

        {appStep === 'entry' ? (
          <section className="entry-panel" aria-label="选择出行人群">
            <div className="entry-copy">
              <span className="surface-label">从关系开始规划</span>
              <h2>把“去哪儿”整理成可选择的本地路线</h2>
              <p>先收齐场景、预算、时间和路线边界，再把杭州本地供给整理成可比较、可调整、可生成预约草稿的方案。</p>

              <div className="decision-metrics" aria-label="规划维度">
                <span>3 套路线</span>
                <span>人均预算</span>
                <span>预约草稿</span>
              </div>
            </div>

            <div className="scene-grid">
              {SCENE_CHOICES.map((choice) => (
                <button
                  key={choice.id}
                  type="button"
                  className={`scene-card scene-card--${choice.id}`}
                  onClick={() => handleSceneSelect(choice)}
                  disabled={isLoading}
                >
                  <span className="scene-icon" aria-hidden="true">{choice.marker}</span>
                  <span className="scene-kicker">{choice.kicker}</span>
                  <strong>{choice.title}</strong>
                  <p>{choice.subtitle}</p>
                  <small>{choice.promise}</small>
                  <span className="scene-checkpoints">
                    {choice.checkpoints.map((checkpoint) => (
                      <em key={checkpoint}>{checkpoint}</em>
                    ))}
                  </span>
                </button>
              ))}
            </div>
          </section>
        ) : (
          <section className="flow-shell">
            <aside className="chat-panel" aria-label="对话控制台">
              <div className="panel-heading">
                <div>
                  <p>对话控制台</p>
                  <h2>{currentScene?.title || '主题局'}</h2>
                </div>
                <span>{STEP_LABELS[appStep]}</span>
              </div>

              <div className="step-track" aria-label="流程进度">
                {STEP_FLOW.map((step, index) => (
                  <span
                    key={step.id}
                    className={[
                      'step-dot',
                      index < flowIndex ? 'is-done' : '',
                      index === flowIndex ? 'is-active' : '',
                    ].filter(Boolean).join(' ')}
                  >
                    {index < flowIndex ? '已' : index + 1}
                    <b>{step.label}</b>
                  </span>
                ))}
              </div>

              <div className="message-list" aria-live="polite">
                {messages.map((message) => (
                  <ChatMessage key={message.id} role={message.role} content={message.content} />
                ))}
              </div>

              {replySuggestions.length > 0 && (
                <div className="suggestion-row" aria-label="快捷回答">
                  {replySuggestions.map((suggestion) => (
                    <button key={suggestion} type="button" onClick={() => sendGuided(suggestion)} disabled={isLoading}>
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}

              {options.length > 0 && (
                <div className="quick-tunes" aria-label="调整路线">
                  {QUICK_TUNES.map((tune) => (
                    <button key={tune.label} type="button" onClick={() => handleTune(tune.message)} disabled={isLoading || !sessionId}>
                      {tune.label}
                    </button>
                  ))}
                </div>
              )}

              <form className="chat-form" onSubmit={handleSubmit}>
                <label className="input-shell">
                  <span aria-hidden="true">输入</span>
                  <input
                    value={inputText}
                    onChange={(event) => setInputText(event.target.value)}
                    placeholder={selectedOption ? '就这个，帮我订；或者再便宜点' : '把你的想法直接说出来'}
                    disabled={isLoading || !scene}
                  />
                </label>
                <button type="submit" disabled={isLoading || !inputText.trim()}>
                  发送
                </button>
              </form>
            </aside>

            <section className="route-panel" aria-label="方案和预约">
              {visibleOptions.length === 0 ? (
                <div className="empty-route">
                  <div className="route-visual" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </div>
                  <p className="surface-label">路线工作台</p>
                  <h2>偏好收齐后生成可比较方案</h2>
                  <div className="empty-grid">
                    <span>预算</span>
                    <span>距离</span>
                    <span>预约</span>
                    <span>风险</span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="surface-label">方案决策区</p>
                      <h2>选一个局，再继续调整或预约</h2>
                    </div>
                    <div className="route-summary-strip" aria-label="方案概览">
                      <span>{visibleOptions.length} 套方案</span>
                      <span>{costRange}</span>
                      <span>可调整</span>
                    </div>
                  </div>

                  <div className="activity-cards">
                    {visibleOptions.map((option) => (
                      <ActivityCard
                        key={option.id}
                        option={option}
                        isSelected={selectedOption?.id === option.id}
                        refreshNote={refreshNotes[option.id]}
                        onSelect={() => handleSelectOption(option)}
                        onRefresh={() => handleRefresh(option)}
                        onBook={() => handleCreateDraft(option)}
                        isLoading={isLoading}
                      />
                    ))}
                  </div>
                </>
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
            </section>
          </section>
        )}

        {isLoading && <div className="loading-bar">正在整理路线</div>}
      </main>
    </div>
  );
}

export default App;
