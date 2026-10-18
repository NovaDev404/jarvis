import os

def list_directory(path=None):
    """List files and directories in a path"""
    if path is None:
        path = os.path.expanduser("~")
    else:
        # Expand ~ and resolve relative paths
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            path = os.path.join(os.path.expanduser("~"), path)
    try:
        items = os.listdir(path)
        return "\n".join(sorted(items))
    except FileNotFoundError:
        return f"Directory not found: {path}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"

tool = {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": "List files and directories in a path (defaults to home directory if not specified)",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path to list (default: home directory)"
                }
            },
            "required": []
        },
        "implementation": list_directory
    },
    "critical": False
}
