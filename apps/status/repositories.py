from redis import Redis
from typing import List, Dict, Any
import os
from dotenv import load_dotenv


def update_operation_status(user_id: int, status: str, role_id: int) -> Dict:
    """
    Update the LLM operation status in Redis for an user.
    Args:
        user_id (int): The ID of the user.
        status (str): The status to be updated.
    Returns:
        Dict: A dictionary containing the status of the operation.
    """
    load_dotenv()
    redis = Redis(host=os.getenv("redis_host"), port=os.getenv("redis_port"), db=os.getenv("redis_status_db"))
    redis.set(f"operation_status_{role_id}_{user_id}", status)
    redis.close()
    return {"status": status, "user_id": user_id}