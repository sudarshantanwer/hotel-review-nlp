import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Hotels API
export const hotelService = {
  // Get all hotels
  getAllHotels: async () => {
    const response = await api.get('/hotels');
    return response.data;
  },

  // Get hotel by ID with reviews
  getHotelById: async (id) => {
    const response = await api.get(`/hotels/${id}`);
    return response.data;
  },
};

// Reviews API
export const reviewService = {
  // Create a new review
  createReview: async (reviewData) => {
    const response = await api.post('/reviews', reviewData);
    return response.data;
  },
};

// Sentiment Analysis API
export const sentimentService = {
  // Analyze sentiment of text
  analyzeSentiment: async (text) => {
    const response = await api.post('/analyze', { text });
    return response.data;
  },
};

// Summarization API
export const summarizationService = {
  // Summarize reviews for a hotel
  summarizeReviews: async (hotelId, options = {}) => {
    const requestData = {
      hotel_id: hotelId,
      max_length: options.maxLength || 100,
      min_length: options.minLength || 20
    };
    const response = await api.post('/summarize', requestData);
    return response.data;
  },
};

export default api;
