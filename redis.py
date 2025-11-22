import redis
from azure.identity import DefaultAzureCredential
import requests

# Step 1: Get Access Token for Azure Cache for Redis
credential = DefaultAzureCredential()
token = credential.get_token("https://*.cacheinfra.windows.net/.default")

# Step 2: Connect to Redis
redis_host = "your-redis-name.redis.cache.windows.net"
redis_port = 6380

client = redis.Redis(
    host=redis_host,
    port=redis_port,
    ssl=True,
    password=token.token  # Pass Azure AD token instead of key
)

# Step 3: Test Redis commands
client.set("test-key", "hello")
print(client.get("test-key"))
