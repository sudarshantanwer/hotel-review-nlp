import React, { useState } from 'react';
import { summarizationService } from '../services/api';

const ReviewSummary = ({ hotelId, hotelName, totalReviews }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);

  const handleSummarize = async () => {
    if (totalReviews === 0) {
      setError('No reviews available to summarize');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await summarizationService.summarizeReviews(hotelId, {
        maxLength: 200,
        minLength: 50
      });
      setSummary(result);
      setExpanded(true);
    } catch (err) {
      setError('Failed to generate summary. Please try again.');
      console.error('Error generating summary:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = () => {
    setExpanded(!expanded);
  };

  if (totalReviews === 0) {
    return null;
  }

  return (
    <div className="card" style={{ marginBottom: '1.5rem', backgroundColor: '#f8f9fa' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, color: '#495057' }}>
          📝 Review Summary
        </h3>
        {!summary && (
          <button 
            onClick={handleSummarize}
            disabled={loading}
            className="btn btn-primary"
            style={{ fontSize: '0.9rem' }}
          >
            {loading ? 'Generating...' : 'Generate Summary'}
          </button>
        )}
        {summary && (
          <button 
            onClick={toggleExpanded}
            className="btn btn-secondary"
            style={{ fontSize: '0.9rem' }}
          >
            {expanded ? 'Hide Summary' : 'Show Summary'}
          </button>
        )}
      </div>

      {error && (
        <div style={{ 
          padding: '0.75rem', 
          backgroundColor: '#f8d7da', 
          border: '1px solid #f5c6cb',
          borderRadius: '0.375rem',
          color: '#721c24',
          marginBottom: '1rem'
        }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ 
          padding: '1.5rem', 
          textAlign: 'center', 
          color: '#6c757d',
          backgroundColor: '#fff',
          borderRadius: '0.375rem',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ marginBottom: '0.5rem' }}>🤖 AI is analyzing {totalReviews} reviews...</div>
          <div style={{ fontSize: '0.9rem' }}>This may take a moment</div>
        </div>
      )}

      {summary && expanded && (
        <div style={{ 
          padding: '1.5rem', 
          backgroundColor: '#fff',
          borderRadius: '0.375rem',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ 
            fontSize: '1rem', 
            lineHeight: '1.6',
            color: '#495057',
            marginBottom: '1rem'
          }}>
            {summary.summary}
          </div>
          
          {summary.error && (
            <div style={{ 
              padding: '0.5rem', 
              backgroundColor: '#fff3cd', 
              border: '1px solid #ffeaa7',
              borderRadius: '0.25rem',
              color: '#856404',
              fontSize: '0.9rem',
              marginBottom: '1rem'
            }}>
              Note: {summary.error}
            </div>
          )}

          <div style={{ 
            display: 'flex', 
            gap: '1rem', 
            fontSize: '0.85rem', 
            color: '#6c757d',
            paddingTop: '1rem',
            borderTop: '1px solid #dee2e6'
          }}>
            <span>📊 Analyzed: {summary.processed_reviews} of {summary.total_reviews} reviews</span>
            {summary.input_length && (
              <span>📄 Input length: {summary.input_length} characters</span>
            )}
          </div>
        </div>
      )}

      {!summary && !loading && !error && (
        <div style={{ 
          padding: '1rem', 
          textAlign: 'center', 
          color: '#6c757d',
          fontSize: '0.95rem'
        }}>
          Get an AI-generated summary of all {totalReviews} reviews for this hotel
        </div>
      )}
    </div>
  );
};

export default ReviewSummary;
