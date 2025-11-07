from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./hotel_reviews.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Hotel(Base):
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    description = Column(Text)
    average_sentiment = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    reviews = relationship("Review", back_populates="hotel")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    reviewer_name = Column(String)
    review_text = Column(Text)
    sentiment_label = Column(String)  # "POSITIVE", "NEGATIVE", "NEUTRAL"
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hotel = relationship("Hotel", back_populates="reviews")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
