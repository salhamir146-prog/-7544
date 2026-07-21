import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'avaye-yaghin-secret-key'
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY') or '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'
    
    # تنظیمات دیتابیس
    DATABASE = 'avaye_yaghin.db'
    
    # تنظیمات AI
    AI_MODEL = 'mixtral-8x7b-32768'
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 2048
    
    # تنظیمات جلسه
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
