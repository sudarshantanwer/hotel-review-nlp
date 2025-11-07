from sqlalchemy.orm import Session
from database import Hotel, Review
from typing import List, Optional

def get_hotels(db: Session, skip: int = 0, limit: int = 100) -> List[Hotel]:
    """Get all hotels with pagination"""
    return db.query(Hotel).offset(skip).limit(limit).all()

def get_hotel(db: Session, hotel_id: int) -> Optional[Hotel]:
    """Get a specific hotel by ID"""
    return db.query(Hotel).filter(Hotel.id == hotel_id).first()

def create_hotel(db: Session, name: str, location: str, description: str = "") -> Hotel:
    """Create a new hotel"""
    db_hotel = Hotel(
        name=name,
        location=location,
        description=description
    )
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

def create_review(
    db: Session,
    hotel_id: int,
    reviewer_name: str,
    review_text: str,
    sentiment_label: str,
    sentiment_score: float
) -> Review:
    """Create a new review"""
    db_review = Review(
        hotel_id=hotel_id,
        reviewer_name=reviewer_name,
        review_text=review_text,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score
    )
    db.add(db_review)
    
    # Update hotel's average sentiment and review count
    hotel = get_hotel(db, hotel_id)
    if hotel:
        # Calculate new average sentiment
        total_score = hotel.average_sentiment * hotel.total_reviews
        total_score += sentiment_score
        hotel.total_reviews += 1
        hotel.average_sentiment = total_score / hotel.total_reviews
        
        db.commit()
        db.refresh(db_review)
    
    return db_review

def get_hotel_reviews(db: Session, hotel_id: int) -> List[Review]:
    """Get all reviews for a specific hotel"""
    return db.query(Review).filter(Review.hotel_id == hotel_id).all()

def seed_sample_hotels(db: Session):
    """Seed database with sample hotels if empty"""
    if db.query(Hotel).first():
        return  # Already seeded
    
    sample_hotels = [
        {
            "name": "Grand Plaza Hotel",
            "location": "New York, NY",
            "description": "Luxury hotel in the heart of Manhattan with stunning city views."
        },
        {
            "name": "Ocean Breeze Resort",
            "location": "Miami, FL", 
            "description": "Beachfront resort with world-class amenities and spa services."
        },
        {
            "name": "Mountain View Lodge",
            "location": "Aspen, CO",
            "description": "Cozy mountain lodge perfect for skiing and outdoor adventures."
        },
        {
            "name": "Downtown Business Hotel",
            "location": "Chicago, IL",
            "description": "Modern business hotel with conference facilities and fine dining."
        },
        {
            "name": "Historic Boutique Inn",
            "location": "Charleston, SC",
            "description": "Charming historic inn with southern hospitality and antique furnishings."
        }
    ]
    
    for hotel_data in sample_hotels:
        create_hotel(db, **hotel_data)
