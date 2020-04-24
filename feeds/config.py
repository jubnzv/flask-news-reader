import os
import secrets

# Recreate database on start
FORCE_INIT_NEW = os.getenv('FORCE_INIT_NEW', False)

# Posgres authentication
PG_URI = os.getenv('PG_URI', 'postgres')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASS = os.getenv('PG_PASS', 'changeme')
PG_PORT = os.getenv('PG_PORT', 5432)

# Redis LRU cache configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URI = f'redis://:{REDIS_HOST}:{REDIS_PORT}/0'

# Scrapper configuration
DEFAULT_REQUEST_TIMEOUT = 10
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 "
                  "Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
}
MAX_PARSABLE_CONTENT_LENGTH = 15 * 1024 * 1024  # 15Mb
HN_SCORE_THRESHOLD = 150

# Flask webapp configuration
DEBUG = os.getenv('DEBUG', 0) == '1'
SECRET_KEY = secrets.token_urlsafe(16)
