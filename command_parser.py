import re
import shlex

def parse_command_to_text(command):
    """Convert shell command to readable natural language description."""
    if not command:
        return ""
    
    # Split by && or ; to handle chained commands
    parts = re.split(r'\s*&&\s*|\s*;\s*', command.strip())
    descriptions = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Parse the command using shlex to handle quotes properly
        try:
            tokens = shlex.split(part)
        except ValueError:
            # Fallback to simple split if shlex fails
            tokens = part.split()
        
        if not tokens:
            continue
        
        cmd = tokens[0]
        args = tokens[1:]
        
        desc = _translate_command(cmd, args)
        descriptions.append(desc)
    
    # Join descriptions with semicolons
    if len(descriptions) == 1:
        return descriptions[0]
    elif len(descriptions) == 2:
        return f"{descriptions[0]} and {descriptions[1]}"
    else:
        return "; ".join(descriptions[:-1]) + "; and " + descriptions[-1]

def _format_path_arg(arg):
    """Format a path argument to readable text."""
    if not arg:
        return ""
    
    # Remove trailing slash if present
    arg = arg.rstrip("/")
    
    # Handle tilde expansion
    if arg.startswith("~/"):
        arg = "home" + arg[1:]
    elif arg.startswith("~"):
        arg = "home"
    
    # Split by slashes to handle each component
    parts = arg.split("/")
    formatted_parts = []
    for part in parts:
        if part == "..":
            formatted_parts.append("back")
        elif part == ".":
            continue
        elif part:
            # Replace underscores with spaces
            formatted_parts.append(part.replace("_", " "))
    
    # Join with commas
    return ", ".join(formatted_parts)

def _format_args(args, skip_flags=True):
    """Format command arguments, optionally skipping flags."""
    if not args:
        return ""
    
    formatted = []
    for arg in args:
        # Skip flags if requested
        if skip_flags and arg.startswith("-"):
            continue
        # Format path-like arguments
        if "/" in arg or "~" in arg or "_" in arg:
            formatted.append(_format_path_arg(arg))
        else:
            formatted.append(arg)
    
    return " ".join(formatted)

def _translate_command(cmd, args):
    """Translate a single command to natural language."""
    cmd_lower = cmd.lower()
    
    # Handle common commands
    if cmd_lower == "cd":
        if args and args[0] == "~":
            return "home"
        elif args:
            path = args[0]
            # Remove trailing slash if present
            path = path.rstrip("/")
            # Handle tilde expansion
            if path.startswith("~/"):
                path = "home" + path[1:]
            # Replace slashes with commas and underscores with spaces
            path = path.replace("/", ", ").replace("_", " ")
            return path
        else:
            return "home"
    
    elif cmd_lower == "ls":
        return "list directory"
    
    elif cmd_lower == "echo":
        return "print text"
    
    elif cmd_lower == "cat":
        formatted_args = _format_args(args)
        if formatted_args:
            return f"read {formatted_args} contents"
        return "read file contents"
    
    elif cmd_lower == "pwd":
        return "show current directory"
    
    elif cmd_lower == "mkdir":
        formatted_args = _format_args(args)
        if formatted_args:
            return f"create directory {formatted_args}"
        return "create directory"
    
    elif cmd_lower == "rm":
        formatted_args = _format_args(args)
        if formatted_args:
            return f"remove {formatted_args}"
        return "remove file or directory"
    
    elif cmd_lower == "cp":
        formatted_args = _format_args(args)
        if formatted_args:
            # Split source and destination
            parts = formatted_args.split()
            if len(parts) >= 2:
                return f"copy {parts[0]} to {parts[1]}"
            return f"copy {formatted_args}"
        return "copy file"
    
    elif cmd_lower == "mv":
        formatted_args = _format_args(args)
        if formatted_args:
            # Split source and destination
            parts = formatted_args.split()
            if len(parts) >= 2:
                return f"move {parts[0]} to {parts[1]}"
            return f"move {formatted_args}"
        return "move or rename file"
    
    elif cmd_lower == "touch":
        formatted_args = _format_args(args)
        if formatted_args:
            return f"create {formatted_args}"
        return "create empty file"
    
    elif cmd_lower == "grep":
        formatted_args = _format_args(args, skip_flags=False)
        if formatted_args:
            return f"search for {formatted_args}"
        return "search for text"
    
    elif cmd_lower == "find":
        return "find files"
    
    elif cmd_lower == "wc":
        if "-l" in args:
            return "count lines"
        elif "-w" in args:
            return "count words"
        elif "-c" in args:
            return "count characters"
        else:
            return "count lines, words, and characters"
    
    elif cmd_lower == "head":
        return "show beginning of file"
    
    elif cmd_lower == "tail":
        return "show end of file"
    
    elif cmd_lower == "sort":
        return "sort lines"
    
    elif cmd_lower == "uniq":
        return "remove duplicate lines"
    
    elif cmd_lower == "cut":
        return "extract columns"
    
    elif cmd_lower == "sed":
        return "edit text"
    
    elif cmd_lower == "awk":
        return "process text"
    
    elif cmd_lower == "tar":
        return "archive files"
    
    elif cmd_lower == "zip" or cmd_lower == "unzip":
        return "compress or extract files"
    
    elif cmd_lower == "chmod":
        return "change file permissions"
    
    elif cmd_lower == "chown":
        return "change file owner"
    
    elif cmd_lower == "ps":
        return "list running processes"
    
    elif cmd_lower == "top":
        return "show system processes"
    
    elif cmd_lower == "kill":
        return "terminate process"
    
    elif cmd_lower == "df":
        return "show disk usage"
    
    elif cmd_lower == "du":
        return "show directory size"
    
    elif cmd_lower == "free":
        return "show memory usage"
    
    elif cmd_lower == "ping":
        return "test network connectivity"
    
    elif cmd_lower == "curl" or cmd_lower == "wget":
        return "download from internet"
    
    elif cmd_lower == "ssh":
        return "connect to remote server"
    
    elif cmd_lower == "scp":
        return "copy file over SSH"
    
    elif cmd_lower == "git":
        return _translate_git_command(args)
    
    elif cmd_lower == "pip" or cmd_lower == "pip3":
        return "manage Python packages"
    
    elif cmd_lower == "npm":
        return "manage Node.js packages"
    
    elif cmd_lower == "python" or cmd_lower == "python3":
        return "run Python script"
    
    elif cmd_lower == "node":
        return "run Node.js script"
    
    elif cmd_lower == "bash" or cmd_lower == "sh" or cmd_lower == "zsh":
        return "run shell script"
    
    elif cmd_lower == "make":
        return "build project"
    
    elif cmd_lower == "cmake":
        return "configure build"
    
    elif cmd_lower == "docker":
        return _translate_docker_command(args)
    
    elif cmd_lower == "systemctl":
        return "manage system services"
    
    elif cmd_lower == "journalctl":
        return "view system logs"
    
    else:
        # Generic fallback
        return f"run {cmd}"

def _translate_git_command(args):
    """Translate git subcommands to natural language."""
    if not args:
        return "run git command"
    
    subcommand = args[0]
    
    if subcommand == "log":
        return "get the git log"
    elif subcommand == "status":
        return "get the git status"
    elif subcommand == "add":
        return "stage files for commit"
    elif subcommand == "commit":
        return "commit changes"
    elif subcommand == "push":
        return "push changes to remote"
    elif subcommand == "pull":
        return "pull changes from remote"
    elif subcommand == "clone":
        return "clone repository"
    elif subcommand == "branch":
        return "manage branches"
    elif subcommand == "checkout":
        return "switch branch or restore files"
    elif subcommand == "merge":
        return "merge branches"
    elif subcommand == "diff":
        return "show changes"
    elif subcommand == "reset":
        return "reset changes"
    elif subcommand == "fetch":
        return "fetch from remote"
    else:
        return f"run git {subcommand}"

def _translate_docker_command(args):
    """Translate docker subcommands to natural language."""
    if not args:
        return "run docker command"
    
    subcommand = args[0]
    
    if subcommand == "build":
        return "build docker image"
    elif subcommand == "run":
        return "run docker container"
    elif subcommand == "ps":
        return "list docker containers"
    elif subcommand == "stop":
        return "stop docker container"
    elif subcommand == "start":
        return "start docker container"
    elif subcommand == "rm":
        return "remove docker container"
    elif subcommand == "rmi":
        return "remove docker image"
    elif subcommand == "exec":
        return "execute command in container"
    elif subcommand == "logs":
        return "view container logs"
    else:
        return f"run docker {subcommand}"
