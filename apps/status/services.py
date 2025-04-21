from .repositories import update_operation_status, get_operation_status
from typing import Dict, Any

def set_status(user_id: int, status: str, role_id: int) -> Dict[str, Any]:
    """
    Set the operation status for a user.
    
    Args:
        user_id (int): The ID of the user.
        status (str): The status to be set.
        
    Returns:
        Dict[str, Any]: A dictionary containing the status and user ID.
    """
    return update_operation_status(user_id, status, role_id)

def get_status(user_id: int, role_id: int) -> str:
    """
    Get the operation status for a user.
    
    Args:
        user_id (int): The ID of the user.
        role_id (int): The ID of the role.
        
    Returns:
        str: The status of the operation.
    """
    return get_operation_status(user_id, role_id)
