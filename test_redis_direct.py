import redis
from app.core.config import settings

def test_redis():
    url = str(settings.REDIS_URL)
    print(f"Testing connection to: {url}")
    try:
        # Manually parse the URL to bypass any library specific formatting issues
        r = redis.from_url(url, ssl_cert_reqs=None)
        info = r.ping()
        print(f"Ping successful: {info}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_redis()
