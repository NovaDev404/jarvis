def add_memory(content):
    """Add a memory entry to permanent memory"""
    with open("memory.txt", "a") as f:
        f.write(content + "\n")
    return f"Memory added: {content}"

tool = {
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
        },
        "implementation": add_memory
    },
    "critical": False
}
