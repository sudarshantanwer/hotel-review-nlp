"""
Test suite for Hotel Review NLP API
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
import models

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def sample_hotel(db_session):
    """Create a sample hotel for testing"""
    hotel = models.create_hotel(
        db=db_session,
        name="Test Hotel",
        location="Test City, TC",
        description="A test hotel for testing purposes"
    )
    return hotel

class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns success"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

class TestHotels:
    """Test hotel-related endpoints"""
    
    def test_get_hotels_empty(self, setup_database):
        """Test getting hotels when none exist"""
        response = client.get("/hotels")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_hotels_with_data(self, setup_database, sample_hotel):
        """Test getting hotels with data"""
        response = client.get("/hotels")
        assert response.status_code == 200
        hotels = response.json()
        assert len(hotels) >= 1
        assert hotels[0]["name"] == "Test Hotel"
    
    def test_get_hotel_by_id(self, setup_database, sample_hotel):
        """Test getting specific hotel by ID"""
        response = client.get(f"/hotels/{sample_hotel.id}")
        assert response.status_code == 200
        hotel = response.json()
        assert hotel["id"] == sample_hotel.id
        assert hotel["name"] == "Test Hotel"
    
    def test_get_nonexistent_hotel(self, setup_database):
        """Test getting hotel that doesn't exist"""
        response = client.get("/hotels/999")
        assert response.status_code == 404

class TestSentimentAnalysis:
    """Test sentiment analysis endpoints"""
    
    def test_analyze_positive_sentiment(self, setup_database):
        """Test analyzing positive sentiment"""
        response = client.post(
            "/analyze",
            json={"text": "This hotel is absolutely amazing! Great service and beautiful rooms."}
        )
        assert response.status_code == 200
        result = response.json()
        assert "label" in result
        assert "score" in result
        assert "confidence" in result
        assert result["label"] in ["POSITIVE", "NEGATIVE"]
    
    def test_analyze_negative_sentiment(self, setup_database):
        """Test analyzing negative sentiment"""
        response = client.post(
            "/analyze", 
            json={"text": "Terrible hotel with awful service and dirty rooms."}
        )
        assert response.status_code == 200
        result = response.json()
        assert "label" in result
        assert result["label"] in ["POSITIVE", "NEGATIVE"]
    
    def test_analyze_empty_text(self, setup_database):
        """Test analyzing empty text"""
        response = client.post("/analyze", json={"text": ""})
        assert response.status_code == 400
    
    def test_analyze_invalid_request(self, setup_database):
        """Test invalid request format"""
        response = client.post("/analyze", json={})
        assert response.status_code == 422

class TestReviews:
    """Test review-related endpoints"""
    
    def test_create_review(self, setup_database, sample_hotel):
        """Test creating a new review"""
        response = client.post(
            "/reviews",
            json={
                "hotel_id": sample_hotel.id,
                "reviewer_name": "Test Reviewer",
                "review_text": "Great hotel with excellent service!"
            }
        )
        assert response.status_code == 200
        review = response.json()
        assert review["hotel_id"] == sample_hotel.id
        assert review["reviewer_name"] == "Test Reviewer"
        assert "sentiment_label" in review
        assert "sentiment_score" in review
    
    def test_create_review_invalid_hotel(self, setup_database):
        """Test creating review for non-existent hotel"""
        response = client.post(
            "/reviews",
            json={
                "hotel_id": 999,
                "reviewer_name": "Test Reviewer", 
                "review_text": "This hotel doesn't exist"
            }
        )
        assert response.status_code == 404
    
    def test_create_review_missing_fields(self, setup_database):
        """Test creating review with missing fields"""
        response = client.post(
            "/reviews",
            json={"hotel_id": 1}
        )
        assert response.status_code == 422

class TestSummarization:
    """Test review summarization endpoints"""
    
    def test_summarize_reviews_by_id(self, setup_database, sample_hotel, db_session):
        """Test summarizing reviews by hotel ID"""
        # Create a sample review first
        models.create_review(
            db=db_session,
            hotel_id=sample_hotel.id,
            reviewer_name="Test Reviewer",
            review_text="Amazing hotel with great service!",
            sentiment_label="POSITIVE",
            sentiment_score=0.9
        )
        
        response = client.post(
            "/summarize",
            json={
                "hotel_id": sample_hotel.id,
                "max_length": 50,
                "min_length": 10
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert "summary" in result
        assert result["hotel_id"] == sample_hotel.id
    
    def test_summarize_reviews_no_reviews(self, setup_database, sample_hotel):
        """Test summarizing when no reviews exist"""
        response = client.post(
            "/summarize",
            json={"hotel_id": sample_hotel.id}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total_reviews"] == 0
    
    def test_summarize_invalid_hotel(self, setup_database):
        """Test summarizing for non-existent hotel"""
        response = client.post(
            "/summarize",
            json={"hotel_id": 999}
        )
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_concurrent_requests(setup_database, sample_hotel):
    """Test handling concurrent requests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        tasks = []
        for i in range(10):
            task = ac.post(
                "/analyze",
                json={"text": f"Test review number {i}"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            assert response.status_code == 200
            result = response.json()
            assert "label" in result

if __name__ == "__main__":
    pytest.main([__file__])
