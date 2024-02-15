import os
import redis

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'fallback_secret_key')
    DEBUG = True
    