from flask import Flask, render_template, request, jsonify
from chatbot.performance import PerformanceBenchmark, make_track_performance
import os
from datetime import datetime
from chatbot.chatbot import generate_linkedin_reply

app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize benchmark
benchmark = PerformanceBenchmark()

# Create track_performance decorator with access to benchmark
track_performance = make_track_performance(benchmark)

# Decorate chatbot function
generate_linkedin_reply = track_performance(generate_linkedin_reply)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    stats_24h = benchmark.get_performance_stats(24)
    stats_1h = benchmark.get_performance_stats(1)
    return render_template('dashboard.html', stats_24h=stats_24h, stats_1h=stats_1h)

@app.route('/simple')
def simple():
    return render_template('simple.html')

@app.route('/api/generate-reply', methods=['POST'])
def api_generate_reply():
    try:
        data = request.json
        comment = data.get('comment', '')
        context = data.get('context', 'professional')
        
        if not comment:
            return jsonify({'error': 'Comment is required'}), 400
        
        reply = generate_linkedin_reply(comment, context)
        return jsonify({
            'success': True,
            'reply': reply,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    hours = request.args.get('hours', 24, type=int)
    stats = benchmark.get_performance_stats(hours)
    return jsonify(stats)

@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    try:
        data = request.json
        satisfaction = data.get('satisfaction', 0)
        
        metrics = {
            'user_satisfaction': satisfaction,
            'quality_score': satisfaction,
            'response_time': 0,
            'api_call_time': 0,
            'tokens_used': 0
        }
        benchmark.log_performance(metrics)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

PERFORMANCE_TARGETS = {
    'response_time': {
        'excellent': 1.0,
        'good': 2.0,
        'acceptable': 5.0,
        'poor': float('inf')
    },
    'api_call_time': {
        'excellent': 0.5,
        'good': 1.0,
        'acceptable': 2.0,
        'poor': float('inf')
    },
    'quality_score': {
        'excellent': 9.0,
        'good': 7.0,
        'acceptable': 5.0,
        'poor': 0
    },
    'error_rate': {
        'excellent': 0.1,
        'good': 1.0,
        'acceptable': 5.0,
        'poor': float('inf')
    }
}

@app.route('/api/benchmark-targets')
def api_benchmark_targets():
    return jsonify(PERFORMANCE_TARGETS)

# For local testing
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
