#!/usr/bin/env python3
"""
ML Model Evaluation Script for Hotel Review Sentiment Analysis
Evaluates model performance and uploads metrics to CloudWatch
"""

import json
import os
import sys
import boto3
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Tuple
import psycopg2
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Evaluates sentiment analysis model performance"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.cloudwatch = boto3.client('cloudwatch')
        self.secrets_client = boto3.client('secretsmanager')
        self.bucket_name = os.environ.get('ML_ARTIFACTS_BUCKET', 'hotel-review-nlp-ml-artifacts')
        
        # Initialize model
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.classifier = pipeline("sentiment-analysis", 
                                 model=self.model, 
                                 tokenizer=self.tokenizer,
                                 return_all_scores=True)
    
    def get_database_connection(self):
        """Get database connection from AWS Secrets Manager"""
        try:
            secret_arn = os.environ.get('DB_SECRET_ARN')
            if not secret_arn:
                logger.error("DB_SECRET_ARN environment variable not set")
                return None
                
            response = self.secrets_client.get_secret_value(SecretId=secret_arn)
            secret = json.loads(response['SecretString'])
            
            conn = psycopg2.connect(
                host=secret['host'],
                port=secret['port'],
                database=secret['dbname'],
                user=secret['username'],
                password=secret['password']
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None
    
    def fetch_evaluation_data(self, conn) -> pd.DataFrame:
        """Fetch recent reviews for evaluation"""
        try:
            query = """
            SELECT 
                review_text,
                sentiment_label,
                sentiment_score,
                created_at
            FROM reviews 
            WHERE created_at >= NOW() - INTERVAL '30 days'
            AND review_text IS NOT NULL
            AND sentiment_label IS NOT NULL
            LIMIT 1000;
            """
            
            df = pd.read_sql_query(query, conn)
            logger.info(f"Fetched {len(df)} reviews for evaluation")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch evaluation data: {e}")
            return pd.DataFrame()
    
    def predict_sentiment(self, text: str) -> Tuple[str, float]:
        """Predict sentiment for a given text"""
        try:
            result = self.classifier(text)
            
            # Convert to our label format
            scores = {item['label']: item['score'] for item in result}
            
            if scores.get('POSITIVE', 0) > scores.get('NEGATIVE', 0):
                label = 'POSITIVE'
                score = scores['POSITIVE']
            else:
                label = 'NEGATIVE' 
                score = scores['NEGATIVE']
            
            return label, score
            
        except Exception as e:
            logger.error(f"Prediction failed for text: {e}")
            return 'NEUTRAL', 0.5
    
    def evaluate_model(self, df: pd.DataFrame) -> Dict:
        """Evaluate model performance on the dataset"""
        if df.empty:
            logger.warning("No data available for evaluation")
            return {}
        
        logger.info("Starting model evaluation...")
        
        # Make predictions
        predictions = []
        prediction_scores = []
        
        for text in df['review_text']:
            label, score = self.predict_sentiment(text)
            predictions.append(label)
            prediction_scores.append(score)
        
        # Convert labels to consistent format
        true_labels = df['sentiment_label'].str.upper()
        pred_labels = pd.Series(predictions)
        
        # Filter out NEUTRAL predictions for binary classification metrics
        binary_mask = (true_labels.isin(['POSITIVE', 'NEGATIVE'])) & (pred_labels.isin(['POSITIVE', 'NEGATIVE']))
        true_binary = true_labels[binary_mask]
        pred_binary = pred_labels[binary_mask]
        
        # Calculate metrics
        metrics = {}
        
        if len(true_binary) > 0:
            metrics['accuracy'] = accuracy_score(true_binary, pred_binary)
            metrics['precision'] = precision_score(true_binary, pred_binary, pos_label='POSITIVE')
            metrics['recall'] = recall_score(true_binary, pred_binary, pos_label='POSITIVE')
            metrics['f1_score'] = f1_score(true_binary, pred_binary, pos_label='POSITIVE')
            
            # Confusion matrix
            cm = confusion_matrix(true_binary, pred_binary, labels=['NEGATIVE', 'POSITIVE'])
            metrics['confusion_matrix'] = cm.tolist()
            
            # Additional metrics
            metrics['total_samples'] = len(df)
            metrics['binary_samples'] = len(true_binary)
            metrics['positive_predictions'] = sum(pred_binary == 'POSITIVE')
            metrics['negative_predictions'] = sum(pred_binary == 'NEGATIVE')
            metrics['avg_confidence'] = np.mean(prediction_scores)
            
        logger.info(f"Evaluation completed. Accuracy: {metrics.get('accuracy', 0):.3f}")
        return metrics
    
    def upload_metrics_to_cloudwatch(self, metrics: Dict):
        """Upload evaluation metrics to CloudWatch"""
        try:
            metric_data = [
                {
                    'MetricName': 'ModelAccuracy',
                    'Value': metrics.get('accuracy', 0) * 100,
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'ModelPrecision', 
                    'Value': metrics.get('precision', 0) * 100,
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'ModelRecall',
                    'Value': metrics.get('recall', 0) * 100, 
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'ModelF1Score',
                    'Value': metrics.get('f1_score', 0) * 100,
                    'Unit': 'Percent', 
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'EvaluationSamples',
                    'Value': metrics.get('total_samples', 0),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'AvgConfidence',
                    'Value': metrics.get('avg_confidence', 0) * 100,
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='HotelReview/ML',
                MetricData=metric_data
            )
            
            logger.info("Metrics uploaded to CloudWatch successfully")
            
        except Exception as e:
            logger.error(f"Failed to upload metrics to CloudWatch: {e}")
    
    def save_evaluation_results(self, metrics: Dict):
        """Save evaluation results to S3"""
        try:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
            
            evaluation_data = {
                'timestamp': timestamp,
                'model_name': self.model_name,
                'metrics': metrics,
                'environment': os.environ.get('ENVIRONMENT', 'unknown')
            }
            
            # Save locally first
            with open('evaluation_results.json', 'w') as f:
                json.dump(evaluation_data, f, indent=2, default=str)
            
            # Upload to S3
            s3_key = f"evaluations/{datetime.utcnow().strftime('%Y/%m/%d')}/evaluation_{timestamp}.json"
            
            self.s3_client.upload_file(
                'evaluation_results.json',
                self.bucket_name,
                s3_key
            )
            
            logger.info(f"Evaluation results saved to S3: s3://{self.bucket_name}/{s3_key}")
            
        except Exception as e:
            logger.error(f"Failed to save evaluation results: {e}")
    
    def run_evaluation(self):
        """Run complete model evaluation pipeline"""
        logger.info("Starting model evaluation pipeline...")
        
        # Get database connection
        conn = self.get_database_connection()
        if not conn:
            logger.error("Failed to establish database connection")
            return False
        
        try:
            # Fetch evaluation data
            df = self.fetch_evaluation_data(conn)
            
            if df.empty:
                logger.warning("No evaluation data available")
                return False
            
            # Evaluate model
            metrics = self.evaluate_model(df)
            
            if not metrics:
                logger.error("Model evaluation failed")
                return False
            
            # Upload metrics and save results
            self.upload_metrics_to_cloudwatch(metrics)
            self.save_evaluation_results(metrics)
            
            logger.info("Model evaluation pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Evaluation pipeline failed: {e}")
            return False
            
        finally:
            conn.close()

def main():
    """Main execution function"""
    evaluator = ModelEvaluator()
    success = evaluator.run_evaluation()
    
    if not success:
        sys.exit(1)
    
    print("Model evaluation completed successfully!")

if __name__ == "__main__":
    main()
