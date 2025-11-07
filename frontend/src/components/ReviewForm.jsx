import React, { useState } from 'react';
import { reviewService } from '../services/api';

const ReviewForm = ({ hotelId, onReviewAdded }) => {
  const [formData, setFormData] = useState({
    reviewer_name: '',
    review_text: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.reviewer_name.trim() || !formData.review_text.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const reviewData = {
        hotel_id: hotelId,
        reviewer_name: formData.reviewer_name.trim(),
        review_text: formData.review_text.trim()
      };

      const newReview = await reviewService.createReview(reviewData);
      
      setSuccess('Review submitted successfully!');
      setFormData({ reviewer_name: '', review_text: '' });
      
      if (onReviewAdded) {
        onReviewAdded(newReview);
      }

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit review');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Write a Review</h3>
      
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="reviewer_name">Your Name</label>
          <input
            type="text"
            id="reviewer_name"
            name="reviewer_name"
            value={formData.reviewer_name}
            onChange={handleChange}
            className="form-control"
            placeholder="Enter your name"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="review_text">Your Review</label>
          <textarea
            id="review_text"
            name="review_text"
            value={formData.review_text}
            onChange={handleChange}
            className="form-control textarea"
            placeholder="Share your experience at this hotel..."
            rows="4"
            disabled={loading}
          />
        </div>

        <button 
          type="submit" 
          className="btn"
          disabled={loading}
        >
          {loading ? 'Analyzing & Submitting...' : 'Submit Review'}
        </button>
      </form>
    </div>
  );
};

export default ReviewForm;
