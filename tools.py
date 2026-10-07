import json
import subprocess
import os
import difflib
import shutil
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
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute"
                    }
                },
                "required": ["command"]
            }
        },
        "critical": True
    },
    {
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
            }
        },
        "critical": False
    },
    {
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
            }
        },
        "critical": False
    },
    {
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
            }
        },
        "critical": True
    },
    {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "description": "Apply a unified diff patch to a file. The patch should be in standard unified diff format starting with '---' for the original file and '+++' for the new version, followed by '@@' line numbers and changes marked with '-' for removals and '+' for additions. Example: '--- a/file.txt\\n+++ b/file.txt\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line'",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to apply the patch to"
                    },
                    "patch": {
                        "type": "string",
                        "description": "The unified diff patch content in standard format with ---, +++, @@, -, and + markers"
                    }
                },
                "required": ["path", "patch"]
            }
        },
        "critical": True
    },
    {
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
            }
        },
        "critical": True
    },
    {
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

def run_command(command):
    """Execute a shell command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout if result.stdout else result.stderr
        return output if output else "Command executed with no output"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

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

def apply_patch(path, patch):
    """Apply a unified diff patch to a file"""
    # Expand ~ and resolve relative paths
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)
    try:
        # Read original file
        try:
            with open(path, "r") as f:
                original_lines = f.readlines()
        except FileNotFoundError:
            return f"File not found for patch application: {path}"
        
        # Apply the patch
        try:
            new_lines = list(difflib.restore(original_lines, 1, patch.splitlines(keepends=True)))
            new_content = "".join(new_lines)
            
            with open(path, "w") as f:
                f.write(new_content)
            return f"Patch applied to: {path}"
        except Exception as e:
            return f"Error applying patch: {str(e)}"
    except Exception as e:
        return f"Error applying patch: {str(e)}"

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

available_functions = {
    "get_time": get_time,
    "add_memory": add_memory,
    "remove_memory": remove_memory,
    "run_command": run_command,
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "apply_patch": apply_patch,
    "delete_file": delete_file,
    "delete_directory": delete_directory
}
