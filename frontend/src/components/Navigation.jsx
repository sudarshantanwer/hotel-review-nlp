import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="nav">
      <div className="container">
        <ul>
          <li>
            <Link 
              to="/" 
              className={location.pathname === '/' ? 'active' : ''}
            >
              Hotels
            </Link>
          </li>
          <li>
            <Link 
              to="/summaries" 
              className={location.pathname === '/summaries' ? 'active' : ''}
            >
              Review Summaries
            </Link>
          </li>
          <li>
            <Link 
              to="/analyze" 
              className={location.pathname === '/analyze' ? 'active' : ''}
            >
              Sentiment Analyzer
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navigation;
