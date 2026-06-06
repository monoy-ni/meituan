
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const createSession = async () => {
  const response = await api.post('/sessions');
  return response.data;
};

export const sendChatMessage = async (sessionId, message) => {
  const response = await api.post('/chat', { session_id: sessionId, message });
  return response.data;
};

export const selectOption = async (sessionId, optionId) => {
  const response = await api.post('/select-option', { session_id: sessionId, option_id: optionId });
  return response.data;
};

export const createBookingDraft = async (sessionId, optionId) => {
  const response = await api.post('/create-booking-draft', { session_id: sessionId, option_id: optionId });
  return response.data;
};

export const confirmBooking = async (sessionId, draftId, confirm) => {
  const response = await api.post('/confirm-booking', { session_id: sessionId, draft_id: draftId, confirm });
  return response.data;
};

export const getConversationState = async (sessionId) => {
  const response = await api.get(`/conversation-state/${sessionId}`);
  return response.data;
};

export default api;

