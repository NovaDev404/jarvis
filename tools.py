import json
from datetime import datetime

# ============================================================
# Tool Definitions
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current date and time",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        "critical": False
    },
    {
        "type": "function",
        "function": {
            "name": "add_memory",
            "description": "Add a memory entry to permanent memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The memory content to add"
                    }
                },
                "required": ["content"]
            }
        },
        "critical": False
    },
    {
        "type": "function",
        "function": {
            "name": "remove_memory",
            "description": "Remove a memory entry from permanent memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The exact memory content to remove"
                    }
                },
                "required": ["content"]
            }
        },
        "critical": True
    }
]

# ============================================================
# Tool Implementations
# ============================================================

def get_time():
    """Get the current date and time"""
    now = datetime.now().astimezone()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def add_memory(content):
    """Add a memory entry to permanent memory"""
    with open("memory.txt", "a") as f:
        f.write(content + "\n")
    return f"Memory added: {content}"

def remove_memory(content):
    """Remove a memory entry from permanent memory"""
    try:
        with open("memory.txt", "r") as f:
            lines = f.readlines()
        
        with open("memory.txt", "w") as f:
            for line in lines:
                if line.strip() != content:
                    f.write(line)
        
        return f"Memory removed: {content}"
    except FileNotFoundError:
        return "Memory file not found"

available_functions = {
    "get_time": get_time,
    "add_memory": add_memory,
    "remove_memory": remove_memory
}
