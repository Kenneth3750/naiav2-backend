from redis import Redis
from typing import Dict
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

def get_operation_status(user_id: int, role_id: int) -> str:
    """
    Get the LLM operation status from Redis for an user.
    Args:
        user_id (int): The ID of the user.
        role_id (int): The ID of the role.
    Returns:
        str: The status of the operation.
    """
    load_dotenv()
    redis = Redis(host=os.getenv("redis_host"), port=os.getenv("redis_port"), db=os.getenv("redis_status_db"))
    status = redis.get(f"operation_status_{role_id}_{user_id}")
    redis.close()
    return status.decode('utf-8') if status else None

