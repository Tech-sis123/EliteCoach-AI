import redis
import ssl
from app.core.config import settings

def test_redis_sync():
    print(f"Testing connection to: {settings.REDIS_URL}")
    try:
        # Parse URL manually for a sync test
        from urllib.parse import urlparse
        url = urlparse(settings.REDIS_URL)
        
        r = redis.Redis(
            host=url.hostname,
            port=url.port,
            password=url.password,
            username=url.username,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            socket_timeout=5
        )
        print("Pinging Redis...")
        response = r.ping()
        print(f"Ping successful: {response}")
    except Exception as e:
        print(f"Redis connection failed: {e}")

if __name__ == "__main__":
    test_redis_sync()
