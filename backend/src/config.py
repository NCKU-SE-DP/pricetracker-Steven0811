class Sentry():
    DSN = "https://b67a832b0e11dac306b64212c08c8a93@o4508454841090048.ingest.us.sentry.io/4508454886768640"
    TRACE_SAMPLE_RATE = 1.0
    PROFILES_SAMPLE_RATE = 1.0

class Auth():
    JWT_SECRET_KEY = '1892dhianiandowqd0n'
    JWT_ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
    TOKER_URL = "/api/v1/users/login"

class Basic():
    ALLOWED_ORIGIN = "http://localhost:8080"
    API_PREFIX = "/api/v1"
    SCHEDULER_INTERVAL_MINUTES = 100