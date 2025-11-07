from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db, Hotel, Review
from sentiment import sentiment_analyzer
import models

# Initialize FastAPI app
app = FastAPI(title="Hotel Review Sentiment Analysis API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class SentimentAnalysisRequest(BaseModel):
    text: str

class SentimentAnalysisResponse(BaseModel):
    text: str
    label: str
    score: float
    confidence: float

class ReviewCreateRequest(BaseModel):
    hotel_id: int
    reviewer_name: str
    review_text: str

class ReviewResponse(BaseModel):
    id: int
    hotel_id: int
    reviewer_name: str
    review_text: str
    sentiment_label: str
    sentiment_score: float
    created_at: str

class HotelResponse(BaseModel):
    id: int
    name: str
    location: str
    description: str
    average_sentiment: float
    total_reviews: int
    
class HotelDetailResponse(BaseModel):
    id: int
    name: str
    location: str
    description: str
    average_sentiment: float
    total_reviews: int
    reviews: List[ReviewResponse]

@app.on_event("startup")
async def startup_event():
    """Initialize database with sample data"""
    db = next(get_db())
    models.seed_sample_hotels(db)
    db.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hotel Review Sentiment Analysis API"}

@app.post("/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """Analyze sentiment of text"""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    result = sentiment_analyzer.analyze_sentiment(request.text)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {result['error']}")
    
    return SentimentAnalysisResponse(
        text=request.text,
        label=result["label"],
        score=result["score"],
        confidence=result["confidence"]
    )

@app.get("/hotels", response_model=List[HotelResponse])
async def get_hotels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all hotels"""
    hotels = models.get_hotels(db, skip=skip, limit=limit)
    return [
        HotelResponse(
            id=hotel.id,
            name=hotel.name,
            location=hotel.location,
            description=hotel.description,
            average_sentiment=hotel.average_sentiment,
            total_reviews=hotel.total_reviews
        )
        for hotel in hotels
    ]

@app.get("/hotels/{hotel_id}", response_model=HotelDetailResponse)
async def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    """Get hotel details with all reviews"""
    hotel = models.get_hotel(db, hotel_id=hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    reviews = models.get_hotel_reviews(db, hotel_id=hotel_id)
    
    return HotelDetailResponse(
        id=hotel.id,
        name=hotel.name,
        location=hotel.location,
        description=hotel.description,
        average_sentiment=hotel.average_sentiment,
        total_reviews=hotel.total_reviews,
        reviews=[
            ReviewResponse(
                id=review.id,
                hotel_id=review.hotel_id,
                reviewer_name=review.reviewer_name,
                review_text=review.review_text,
                sentiment_label=review.sentiment_label,
                sentiment_score=review.sentiment_score,
                created_at=review.created_at.isoformat()
            )
            for review in reviews
        ]
    )

@app.post("/reviews", response_model=ReviewResponse)
async def create_review(request: ReviewCreateRequest, db: Session = Depends(get_db)):
    """Create a new review with sentiment analysis"""
    # Check if hotel exists
    hotel = models.get_hotel(db, hotel_id=request.hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Analyze sentiment
    sentiment_result = sentiment_analyzer.analyze_sentiment(request.review_text)
    
    if "error" in sentiment_result:
        raise HTTPException(
            status_code=500, 
            detail=f"Sentiment analysis failed: {sentiment_result['error']}"
        )
    
    # Create review
    review = models.create_review(
        db=db,
        hotel_id=request.hotel_id,
        reviewer_name=request.reviewer_name,
        review_text=request.review_text,
        sentiment_label=sentiment_result["label"],
        sentiment_score=sentiment_result["score"]
    )
    
    return ReviewResponse(
        id=review.id,
        hotel_id=review.hotel_id,
        reviewer_name=review.reviewer_name,
        review_text=review.review_text,
        sentiment_label=review.sentiment_label,
        sentiment_score=review.sentiment_score,
        created_at=review.created_at.isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
