import redis
import os
from dotenv import load_dotenv

load_dotenv()

def get_redis_client():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )

def save_user_memory(user_id, memory):
  redis = get_redis_client()
  redis.set(user_id, memory, ex=7*86400)

def get_user_memory(user_id):
  redis = get_redis_client()
  return redis.get(user_id)