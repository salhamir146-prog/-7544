from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sqlite3
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import re
import hashlib

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = 'avaye-yaghin-super-secret-key-2026'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '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')
ADMIN_PASSWORD = 'Amidhjsos62627@_897'

# ============ دیتابیس ============
def init_db():
    conn = sqlite3.connect('avaye_yaghin.db')
    c = conn.cursor()
    
    # جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP
    )''')
    
    # جدول چت‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        response TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # جدول تنظیمات ربات
    c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        personality TEXT,
        welcome_message TEXT,
        system_prompt TEXT,
        temperature REAL DEFAULT 0.7,
        max_tokens INTEGER DEFAULT 2048,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول بازخورد کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # درج تنظیمات پیش‌فرض
    c.execute('''INSERT OR IGNORE INTO bot_settings (id, name, personality, welcome_message, system_prompt)
                 VALUES (1, 'آوای یقین', 
                 'دستیار دینی مهربان، دانا و صبور که با استناد به آیات قرآن و روایات معصومین پاسخ می‌دهد. بسیار خوش‌برخورد و مشتاق به کمک به دیگران است.',
                 '🌙 سلام! من آوای یقین هستم، دستیار دینی شما. در مسیر ایمان و یقین همراهتان هستم. چه سوالی دارید؟',
                 'شما یک دستیار دینی متخصص هستید که بر اساس قرآن و سنت پاسخ می‌دهید. پاسخ‌ها باید دقیق، مستدل و با مهربانی بیان شوند. از آیات و روایات معتبر استفاده کنید.')''')
    
    conn.commit()
    conn.close()

init_db()

# ============ توابع کمکی ============
def get_db():
    conn = sqlite3.connect('avaye_yaghin.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_ai_response(message, personality, system_prompt, chat_history=[], temperature=0.7):
    """ارسال درخواست به Groq API"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"شخصیت شما: {personality}"}
    ]
    
    # اضافه کردن تاریخچه چت (حداکثر ۱۰ پیام آخر)
    for h in chat_history[-10:]:
        messages.append({"role": "user", "content": h['message']})
        messages.append({"role": "assistant", "content": h['response']})
    
    messages.append({"role": "user", "content": message})
    
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
        "top_p": 0.95
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return "⏰ متأسفم، زمان پاسخگویی به پایان رسید. لطفاً دوباره تلاش کنید."
    except requests.exceptions.RequestException as e:
        return f"❌ خطا در ارتباط با سرور: {str(e)}"
    except Exception as e:
        return f"⚠️ خطای ناشناخته: {str(e)}"

def save_chat(user_id, message, response):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO chats (user_id, message, response) VALUES (?, ?, ?)",
              (user_id, message, response))
    conn.commit()
    chat_id = c.lastrowid
    conn.close()
    return chat_id

def get_user_chat_history(user_id, limit=20):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT message, response, timestamp FROM chats WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", 
              (user_id, limit))
    history = c.fetchall()
    conn.close()
    return [{'message': h[0], 'response': h[1], 'timestamp': h[2]} for h in reversed(history)]

def create_or_get_user(phone, name):
    conn = get_db()
    c = conn.cursor()
    
    # بررسی وجود کاربر
    c.execute("SELECT id FROM users WHERE phone = ?", (phone,))
    user = c.fetchone()
    
    if user:
        user_id = user[0]
        # به‌روزرسانی زمان آخرین فعالیت
        c.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP, name = ? WHERE id = ?", (name, user_id))
    else:
        c.execute("INSERT INTO users (phone, name, last_active) VALUES (?, ?, CURRENT_TIMESTAMP)", (phone, name))
        user_id = c.lastrowid
    
    conn.commit()
    conn.close()
    return user_id

def get_bot_settings():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, personality, welcome_message, system_prompt, temperature, max_tokens FROM bot_settings WHERE id = 1")
    settings = c.fetchone()
    conn.close()
    return {
        'name': settings[0],
        'personality': settings[1],
        'welcome_message': settings[2],
        'system_prompt': settings[3],
        'temperature': settings[4],
        'max_tokens': settings[5]
    }

# ============ مسیرهای API ============

# مسیر اصلی - صفحه ورود
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('../frontend', 'admin.html')

# سرویس فایل‌های استاتیک
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('../frontend/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('../frontend/js', filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('../frontend/assets', filename)

# ============ API ورود ============
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone', '').strip()
    name = data.get('name', '').strip()
    
    if not phone or not name:
        return jsonify({'error': 'لطفاً نام و شماره تلفن را وارد کنید'}), 400
    
    # بررسی ورود ادمین
    if phone == ADMIN_PASSWORD:
        return jsonify({'status': 'admin', 'redirect': '/admin'})
    
    # ایجاد کاربر جدید یا بازگشت کاربر موجود
    user_id = create_or_get_user(phone, name)
    
    return jsonify({
        'status': 'success',
        'user_id': user_id,
        'phone': phone,
        'name': name
    })

# ============ API چت ============
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message', '').strip()
    phone = data.get('phone')
    
    if not message:
        return jsonify({'error': 'پیام نمی‌تواند خالی باشد'}), 400
    
    # اگر user_id ارسال نشده، از شماره تلفن پیدا کن
    if not user_id and phone:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        user = c.fetchone()
        conn.close()
        if user:
            user_id = user[0]
        else:
            return jsonify({'error': 'کاربر یافت نشد'}), 404
    
    if not user_id:
        return jsonify({'error': 'شناسه کاربر معتبر نیست'}), 400
    
    # دریافت تنظیمات ربات
    settings = get_bot_settings()
    
    # دریافت تاریخچه چت
    chat_history = get_user_chat_history(user_id, 20)
    
    # دریافت پاسخ از AI
    response = get_ai_response(
        message=message,
        personality=settings['personality'],
        system_prompt=settings['system_prompt'],
        chat_history=chat_history,
        temperature=settings['temperature']
    )
    
    # ذخیره چت
    chat_id = save_chat(user_id, message, response)
    
    return jsonify({
        'response': response,
        'chat_id': chat_id
    })

# ============ API تنظیمات ادمین ============
@app.route('/api/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if request.method == 'GET':
        settings = get_bot_settings()
        return jsonify(settings)
    
    # POST - به‌روزرسانی تنظیمات
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''UPDATE bot_settings 
                 SET name = ?, personality = ?, welcome_message = ?, 
                     system_prompt = ?, temperature = ?, max_tokens = ?,
                     updated_at = CURRENT_TIMESTAMP
                 WHERE id = 1''',
              (data.get('name'), data.get('personality'), data.get('welcome_message'),
               data.get('system_prompt'), float(data.get('temperature', 0.7)), 
               int(data.get('max_tokens', 2048))))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'تنظیمات با موفقیت ذخیره شد'})

# ============ API دریافت چت‌ها ============
@app.route('/api/admin/chats', methods=['GET'])
def get_chats():
    limit = request.args.get('limit', 100, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    c = conn.cursor()
    
    query = '''SELECT u.name, u.phone, c.message, c.response, c.timestamp 
               FROM chats c 
               JOIN users u ON c.user_id = u.id'''
    
    params = []
    if search:
        query += " WHERE u.name LIKE ? OR u.phone LIKE ? OR c.message LIKE ?"
        search_pattern = f"%{search}%"
        params = [search_pattern, search_pattern, search_pattern]
    
    query += " ORDER BY c.timestamp DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    chats = c.fetchall()
    conn.close()
    
    return jsonify([{
        'name': c[0],
        'phone': c[1],
        'message': c[2],
        'response': c[3],
        'timestamp': c[4]
    } for c in chats])

# ============ API آمار ============
@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    c = conn.cursor()
    
    # تعداد کل کاربران
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    # تعداد کل پیام‌ها
    c.execute("SELECT COUNT(*) FROM chats")
    total_messages = c.fetchone()[0]
    
    # چت‌های امروز
    c.execute("SELECT COUNT(*) FROM chats WHERE DATE(timestamp) = DATE('now')")
    today_chats = c.fetchone()[0]
    
    # کاربران آنلاین (فعال در ۵ دقیقه اخیر)
    five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
    c.execute("SELECT COUNT(*) FROM users WHERE last_active > ?", (five_min_ago,))
    online_users = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_users': total_users,
        'total_messages': total_messages,
        'today_chats': today_chats,
        'online_users': online_users
    })

# ============ API خروجی داده ============
@app.route('/api/admin/export', methods=['GET'])
def export_chats():
    format_type = request.args.get('format', 'json')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT u.name, u.phone, c.message, c.response, c.timestamp 
                 FROM chats c JOIN users u ON c.user_id = u.id
                 ORDER BY c.timestamp DESC''')
    chats = c.fetchall()
    conn.close()
    
    data = [{
        'نام': c[0],
        'شماره': c[1],
        'پیام': c[2],
        'پاسخ': c[3],
        'زمان': c[4]
    } for c in chats]
    
    if format_type == 'csv':
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['نام', 'شماره', 'پیام', 'پاسخ', 'زمان'])
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue(), 200, {'Content-Type': 'text/csv'}
    
    return jsonify(data)

# ============ API بازخورد ============
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    user_id = data.get('user_id')
    chat_id = data.get('chat_id')
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id, chat_id, rating, comment) VALUES (?, ?, ?, ?)",
              (user_id, chat_id, rating, comment))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

# ============ اجرا ============
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
