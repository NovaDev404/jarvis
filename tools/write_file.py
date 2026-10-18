import os

def write_file(path, content, mode="overwrite"):
    """Write content to a file"""
    # Expand ~ and resolve relative paths
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)
    try:
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        if mode == "append":
            with open(path, "a") as f:
                f.write(content)
            return f"Content appended to: {path}"
        else:  # overwrite (default)
            with open(path, "w") as f:
                f.write(content)
            return f"File written: {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

tool = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write content to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to write to"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write"
                },
                "mode": {
                    "type": "string",
                    "description": "Write mode: 'overwrite' replaces entire file content, 'append' adds content to end of file (does not add newline automatically)",
                    "enum": ["overwrite", "append"],
                    "default": "overwrite"
                }
            },
            "required": ["path", "content"]
        },
        "implementation": write_file
    },
    "critical": True,
    "confirmation_template": "write to the file {path}"
}
