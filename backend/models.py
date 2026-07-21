from datetime import datetime
import sqlite3

class Database:
    def __init__(self, db_path='avaye_yaghin.db'):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

class User:
    def __init__(self, id=None, phone=None, name=None, created_at=None):
        self.id = id
        self.phone = phone
        self.name = name
        self.created_at = created_at or datetime.now()
    
    def save(self):
        db = Database()
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (id, phone, name, created_at) VALUES (?, ?, ?, ?)",
                  (self.id, self.phone, self.name, self.created_at))
        conn.commit()
        self.id = c.lastrowid
        conn.close()
        return self.id
    
    @classmethod
    def find_by_phone(cls, phone):
        db = Database()
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        user = c.fetchone()
        conn.close()
        if user:
            return cls(id=user['id'], phone=user['phone'], name=user['name'], 
                      created_at=user['created_at'])
        return None

class Chat:
    def __init__(self, id=None, user_id=None, message=None, response=None, timestamp=None):
        self.id = id
        self.user_id = user_id
        self.message = message
        self.response = response
        self.timestamp = timestamp or datetime.now()
    
    def save(self):
        db = Database()
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO chats (user_id, message, response, timestamp) VALUES (?, ?, ?, ?)",
                  (self.user_id, self.message, self.response, self.timestamp))
        conn.commit()
        self.id = c.lastrowid
        conn.close()
        return self.id
