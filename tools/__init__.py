# Tool modules
from .get_time import tool as get_time_tool
from .add_memory import tool as add_memory_tool
from .remove_memory import tool as remove_memory_tool
from .run_command import tool as run_command_tool
from .list_directory import tool as list_directory_tool
from .read_file import tool as read_file_tool
from .write_file import tool as write_file_tool
from .apply_patch import tool as apply_patch_tool
from .delete_file import tool as delete_file_tool
from .delete_directory import tool as delete_directory_tool
from .send_email import tool as send_email_tool
from .calculator import tool as calculator_tool

# Aggregate all tool definitions
tools = [
    get_time_tool,
    add_memory_tool,
    remove_memory_tool,
    run_command_tool,
    list_directory_tool,
    read_file_tool,
    write_file_tool,
    apply_patch_tool,
    delete_file_tool,
    delete_directory_tool,
    send_email_tool,
    calculator_tool
]

# Aggregate all function implementations
available_functions = {
    "get_time": get_time_tool["function"]["implementation"],
    "add_memory": add_memory_tool["function"]["implementation"],
    "remove_memory": remove_memory_tool["function"]["implementation"],
    "run_command": run_command_tool["function"]["implementation"],
    "list_directory": list_directory_tool["function"]["implementation"],
    "read_file": read_file_tool["function"]["implementation"],
    "write_file": write_file_tool["function"]["implementation"],
    "apply_patch": apply_patch_tool["function"]["implementation"],
    "delete_file": delete_file_tool["function"]["implementation"],
    "delete_directory": delete_directory_tool["function"]["implementation"],
    "send_email": send_email_tool["function"]["implementation"],
    "calculator": calculator_tool["function"]["implementation"]
}

def get_api_tools():
    """Return tool definitions compatible with AI APIs (removes local metadata)"""
    api_tools = []
    for tool in tools:
        api_tool = {
            "type": tool["type"],
            "function": {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "parameters": tool["function"]["parameters"]
            }
        }
        api_tools.append(api_tool)
    return api_tools
