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

tool = {
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
        },
        "implementation": remove_memory
    },
    "critical": True,
    "confirmation_template": "remove the memory entry: {content}"
}
