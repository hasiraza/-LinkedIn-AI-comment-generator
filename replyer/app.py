from flask import Flask, render_template, request, jsonify
from api.performance import PerformanceBenchmark, make_track_performance
import os
from datetime import datetime
from api.chatbot import generate_linkedin_reply
app = Flask(__name__)

# Initialize benchmark
benchmark = PerformanceBenchmark()

# Create track_performance decorator with access to benchmark
track_performance = make_track_performance(benchmark)

# Import and decorate chatbot functions after creating the decorator
from api.chatbot import generate_linkedin_reply
generate_linkedin_reply = track_performance(generate_linkedin_reply)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    stats_24h = benchmark.get_performance_stats(24)
    stats_1h = benchmark.get_performance_stats(1)
    return render_template('dashboard.html', stats_24h=stats_24h, stats_1h=stats_1h)

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

# Performance benchmark targets
PERFORMANCE_TARGETS = {
    'response_time': {
        'excellent': 1.0,    # < 1 second
        'good': 2.0,         # < 2 seconds
        'acceptable': 5.0,   # < 5 seconds
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
        'excellent': 0.1,    # < 0.1%
        'good': 1.0,         # < 1%
        'acceptable': 5.0,   # < 5%
        'poor': float('inf')
    }
}

@app.route('/api/benchmark-targets')
def api_benchmark_targets():
    return jsonify(PERFORMANCE_TARGETS)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Create default templates if they don't exist
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Comment Reply Chatbot</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="nav">
        <a href="/">Home</a>
        <a href="/dashboard">Performance Dashboard</a>
    </div>
    
    <div class="container">
        <h1>LinkedIn Comment Reply Generator</h1>
        
        <div class="input-section">
            <h3>Enter LinkedIn Comment</h3>
            <textarea id="comment" placeholder="Paste the LinkedIn comment here..."></textarea>
            <div class="options">
                <label for="tone">Tone:</label>
                <select id="tone">
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="enthusiastic">Enthusiastic</option>
                    <option value="thoughtful">Thoughtful</option>
                </select>
                <button onclick="generateReply()">Generate Reply</button>
            </div>
        </div>
        
        <div id="result" class="result-section" style="display: none;">
            <h3>Generated Reply</h3>
            <div id="reply" class="reply-box" contenteditable="true"></div>
            <div class="action-buttons">
                <button onclick="copyToClipboard()">Copy Reply</button>
                <button onclick="regenerateReply()">Regenerate</button>
                <div class="rating">
                    <span>Rate this reply:</span>
                    <select id="rating">
                        <option value="10">10 - Excellent</option>
                        <option value="9">9</option>
                        <option value="8" selected>8 - Good</option>
                        <option value="7">7</option>
                        <option value="6">6 - Average</option>
                        <option value="5">5</option>
                        <option value="4">4 - Poor</option>
                    </select>
                    <button onclick="submitFeedback()">Submit Feedback</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentComment = '';
        
        async function generateReply() {
            currentComment = document.getElementById('comment').value;
            if (!currentComment.trim()) {
                alert('Please enter a comment');
                return;
            }
            
            const button = document.querySelector('.input-section button');
            button.disabled = true;
            button.textContent = 'Generating...';
            
            try {
                const tone = document.getElementById('tone').value;
                const response = await fetch('/api/generate-reply', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        comment: currentComment,
                        context: tone
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('reply').innerHTML = data.reply;
                    document.getElementById('result').style.display = 'block';
                } else {
                    alert('Error: ' + (data.error || 'Unknown error occurred'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                button.disabled = false;
                button.textContent = 'Generate Reply';
            }
        }
        
        function copyToClipboard() {
            const reply = document.getElementById('reply');
            navigator.clipboard.writeText(reply.innerText)
                .then(() => alert('Reply copied to clipboard!'))
                .catch(err => alert('Failed to copy: ' + err));
        }
        
        function regenerateReply() {
            if (currentComment) {
                generateReply();
            }
        }
        
        async function submitFeedback() {
            const rating = document.getElementById('rating').value;
            
            try {
                const response = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({satisfaction: parseInt(rating)})
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('Thank you for your feedback!');
                }
            } catch (error) {
                alert('Error submitting feedback: ' + error.message);
            }
        }
    </script>
</body>
</html>''')
    
    if not os.path.exists('templates/dashboard.html'):
        with open('templates/dashboard.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Performance Dashboard</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="nav">
        <a href="/">Home</a>
        <a href="/dashboard">Performance Dashboard</a>
    </div>
    
    <h1>Performance Dashboard</h1>
    <button class="refresh-btn" onclick="location.reload()">Refresh Data</button>
    
    <div class="section">
        <h2>Last 24 Hours</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(stats_24h.avg_response_time) }}s</div>
                <div class="metric-label">Average Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ stats_24h.total_requests }}</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(stats_24h.avg_quality_score) }}/10</div>
                <div class="metric-label">Average Quality Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(stats_24h.error_rate) }}%</div>
                <div class="metric-label">Error Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ stats_24h.total_tokens }}</div>
                <div class="metric-label">Total Tokens Used</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(stats_24h.requests_per_hour) }}</div>
                <div class="metric-label">Requests per Hour</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Last Hour</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(stats_1h.avg_response_time) }}s</div>
                <div class="metric-label">Average Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ stats_1h.total_requests }}</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(stats_1h.p95_response_time) }}s</div>
                <div class="metric-label">95th Percentile Response Time</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Performance Targets</h2>
        <div style="background: #f9f9f9; padding: 20px; border-radius: 8px;">
            <h3>Response Time Targets</h3>
            <ul>
                <li>Excellent: < 1.0 seconds</li>
                <li>Good: < 2.0 seconds</li>
                <li>Acceptable: < 5.0 seconds</li>
            </ul>
            
            <h3>Quality Score Targets</h3>
            <ul>
                <li>Excellent: > 9.0/10</li>
                <li>Good: > 7.0/10</li>
                <li>Acceptable: > 5.0/10</li>
            </ul>
            
            <h3>Error Rate Targets</h3>
            <ul>
                <li>Excellent: < 0.1%</li>
                <li>Good: < 1.0%</li>
                <li>Acceptable: < 5.0%</li>
            </ul>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>''')

    if not os.path.exists('static/style.css'):
        with open('static/style.css', 'w') as f:
            f.write('''body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    line-height: 1.6;
    color: #333;
    background-color: #f9f9f9;
}

.nav {
    margin-bottom: 30px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

.nav a {
    margin-right: 20px;
    text-decoration: none;
    color: #0077b5;
    font-weight: 500;
}

.nav a:hover {
    text-decoration: underline;
}

.container {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h1, h2, h3 {
    color: #0077b5;
}

.input-section {
    margin-bottom: 30px;
}

textarea {
    width: 100%;
    height: 120px;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: inherit;
    font-size: 16px;
    margin: 10px 0;
    resize: vertical;
}

.options {
    display: flex;
    align-items: center;
    gap: 15px;
}

select {
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid #ddd;
}

button {
    background-color: #0077b5;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #006097;
}

button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
}

.result-section {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}

.reply-box {
    background-color: #f0f7fc;
    padding: 20px;
    border-radius: 4px;
    margin: 15px 0;
    border-left: 4px solid #0077b5;
    min-height: 100px;
    white-space: pre-wrap;
}

.action-buttons {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
}

.rating {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 10px;
}

.rating span {
    color: #666;
}

/* Dashboard specific styles */
.section {
    margin: 30px 0;
}

.refresh-btn {
    margin-bottom: 20px;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.metric-card {
    background: #f9f9f9;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #0077b5;
}

.metric-value {
    font-size: 2em;
    font-weight: bold;
    color: #0077b5;
}

.metric-label {
    color: #666;
    font-size: 0.9em;
}

.status-excellent {
    border-left-color: #28a745;
}

.status-good {
    border-left-color: #ffc107;
}

.status-poor {
    border-left-color: #dc3545;
}''')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
