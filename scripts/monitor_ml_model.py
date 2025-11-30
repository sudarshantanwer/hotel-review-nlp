"""
Advanced ML Model Monitoring and Drift Detection
Monitors model performance, data drift, and model degradation
"""

import json
import boto3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLModelMonitor:
    """Advanced ML model monitoring system"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.s3_client = boto3.client('s3')
        self.sns_client = boto3.client('sns')
        
        # Configuration
        self.bucket_name = "hotel-review-nlp-ml-artifacts"
        self.sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:hotel-review-nlp-alerts"
        
        # Thresholds for alerts
        self.accuracy_threshold = 0.8
        self.drift_threshold = 0.1
        self.performance_degradation_threshold = 0.05
    
    def detect_data_drift(self, baseline_data: pd.DataFrame, current_data: pd.DataFrame) -> Dict:
        """Detect data drift using statistical tests"""
        drift_results = {}
        
        # Kolmogorov-Smirnov test for numerical features
        if 'sentiment_score' in baseline_data.columns and 'sentiment_score' in current_data.columns:
            ks_stat, p_value = stats.ks_2samp(
                baseline_data['sentiment_score'].dropna(),
                current_data['sentiment_score'].dropna()
            )
            
            drift_results['sentiment_score_drift'] = {
                'ks_statistic': ks_stat,
                'p_value': p_value,
                'drift_detected': p_value < 0.05
            }
        
        # Chi-square test for categorical features (sentiment labels)
        if 'sentiment_label' in baseline_data.columns and 'sentiment_label' in current_data.columns:
            baseline_counts = baseline_data['sentiment_label'].value_counts()
            current_counts = current_data['sentiment_label'].value_counts()
            
            # Align the indices
            all_labels = set(baseline_counts.index) | set(current_counts.index)
            baseline_aligned = [baseline_counts.get(label, 0) for label in all_labels]
            current_aligned = [current_counts.get(label, 0) for label in all_labels]
            
            if sum(baseline_aligned) > 0 and sum(current_aligned) > 0:
                chi2_stat, p_value = stats.chisquare(current_aligned, baseline_aligned)
                
                drift_results['sentiment_label_drift'] = {
                    'chi2_statistic': chi2_stat,
                    'p_value': p_value,
                    'drift_detected': p_value < 0.05
                }
        
        return drift_results
    
    def calculate_model_performance_metrics(self, true_labels: List[str], 
                                          predicted_labels: List[str], 
                                          confidence_scores: List[float]) -> Dict:
        """Calculate comprehensive model performance metrics"""
        
        # Basic classification metrics
        metrics = {
            'accuracy': accuracy_score(true_labels, predicted_labels),
            'precision': precision_score(true_labels, predicted_labels, average='weighted', zero_division=0),
            'recall': recall_score(true_labels, predicted_labels, average='weighted', zero_division=0),
            'f1_score': f1_score(true_labels, predicted_labels, average='weighted', zero_division=0)
        }
        
        # Confidence-related metrics
        metrics['avg_confidence'] = np.mean(confidence_scores)
        metrics['min_confidence'] = np.min(confidence_scores)
        metrics['max_confidence'] = np.max(confidence_scores)
        metrics['confidence_std'] = np.std(confidence_scores)
        
        # Calculate calibration metrics
        metrics['confidence_accuracy_correlation'] = self._calculate_confidence_accuracy_correlation(
            true_labels, predicted_labels, confidence_scores
        )
        
        return metrics
    
    def _calculate_confidence_accuracy_correlation(self, true_labels: List[str], 
                                                 predicted_labels: List[str], 
                                                 confidence_scores: List[float]) -> float:
        """Calculate correlation between confidence and accuracy"""
        correct_predictions = [1 if true == pred else 0 for true, pred in zip(true_labels, predicted_labels)]
        
        if len(set(correct_predictions)) <= 1 or len(set(confidence_scores)) <= 1:
            return 0.0
        
        correlation, _ = stats.pearsonr(confidence_scores, correct_predictions)
        return correlation if not np.isnan(correlation) else 0.0
    
    def detect_performance_degradation(self, baseline_metrics: Dict, current_metrics: Dict) -> Dict:
        """Detect if model performance has degraded significantly"""
        degradation_results = {}
        
        key_metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        
        for metric in key_metrics:
            if metric in baseline_metrics and metric in current_metrics:
                baseline_value = baseline_metrics[metric]
                current_value = current_metrics[metric]
                
                # Calculate relative change
                if baseline_value > 0:
                    relative_change = (current_value - baseline_value) / baseline_value
                    degradation_detected = relative_change < -self.performance_degradation_threshold
                else:
                    relative_change = 0
                    degradation_detected = False
                
                degradation_results[metric] = {
                    'baseline_value': baseline_value,
                    'current_value': current_value,
                    'relative_change': relative_change,
                    'degradation_detected': degradation_detected
                }
        
        return degradation_results
    
    def send_alert(self, alert_type: str, message: str, details: Dict):
        """Send alert via SNS"""
        try:
            subject = f"Hotel Review NLP - {alert_type} Alert"
            
            alert_message = {
                'timestamp': datetime.utcnow().isoformat(),
                'alert_type': alert_type,
                'message': message,
                'details': details
            }
            
            self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Subject=subject,
                Message=json.dumps(alert_message, indent=2, default=str)
            )
            
            logger.info(f"Alert sent: {alert_type}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def publish_metrics_to_cloudwatch(self, metrics: Dict, namespace: str = 'HotelReview/ML/Monitoring'):
        """Publish monitoring metrics to CloudWatch"""
        try:
            metric_data = []
            
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    metric_data.append({
                        'MetricName': metric_name,
                        'Value': float(value),
                        'Unit': 'Percent' if 'accuracy' in metric_name.lower() or 'precision' in metric_name.lower() or 'recall' in metric_name.lower() else 'None',
                        'Timestamp': datetime.utcnow()
                    })
            
            if metric_data:
                # CloudWatch accepts max 20 metrics per request
                for i in range(0, len(metric_data), 20):
                    batch = metric_data[i:i+20]
                    self.cloudwatch.put_metric_data(
                        Namespace=namespace,
                        MetricData=batch
                    )
                
                logger.info(f"Published {len(metric_data)} metrics to CloudWatch")
                
        except Exception as e:
            logger.error(f"Failed to publish metrics to CloudWatch: {e}")
    
    def save_monitoring_report(self, report_data: Dict, report_type: str = "monitoring"):
        """Save monitoring report to S3"""
        try:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
            s3_key = f"monitoring/{report_type}/{datetime.utcnow().strftime('%Y/%m/%d')}/{report_type}_{timestamp}.json"
            
            # Save locally first
            filename = f"{report_type}_report.json"
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # Upload to S3
            self.s3_client.upload_file(filename, self.bucket_name, s3_key)
            
            logger.info(f"Monitoring report saved to S3: s3://{self.bucket_name}/{s3_key}")
            
        except Exception as e:
            logger.error(f"Failed to save monitoring report: {e}")
    
    def run_comprehensive_monitoring(self, current_data: pd.DataFrame, 
                                   baseline_data: Optional[pd.DataFrame] = None,
                                   baseline_metrics: Optional[Dict] = None) -> Dict:
        """Run comprehensive monitoring including drift detection and performance monitoring"""
        
        monitoring_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'data_summary': {
                'total_samples': len(current_data),
                'date_range': {
                    'start': current_data['created_at'].min() if 'created_at' in current_data.columns else None,
                    'end': current_data['created_at'].max() if 'created_at' in current_data.columns else None
                }
            }
        }
        
        # Data drift detection
        if baseline_data is not None and not baseline_data.empty:
            logger.info("Running data drift detection...")
            drift_results = self.detect_data_drift(baseline_data, current_data)
            monitoring_report['data_drift'] = drift_results
            
            # Check for significant drift
            drift_detected = any(
                result.get('drift_detected', False) 
                for result in drift_results.values() 
                if isinstance(result, dict)
            )
            
            if drift_detected:
                self.send_alert(
                    "Data Drift",
                    "Significant data drift detected in model inputs",
                    drift_results
                )
        
        # Performance monitoring (if we have predictions to evaluate)
        if all(col in current_data.columns for col in ['sentiment_label', 'predicted_label', 'confidence_score']):
            logger.info("Running performance monitoring...")
            
            current_metrics = self.calculate_model_performance_metrics(
                current_data['sentiment_label'].tolist(),
                current_data['predicted_label'].tolist(),
                current_data['confidence_score'].tolist()
            )
            
            monitoring_report['current_metrics'] = current_metrics
            
            # Performance degradation check
            if baseline_metrics:
                degradation_results = self.detect_performance_degradation(baseline_metrics, current_metrics)
                monitoring_report['performance_degradation'] = degradation_results
                
                # Check for significant degradation
                degradation_detected = any(
                    result.get('degradation_detected', False) 
                    for result in degradation_results.values() 
                    if isinstance(result, dict)
                )
                
                if degradation_detected:
                    self.send_alert(
                        "Performance Degradation",
                        "Model performance has degraded significantly",
                        degradation_results
                    )
            
            # Low accuracy alert
            if current_metrics.get('accuracy', 0) < self.accuracy_threshold:
                self.send_alert(
                    "Low Accuracy",
                    f"Model accuracy ({current_metrics['accuracy']:.3f}) is below threshold ({self.accuracy_threshold})",
                    current_metrics
                )
            
            # Publish metrics to CloudWatch
            self.publish_metrics_to_cloudwatch(current_metrics)
        
        # Save comprehensive report
        self.save_monitoring_report(monitoring_report)
        
        return monitoring_report

def main():
    """Main function for running ML monitoring"""
    monitor = MLModelMonitor()
    
    # Example usage - in production, this would fetch real data
    logger.info("Starting ML monitoring pipeline...")
    
    # Create sample data for demonstration
    current_data = pd.DataFrame({
        'sentiment_label': ['POSITIVE', 'NEGATIVE', 'POSITIVE', 'NEGATIVE', 'POSITIVE'],
        'predicted_label': ['POSITIVE', 'NEGATIVE', 'POSITIVE', 'POSITIVE', 'POSITIVE'],
        'confidence_score': [0.9, 0.8, 0.95, 0.6, 0.85],
        'sentiment_score': [0.9, 0.2, 0.95, 0.4, 0.85],
        'created_at': pd.date_range(start='2024-01-01', periods=5, freq='D')
    })
    
    baseline_data = pd.DataFrame({
        'sentiment_score': [0.8, 0.3, 0.9, 0.2, 0.7],
        'sentiment_label': ['POSITIVE', 'NEGATIVE', 'POSITIVE', 'NEGATIVE', 'POSITIVE']
    })
    
    baseline_metrics = {
        'accuracy': 0.9,
        'precision': 0.85,
        'recall': 0.88,
        'f1_score': 0.86
    }
    
    # Run monitoring
    report = monitor.run_comprehensive_monitoring(
        current_data=current_data,
        baseline_data=baseline_data,
        baseline_metrics=baseline_metrics
    )
    
    print("Monitoring completed successfully!")
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()
