from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import sqlite3
import qrcode
from io import BytesIO
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Database setup
DATABASE = 'feedback.db'

# Admin password (change this in production or use environment variable)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

def init_db():
    """Initialize the database with feedback and settings tables"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER NOT NULL,
            comment TEXT,
            name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    # Initialize admin password if not exists
    c.execute('SELECT value FROM settings WHERE key = ?', ('admin_password',))
    if not c.fetchone():
        c.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('admin_password', ADMIN_PASSWORD))
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_admin_password():
    """Get admin password from database"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', ('admin_password',))
    result = c.fetchone()
    conn.close()
    return result['value'] if result else ADMIN_PASSWORD

def set_admin_password(new_password):
    """Update admin password in database"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO settings (key, value) 
        VALUES (?, ?)
    ''', ('admin_password', new_password))
    conn.commit()
    conn.close()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Redirect to feedback form"""
    return render_template('feedback.html')

@app.route('/feedback')
def feedback():
    """Feedback form page"""
    return render_template('feedback.html')

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """API endpoint to submit feedback"""
    try:
        data = request.json
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '')
        name = data.get('name', '')
        email = data.get('email', '')
        
        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO feedback (rating, comment, name, email)
            VALUES (?, ?, ?, ?)
        ''', (rating, comment, name, email))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Feedback submitted successfully', 'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/feedback', methods=['GET'])
@login_required
def get_feedback():
    """API endpoint to get all feedback (admin only)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM feedback ORDER BY created_at DESC')
        feedback_list = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(feedback_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = get_admin_password()
        if password == admin_password:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout admin"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/api/stats')
@login_required
def get_stats():
    """API endpoint to get feedback statistics"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Total count
        c.execute('SELECT COUNT(*) as total FROM feedback')
        total = c.fetchone()['total']
        
        # Positive (4-5 stars)
        c.execute('SELECT COUNT(*) as count FROM feedback WHERE rating >= 4')
        positive = c.fetchone()['count']
        
        # Medium (3 stars)
        c.execute('SELECT COUNT(*) as count FROM feedback WHERE rating = 3')
        medium = c.fetchone()['count']
        
        # Negative (1-2 stars)
        c.execute('SELECT COUNT(*) as count FROM feedback WHERE rating <= 2')
        negative = c.fetchone()['count']
        
        # Average rating
        c.execute('SELECT AVG(rating) as avg FROM feedback')
        avg_rating = c.fetchone()['avg']
        avg_rating = round(avg_rating, 2) if avg_rating else 0
        
        # Rating distribution
        c.execute('''
            SELECT rating, COUNT(*) as count 
            FROM feedback 
            GROUP BY rating 
            ORDER BY rating DESC
        ''')
        distribution = {row['rating']: row['count'] for row in c.fetchall()}
        
        conn.close()
        
        return jsonify({
            'total': total,
            'positive': positive,
            'medium': medium,
            'negative': negative,
            'average': avg_rating,
            'distribution': distribution
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page (admin only)"""
    return render_template('dashboard.html')

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """API endpoint to change admin password"""
    try:
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': 'All fields are required', 'success': False}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match', 'success': False}), 400
        
        if len(new_password) < 4:
            return jsonify({'error': 'Password must be at least 4 characters long', 'success': False}), 400
        
        # Verify current password
        admin_password = get_admin_password()
        if current_password != admin_password:
            return jsonify({'error': 'Current password is incorrect', 'success': False}), 400
        
        # Update password
        set_admin_password(new_password)
        
        return jsonify({'message': 'Password changed successfully', 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/qr')
def qr_code():
    """Generate QR code for feedback link"""
    # Get the base URL (you may need to adjust this for production)
    base_url = request.host_url.rstrip('/')
    feedback_url = f"{base_url}/feedback"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(feedback_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to bytes
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("Feedback Application Started!")
    print("="*50)
    print(f"Feedback Form: http://localhost:5000/feedback")
    print(f"Admin Login: http://localhost:5000/login")
    print(f"Default Admin Password: {ADMIN_PASSWORD}")
    print("="*50 + "\n")
    app.run(debug=False, host='0.0.0.0', port=5000)

