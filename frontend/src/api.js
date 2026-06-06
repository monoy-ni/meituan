import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const request = async (promise) => {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    const detail = error.response?.data?.detail;
    const message = typeof detail === 'string' ? detail : error.message;
    throw new Error(message || '请求失败，请稍后重试');
  }
};

export const createSession = async () => request(api.post('/sessions'));

export const getThemes = async (city = 'hangzhou') =>
  request(api.get('/themes', { params: { city } }));

export const getFeaturedItineraries = async ({ city = 'hangzhou', duration = 'half_day', date, sessionId } = {}) =>
  request(api.get('/featured-itineraries', {
    params: {
      city,
      duration,
      date,
      session_id: sessionId,
    },
  }));

export const generateItineraries = async (payload) =>
  request(api.post('/itineraries/generate', payload));

export const refreshItinerary = async (sessionId, optionId) =>
  request(api.post(`/itineraries/${optionId}/refresh`, { session_id: sessionId }));

export const sendChatMessage = async (sessionId, message) =>
  request(api.post('/chat', { session_id: sessionId, message }));

export const selectOption = async (sessionId, optionId) =>
  request(api.post('/select-option', { session_id: sessionId, option_id: optionId }));

export const createBookingDraft = async (sessionId, optionId) =>
  request(api.post('/create-booking-draft', { session_id: sessionId, option_id: optionId }));

export const confirmBooking = async (sessionId, draftId, confirm) =>
  request(api.post('/confirm-booking', { session_id: sessionId, draft_id: draftId, confirm }));

export const getConversationState = async (sessionId) =>
  request(api.get(`/conversation-state/${sessionId}`));

export default api;
