from dotenv import load_dotenv
import os

load_dotenv()

class Sentry():
    DSN = os.getenv("SENTRY_DSN")
    TRACE_SAMPLE_RATE = 1.0
    PROFILES_SAMPLE_RATE = 1.0

class Auth():
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
    TOKER_URL = "/api/v1/users/login"
    
class Basic():
    ALLOWED_ORIGIN = "http://localhost:8080"
    API_PREFIX = "/api/v1"
    SCHEDULER_INTERVAL_MINUTES = 100