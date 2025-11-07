import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

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

export default api;
