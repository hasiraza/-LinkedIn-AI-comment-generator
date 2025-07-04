import time
import sqlite3
from datetime import datetime, timedelta
import psutil
import statistics
from functools import wraps

class PerformanceBenchmark:
    def __init__(self, db_path="performance_metrics.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for storing metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                response_time FLOAT,
                api_call_time FLOAT,
                tokens_used INTEGER,
                request_size INTEGER,
                response_size INTEGER,
                memory_usage FLOAT,
                cpu_usage FLOAT,
                quality_score FLOAT,
                user_satisfaction INTEGER,
                error_occurred BOOLEAN DEFAULT FALSE,
                error_message TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_performance(self, metrics):
        """Log performance metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO performance_metrics 
            (response_time, api_call_time, tokens_used, request_size, response_size, 
             memory_usage, cpu_usage, quality_score, user_satisfaction, error_occurred, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.get('response_time', 0),
            metrics.get('api_call_time', 0),
            metrics.get('tokens_used', 0),
            metrics.get('request_size', 0),
            metrics.get('response_size', 0),
            metrics.get('memory_usage', 0),
            metrics.get('cpu_usage', 0),
            metrics.get('quality_score', 0),
            metrics.get('user_satisfaction', 0),
            metrics.get('error_occurred', False),
            metrics.get('error_message', '')
        ))
        conn.commit()
        conn.close()
    
    def get_performance_stats(self, hours=24):
        """Get performance statistics for the last N hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since_time = datetime.now() - timedelta(hours=hours)
        cursor.execute('SELECT * FROM performance_metrics WHERE timestamp >= ?', (since_time,))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return self.get_default_stats()
        
        response_times = [r[2] for r in results if r[2] is not None]
        api_times = [r[3] for r in results if r[3] is not None]
        tokens = [r[4] for r in results if r[4] is not None]
        quality_scores = [r[8] for r in results if r[8] is not None and r[8] > 0]
        errors = [r[10] for r in results]
        
        return {
            'total_requests': len(results),
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'avg_api_time': statistics.mean(api_times) if api_times else 0,
            'total_tokens': sum(tokens) if tokens else 0,
            'avg_quality_score': statistics.mean(quality_scores) if quality_scores else 0,
            'error_rate': (sum(errors) / len(results)) * 100 if results else 0,
            'requests_per_hour': len(results) / hours,
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else (max(response_times) if response_times else 0)
        }
    
    def get_default_stats(self):
        return {
            'total_requests': 0,
            'avg_response_time': 0,
            'max_response_time': 0,
            'avg_api_time': 0,
            'total_tokens': 0,
            'avg_quality_score': 0,
            'error_rate': 0,
            'requests_per_hour': 0,
            'p95_response_time': 0
        }

def make_track_performance(benchmark):
    """Factory function to create a track_performance decorator with access to benchmark"""
    def track_performance(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            start_cpu = psutil.cpu_percent()
            
            metrics = {
                'error_occurred': False,
                'error_message': '',
                'request_size': len(str(args) + str(kwargs)),
                'memory_usage': start_memory,
                'cpu_usage': start_cpu
            }
            
            try:
                result = func(*args, **kwargs)
                metrics['response_time'] = time.time() - start_time
                metrics['response_size'] = len(str(result)) if result else 0
                return result
            except Exception as e:
                metrics['error_occurred'] = True
                metrics['error_message'] = str(e)
                raise
            finally:
                benchmark.log_performance(metrics)
        return wrapper
    return track_performance