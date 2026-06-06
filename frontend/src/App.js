import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  confirmBooking,
  createBookingDraft,
  createSession,
  generateItineraries,
  getFeaturedItineraries,
  getThemes,
  refreshItinerary,
  selectOption,
  sendChatMessage,
} from './api';
import ActivityCard from './components/ActivityCard';
import BookingConfirmation from './components/BookingConfirmation';
import BookingDraft from './components/BookingDraft';
import './App.css';

const QUICK_TUNES = [
  { label: '更近一点', message: '更近一点' },
  { label: '便宜点', message: '便宜点' },
  { label: '少走路', message: '少走路，不想太累' },
  { label: '改室内', message: '改室内，雨天也稳' },
  { label: '加拍照点', message: '加拍照点' },
];

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [themes, setThemes] = useState([]);
  const [options, setOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [bookingDraft, setBookingDraft] = useState(null);
  const [bookingConfirmation, setBookingConfirmation] = useState(null);
  const [refreshNotes, setRefreshNotes] = useState({});
  const [activeThemeId, setActiveThemeId] = useState(null);
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const visibleOptions = useMemo(() => options.slice(0, 3), [options]);

  const loadHome = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const session = await createSession();
      setSessionId(session.session_id);

      const [themeData, featuredData] = await Promise.all([
        getThemes('hangzhou'),
        getFeaturedItineraries({ city: 'hangzhou', duration: 'half_day', sessionId: session.session_id }),
      ]);

      setThemes(themeData.themes || []);
      setOptions(featuredData.options || []);
      setSelectedOption((featuredData.options || [])[0] || null);
      setBookingDraft(null);
      setBookingConfirmation(null);
      setRefreshNotes({});
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHome();
  }, [loadHome]);

  const applyResponse = (response) => {
    const nextOptions = response.options || [];
    setOptions(nextOptions);
    setSelectedOption(nextOptions[0] || null);
    setBookingDraft(null);
    setBookingConfirmation(null);
    setRefreshNotes({});
  };

  const handleThemeClick = async (theme) => {
    if (!sessionId || isLoading) return;
    setIsLoading(true);
    setError('');
    setActiveThemeId(theme.id);
    try {
      const response = await generateItineraries({
        session_id: sessionId,
        city: 'hangzhou',
        theme_id: theme.id,
        duration: theme.duration,
        experience_tags: theme.experience_tags || [],
      });
      applyResponse(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTune = async (message) => {
    if (!sessionId || isLoading) return;
    setIsLoading(true);
    setError('');
    try {
      const response = await sendChatMessage(sessionId, message);
      applyResponse(response);
      setInputText('');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitTune = (event) => {
    event.preventDefault();
    if (!inputText.trim()) return;
    handleTune(inputText.trim());
  };

  const handleSelectOption = async (option) => {
    if (!sessionId) return;
    setSelectedOption(option);
    setBookingDraft(null);
    setBookingConfirmation(null);
    setError('');
    try {
      await selectOption(sessionId, option.id);
    } catch (err) {
      setError(err.message);
    }
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
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBook = async (option = selectedOption) => {
    if (!sessionId || !option || isLoading) return;
    setIsLoading(true);
    setError('');
    try {
      const draft = await createBookingDraft(sessionId, option.id);
      setSelectedOption(option);
      setBookingDraft(draft);
      setBookingConfirmation(null);
    } catch (err) {
      setError(err.message);
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
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <main className="app-shell">
        <header className="hero-band">
          <div>
            <p className="eyebrow">杭州本地一日主题局</p>
            <h1>今天不用想，选一个杭州局出门</h1>
            <p className="hero-copy">吃、玩、打卡收成一条线，默认少折返，预算和雨天都有兜底。</p>
          </div>
          <div className="version-stack">
            <span>后端 v1.4.0</span>
            <span>前端 v0.5.0</span>
          </div>
        </header>

        {error && (
          <section className="error-banner" role="alert">
            <span>{error}</span>
            <button type="button" onClick={loadHome}>重试</button>
          </section>
        )}

        <section className="theme-row" aria-label="杭州主题">
          {themes.map((theme) => (
            <button
              key={theme.id}
              type="button"
              className={`theme-chip ${activeThemeId === theme.id ? 'active' : ''}`}
              onClick={() => handleThemeClick(theme)}
              disabled={isLoading}
            >
              <span>{theme.name}</span>
              <small>{(theme.experience_tags || []).slice(0, 2).join(' / ')}</small>
            </button>
          ))}
        </section>

        <section className="route-section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">现成局</p>
              <h2>先给你三条能直接走的路线</h2>
            </div>
            <button type="button" className="secondary-action" onClick={loadHome} disabled={isLoading}>
              换一组
            </button>
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
                onBook={() => handleBook(option)}
                isLoading={isLoading}
              />
            ))}
          </div>
        </section>

        <section className="tune-panel">
          <div className="quick-tunes">
            {QUICK_TUNES.map((tune) => (
              <button key={tune.label} type="button" onClick={() => handleTune(tune.message)} disabled={isLoading || !sessionId}>
                {tune.label}
              </button>
            ))}
          </div>
          <form className="tune-form" onSubmit={handleSubmitTune}>
            <input
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              placeholder="比如：人均 150，想走运河，少走路"
              disabled={isLoading || !sessionId}
            />
            <button type="submit" disabled={isLoading || !inputText.trim()}>
              调整
            </button>
          </form>
        </section>

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

        {isLoading && <div className="loading-bar">正在整理路线</div>}
      </main>
    </div>
  );
}

export default App;
