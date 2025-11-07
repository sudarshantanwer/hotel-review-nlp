# Hotel Review Sentiment Analysis Web App

A web application that allows users to submit hotel reviews and automatically analyzes their sentiment using NLP.

## Features

- View list of hotels with average sentiment scores
- Submit reviews for hotels
- Real-time sentiment analysis (Positive/Negative/Neutral)
- View all reviews for each hotel
- Clean, modern UI

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React with Vite
- **NLP**: Hugging Face Transformers (DistilBERT)
- **Database**: SQLite with SQLAlchemy
- **API Calls**: Axios

## Project Structure

```
hotel-review-nlp/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # SQLAlchemy models
│   ├── sentiment.py         # Sentiment analysis logic
│   ├── database.py          # Database configuration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service
│   │   └── App.jsx         # Main app component
│   ├── package.json
│   └── index.html
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## API Endpoints

- `GET /hotels` - Get all hotels
- `GET /hotels/{hotel_id}` - Get hotel details with reviews
- `POST /reviews` - Submit a new review
- `POST /analyze` - Analyze sentiment of text

## Usage

1. **Visit the Application**: Navigate to `http://localhost:5173` in your browser
2. **Browse Hotels**: The homepage displays all available hotels with their current sentiment scores
3. **View Hotel Details**: Click on any hotel card to see detailed information and reviews
4. **Submit Reviews**: Use the review form to add your own hotel experience
5. **Real-time Analysis**: Watch as your review is automatically analyzed for sentiment
6. **Test Sentiment Analyzer**: Visit the "Sentiment Analyzer" tab to test the AI model with custom text

## Live Demo Features

✅ **Hotel Management**: View 5 sample hotels with detailed information  
✅ **Sentiment Analysis**: Real-time sentiment classification using DistilBERT  
✅ **Review System**: Submit and view reviews with automatic sentiment scoring  
✅ **Interactive UI**: Modern, responsive design with smooth transitions  
✅ **API Integration**: Full frontend-backend communication via REST API  
✅ **Data Persistence**: Reviews stored in SQLite database  
✅ **Statistics Dashboard**: View sentiment distribution for each hotel

## Model Information

The app uses the `distilbert-base-uncased-finetuned-sst-2-english` model from Hugging Face for sentiment analysis, which provides:
- Binary sentiment classification (Positive/Negative)
- Confidence scores ranging from 0-100%
- Fast inference suitable for real-time analysis
- Automatic model downloading on first startup

## Testing the Application

### Quick Start Commands

```bash
# Start Backend (Terminal 1)
cd backend
source venv/bin/activate  # or .venv/bin/activate
uvicorn main:app --reload

# Start Frontend (Terminal 2) 
cd frontend
node node_modules/vite/bin/vite.js
```

### Sample Operations

1. **Test Sentiment Analysis**:
   ```bash
   curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "Amazing hotel with excellent service!"}'
   ```

2. **Get Hotels**:
   ```bash
   curl http://localhost:8000/hotels
   ```

3. **Submit Review**:
   ```bash
   curl -X POST "http://localhost:8000/reviews" \
     -H "Content-Type: application/json" \
     -d '{
       "hotel_id": 1,
       "reviewer_name": "John Doe", 
       "review_text": "Great experience! Highly recommend."
     }'
   ```

## Database Management

The SQLite database is located at: `backend/hotel_reviews.db`

### Database Operations

```bash
# Navigate to backend directory
cd backend

# Create tables and seed sample data
python migrations.py create
python migrations.py seed

# Reset database (WARNING: Deletes all data)
python migrations.py reset

# Backup database
python migrations.py backup
```

### Database Files in Code

- **Schema**: `database.py` - SQLAlchemy models
- **Sample Data**: `database_config.py` - Hotels and reviews data
- **Migrations**: `migrations.py` - Database setup and seeding
- **JSON Data**: `data/hotels.json` - Structured data files

## Troubleshooting

- **Backend Issues**: Ensure Python dependencies are installed and virtual environment is activated
- **Frontend Issues**: Verify Node.js is installed and all npm packages are available
- **Port Conflicts**: Backend uses port 8000, frontend uses port 5173
- **Model Loading**: First startup may take longer as the AI model downloads (~268MB)
- **CORS Errors**: Both servers must be running for API calls to work
- **Database Issues**: Run `python migrations.py reset` to recreate the database
