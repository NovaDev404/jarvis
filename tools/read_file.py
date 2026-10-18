import os

def read_file(path):
    """Read the contents of a file"""
    # Expand ~ and resolve relative paths
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

tool = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to read"
                }
            },
            "required": ["path"]
        },
        "implementation": read_file
    },
    "critical": False
}
