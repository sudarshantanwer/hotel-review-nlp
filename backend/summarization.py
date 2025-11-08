from transformers import pipeline
from typing import Dict, Any, List
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReviewSummarizer:
    def __init__(self):
        """Initialize the text summarization pipeline"""
        self.summarizer = None
        self.model_name = None
        
        # Try to load models in order of preference
        models_to_try = [
            "t5-small",  # Start with smaller model first
            "facebook/bart-large-cnn",  # Fallback to larger model if needed
        ]
        
        for model in models_to_try:
            try:
                logger.info(f"Attempting to load model: {model}")
                
                # Set cache directory to avoid permission issues
                os.environ['TRANSFORMERS_CACHE'] = '/tmp/transformers_cache'
                
                self.summarizer = pipeline(
                    "summarization",
                    model=model,
                    device=-1,  # Force CPU usage for better compatibility
                    max_length=512,  # Limit max length to avoid memory issues
                )
                self.model_name = model
                logger.info(f"Successfully loaded summarization model: {model}")
                break
                
            except Exception as e:
                logger.error(f"Failed to load model {model}: {e}")
                continue
        
        if not self.summarizer:
            logger.error("Failed to load any summarization model, using fallback method")
    
    def _simple_extractive_summary(self, reviews: List[str], max_sentences: int = 3) -> str:
        """
        Simple extractive summarization as fallback when model is not available
        """
        if not reviews:
            return "No reviews available to summarize."
        
        # Combine all reviews
        all_text = " ".join([r.strip() for r in reviews if r and len(r.strip()) > 10])
        
        if not all_text:
            return "Insufficient review content to generate a summary."
        
        # Split into sentences (simple approach)
        sentences = []
        for review in reviews:
            if review and len(review.strip()) > 20:
                # Simple sentence splitting
                review_sentences = review.replace('!', '.').replace('?', '.').split('.')
                sentences.extend([s.strip() for s in review_sentences if len(s.strip()) > 15])
        
        if not sentences:
            return "Unable to extract meaningful sentences from reviews."
        
        # Score sentences by length and common positive/negative words
        positive_words = {'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect', 'love', 'beautiful', 'clean', 'friendly'}
        negative_words = {'terrible', 'awful', 'bad', 'poor', 'disappointing', 'dirty', 'rude', 'worst', 'horrible', 'noisy'}
        
        scored_sentences = []
        for sentence in sentences:
            score = 0
            words = sentence.lower().split()
            
            # Score based on sentiment words
            for word in words:
                if word in positive_words:
                    score += 2
                elif word in negative_words:
                    score += 2  # Both positive and negative are important
            
            # Prefer moderate length sentences
            if 30 <= len(sentence) <= 150:
                score += 1
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [sent for _, sent in scored_sentences[:max_sentences]]
        
        return " ".join(top_sentences) if top_sentences else "Unable to generate a meaningful summary."
    
    def _preprocess_reviews(self, reviews: List[str]) -> str:
        """
        Preprocess and concatenate reviews for summarization
        """
        if not reviews:
            return ""
        
        # Filter out very short reviews and clean up text
        processed_reviews = []
        for review in reviews:
            if review and len(review.strip()) > 10:
                clean_review = review.strip()
                clean_review = " ".join(clean_review.split())
                processed_reviews.append(clean_review)
        
        # Combine reviews with separator
        combined_text = " ".join(processed_reviews)
        
        # Truncate if too long for the model
        max_chars = 800  # Conservative limit for t5-small
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars] + "..."
            logger.info(f"Truncated combined reviews to {len(combined_text)} characters")
        
        return combined_text
    
    def summarize_reviews(self, reviews: List[str], max_length: int = 150, min_length: int = 30) -> Dict[str, Any]:
        """
        Summarize a list of reviews
        
        Args:
            reviews: List of review texts to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            
        Returns:
            Dict containing summary and metadata
        """
        if not reviews:
            return {
                "summary": "No reviews available to summarize.",
                "total_reviews": 0,
                "processed_reviews": 0
            }
        
        # Count non-empty reviews that can be processed
        processed_count = len([r for r in reviews if r and len(r.strip()) > 10])
        
        if processed_count == 0:
            return {
                "summary": "No meaningful reviews available to summarize.",
                "total_reviews": len(reviews),
                "processed_reviews": 0
            }
        
        try:
            if self.summarizer:
                # Use AI model for summarization
                logger.info(f"Using AI model ({self.model_name}) for summarization")
                
                combined_text = self._preprocess_reviews(reviews)
                
                if not combined_text or len(combined_text.strip()) < 50:
                    return {
                        "summary": "Insufficient review content to generate a meaningful summary.",
                        "total_reviews": len(reviews),
                        "processed_reviews": 0
                    }
                
                # Adjust parameters for t5-small
                if self.model_name == "t5-small":
                    max_length = min(max_length, 100)  # t5-small works better with shorter outputs
                    min_length = min(min_length, 20)
                
                summary_result = self.summarizer(
                    combined_text,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    clean_up_tokenization_spaces=True
                )
                
                summary_text = summary_result[0]['summary_text'] if summary_result else "Unable to generate summary."
                
                return {
                    "summary": summary_text,
                    "total_reviews": len(reviews),
                    "processed_reviews": processed_count,
                    "input_length": len(combined_text),
                    "model_used": self.model_name
                }
            else:
                # Use fallback extractive summarization
                logger.info("Using fallback extractive summarization")
                
                summary_text = self._simple_extractive_summary(reviews, max_sentences=3)
                
                return {
                    "summary": summary_text,
                    "total_reviews": len(reviews),
                    "processed_reviews": processed_count,
                    "model_used": "extractive_fallback",
                    "note": "Using simplified summarization due to model unavailability"
                }
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            
            # Try fallback method
            try:
                summary_text = self._simple_extractive_summary(reviews, max_sentences=2)
                return {
                    "summary": summary_text,
                    "total_reviews": len(reviews),
                    "processed_reviews": processed_count,
                    "error": f"AI summarization failed, used fallback method: {str(e)}",
                    "model_used": "extractive_fallback"
                }
            except Exception as fallback_error:
                logger.error(f"Fallback summarization also failed: {fallback_error}")
                return {
                    "summary": f"Error generating summary. Please try again later.",
                    "error": str(e),
                    "total_reviews": len(reviews),
                    "processed_reviews": 0
                }

# Global instance
review_summarizer = ReviewSummarizer()
