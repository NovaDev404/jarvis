import subprocess

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

tool = {
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
        },
        "implementation": run_command
    },
    "critical": True,
    "confirmation_template": "run the command `{command}`"
}
