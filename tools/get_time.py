from datetime import datetime

def get_time():
    """Get the current date and time"""
    now = datetime.now().astimezone()
    return now.strftime("%Y-%m-%d %I:%M:%S %p")

tool = {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "Get the current date and time",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "implementation": get_time
    },
    "critical": False
}
