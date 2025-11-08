import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Navigation from './components/Navigation';
import HotelList from './pages/HotelList';
import HotelDetail from './pages/HotelDetail';
import SentimentAnalyzer from './pages/SentimentAnalyzer';
import ReviewSummaryPage from './pages/ReviewSummaryPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <Navigation />
        
        <Routes>
          <Route path="/" element={<HotelList />} />
          <Route path="/hotel/:id" element={<HotelDetail />} />
          <Route path="/analyze" element={<SentimentAnalyzer />} />
          <Route path="/summaries" element={<ReviewSummaryPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
