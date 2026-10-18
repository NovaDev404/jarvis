import os

def delete_file(path):
    """Delete a file"""
    # Expand ~ and resolve relative paths
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)
    try:
        os.remove(path)
        return f"File deleted: {path}"
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

tool = {
    "type": "function",
    "function": {
        "name": "delete_file",
        "description": "Delete a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to delete"
                }
            },
            "required": ["path"]
        },
        "implementation": delete_file
    },
    "critical": True,
    "confirmation_template": "delete the file {path}"
}
