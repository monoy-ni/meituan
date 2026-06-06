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
    subtitle: '先定这局是回血、热闹、出片、聊天还是省钱。',
    userText: '我想安排朋友局',
    bootstrap: '朋友局',
  },
  {
    id: 'couple',
    title: '情侣约会',
    subtitle: '不直接问关系阶段，通过聊天判断是升温还是日常出行。',
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

  const replySuggestions = useMemo(() => {
    if (!scene || options.length > 0) return [];
    const nextStep = conversation?.next_step;
    return SUGGESTIONS[scene]?.[nextStep] || [];
  }, [conversation, options.length, scene]);

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
        <header className="hero-band">
          <div>
            <p className="eyebrow">杭州本地一日主题局</p>
            <h1>先聊清楚，再把一整天安排成局</h1>
            <p className="hero-copy">先判断朋友局还是情侣约会，再由 AI 多轮确认需求，最后给出能直接选择、调整和预约的完整路线。</p>
          </div>
          <div className="version-stack">
            <span>后端 v1.5.0</span>
            <span>前端 v0.6.0</span>
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
              <p className="eyebrow">第一步</p>
              <h2>这次先按谁的关系来安排？</h2>
              <p>朋友局要先定这局的定位；情侣约会要从语气里判断是关系升温，还是老夫老妻的日常出行。</p>
            </div>
            <div className="scene-grid">
              {SCENE_CHOICES.map((choice) => (
                <button
                  key={choice.id}
                  type="button"
                  className="scene-card"
                  onClick={() => handleSceneSelect(choice)}
                  disabled={isLoading}
                >
                  <span>{choice.title}</span>
                  <strong>{choice.id === 'friends' ? '先定局的定位' : '先判断关系温度'}</strong>
                  <p>{choice.subtitle}</p>
                </button>
              ))}
            </div>
          </section>
        ) : (
          <section className="flow-shell">
            <aside className="chat-panel">
              <div className="flow-topline">
                <span>{SCENE_CHOICES.find((choice) => choice.id === scene)?.title}</span>
                <b>{STEP_LABELS[appStep]}</b>
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
                <div className="quick-tunes">
                  {QUICK_TUNES.map((tune) => (
                    <button key={tune.label} type="button" onClick={() => handleTune(tune.message)} disabled={isLoading || !sessionId}>
                      {tune.label}
                    </button>
                  ))}
                </div>
              )}

              <form className="chat-form" onSubmit={handleSubmit}>
                <input
                  value={inputText}
                  onChange={(event) => setInputText(event.target.value)}
                  placeholder={selectedOption ? '比如：就这个，帮我订；或者再便宜点' : '把你的想法直接说出来'}
                  disabled={isLoading || !scene}
                />
                <button type="submit" disabled={isLoading || !inputText.trim()}>
                  发送
                </button>
              </form>

              <button type="button" className="text-action" onClick={resetFlow} disabled={isLoading}>
                重新开始
              </button>
            </aside>

            <section className="route-panel" aria-label="方案和预约">
              {visibleOptions.length === 0 ? (
                <div className="empty-route">
                  <p className="eyebrow">等待生成</p>
                  <h2>卡片会在需求确认后出现</h2>
                  <p>先和 AI 聊两三轮：局的定位、预算、时间和体力偏好确定后，这里会出现 3 个完整方案。</p>
                </div>
              ) : (
                <>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">完整方案</p>
                      <h2>选一个局，再继续调整或预约</h2>
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

        {isLoading && <div className="loading-bar">正在整理</div>}
      </main>
    </div>
  );
}

export default App;
