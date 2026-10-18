import os
import shutil

def delete_directory(path):
    """Delete a directory and all its contents"""
    # Expand ~ and resolve relative paths
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)
    try:
        shutil.rmtree(path)
        return f"Directory deleted: {path}"
    except FileNotFoundError:
        return f"Directory not found: {path}"
    except Exception as e:
        return f"Error deleting directory: {str(e)}"

tool = {
    "type": "function",
    "function": {
        "name": "delete_directory",
        "description": "Delete a directory and all its contents",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path to delete"
                }
            },
            "required": ["path"]
        },
        "implementation": delete_directory
    },
    "critical": True,
    "confirmation_template": "permanently delete the directory {path}"
}
