import React, { useState, useEffect } from 'react';
import { hotelService, summarizationService } from '../services/api';

const ReviewSummaryPage = () => {
  const [hotels, setHotels] = useState([]);
  const [summaries, setSummaries] = useState({});
  const [loading, setLoading] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState({});
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHotels();
  }, []);

  const fetchHotels = async () => {
    try {
      const data = await hotelService.getAllHotels();
      setHotels(data.filter(hotel => hotel.total_reviews > 0)); // Only show hotels with reviews
    } catch (err) {
      setError('Failed to load hotels');
      console.error('Error fetching hotels:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateSummary = async (hotelId) => {
    setLoadingSummary(prev => ({ ...prev, [hotelId]: true }));
    
    try {
      const result = await summarizationService.summarizeReviews(hotelId, {
        maxLength: 150,
        minLength: 30
      });
      setSummaries(prev => ({ ...prev, [hotelId]: result }));
    } catch (err) {
      setSummaries(prev => ({ 
        ...prev, 
        [hotelId]: { 
          summary: 'Failed to generate summary. Please try again.',
          error: 'Generation failed'
        }
      }));
      console.error('Error generating summary:', err);
    } finally {
      setLoadingSummary(prev => ({ ...prev, [hotelId]: false }));
    }
  };

  const generateAllSummaries = async () => {
    const hotelsWithReviews = hotels.filter(hotel => hotel.total_reviews > 0);
    
    for (const hotel of hotelsWithReviews) {
      if (!summaries[hotel.id] && !loadingSummary[hotel.id]) {
        await generateSummary(hotel.id);
        // Add small delay between requests to avoid overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading hotels...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">{error}</div>
      </div>
    );
  }

  const hotelsWithReviews = hotels.filter(hotel => hotel.total_reviews > 0);

  return (
    <div className="container">
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem', color: '#333' }}>Review Summaries</h2>
        <p style={{ color: '#666', marginBottom: '1.5rem' }}>
          AI-generated summaries of guest reviews for each hotel
        </p>
        
        {hotelsWithReviews.length > 0 && (
          <button 
            onClick={generateAllSummaries}
            className="btn btn-primary"
            style={{ marginBottom: '2rem' }}
          >
            Generate All Summaries
          </button>
        )}
      </div>

      {hotelsWithReviews.length === 0 ? (
        <div className="card">
          <p>No hotels with reviews available for summarization.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {hotelsWithReviews.map(hotel => (
            <div key={hotel.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0' }}>{hotel.name}</h3>
                  <p style={{ margin: '0 0 0.5rem 0', color: '#666' }}>📍 {hotel.location}</p>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#888' }}>
                    {hotel.total_reviews} reviews • Average sentiment: {(hotel.average_sentiment * 100).toFixed(0)}%
                  </p>
                </div>
                {!summaries[hotel.id] && !loadingSummary[hotel.id] && (
                  <button 
                    onClick={() => generateSummary(hotel.id)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.9rem' }}
                  >
                    Generate Summary
                  </button>
                )}
              </div>

              {loadingSummary[hotel.id] && (
                <div style={{ 
                  padding: '1.5rem', 
                  textAlign: 'center', 
                  color: '#6c757d',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '0.375rem',
                  border: '1px solid #dee2e6'
                }}>
                  <div style={{ marginBottom: '0.5rem' }}>🤖 Analyzing {hotel.total_reviews} reviews...</div>
                  <div style={{ fontSize: '0.9rem' }}>This may take a moment</div>
                </div>
              )}

              {summaries[hotel.id] && (
                <div style={{ 
                  padding: '1.5rem', 
                  backgroundColor: '#f8f9fa',
                  borderRadius: '0.375rem',
                  border: '1px solid #dee2e6'
                }}>
                  <h4 style={{ margin: '0 0 1rem 0', color: '#495057' }}>📝 Summary</h4>
                  <div style={{ 
                    fontSize: '1rem', 
                    lineHeight: '1.6',
                    color: '#495057',
                    marginBottom: '1rem'
                  }}>
                    {summaries[hotel.id].summary}
                  </div>
                  
                  {summaries[hotel.id].error && (
                    <div style={{ 
                      padding: '0.5rem', 
                      backgroundColor: '#fff3cd', 
                      border: '1px solid #ffeaa7',
                      borderRadius: '0.25rem',
                      color: '#856404',
                      fontSize: '0.9rem',
                      marginBottom: '1rem'
                    }}>
                      Note: {summaries[hotel.id].error}
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
                    <span>📊 Analyzed: {summaries[hotel.id].processed_reviews} of {summaries[hotel.id].total_reviews} reviews</span>
                    {summaries[hotel.id].input_length && (
                      <span>📄 Input length: {summaries[hotel.id].input_length} characters</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReviewSummaryPage;
