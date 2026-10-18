import os

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
        
        # Parse and apply the unified diff patch
        try:
            result, applied = _apply_unified_diff(original_lines, patch)
            if result is None:
                return f"Error applying patch: Failed to parse or apply unified diff"
            
            if not applied:
                return f"Error applying patch: No hunks could be applied - context mismatch or file content differs from expected"
            
            new_content = "".join(result)
            
            with open(path, "w") as f:
                f.write(new_content)
            return f"Patch applied to: {path}"
        except Exception as e:
            return f"Error applying patch: {str(e)}"
    except Exception as e:
        return f"Error applying patch: {str(e)}"

def _apply_unified_diff(original_lines, patch_text):
    """Apply a unified diff patch to a list of lines using only stdlib"""
    patch_lines = patch_text.splitlines(keepends=True)
    
    # Parse the patch into hunks
    hunks = []
    current_hunk = None
    i = 0
    
    while i < len(patch_lines):
        line = patch_lines[i]
        
        # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith('@@'):
            if current_hunk is not None:
                hunks.append(current_hunk)
            
            # Extract line numbers from hunk header
            try:
                parts = line.split()
                old_part = parts[1]  # -old_start,old_count
                new_part = parts[2]  # +new_start,new_count
                
                old_start = int(old_part.split(',')[0].lstrip('-'))
                new_start = int(new_part.split(',')[0].lstrip('+'))
                
                current_hunk = {
                    'old_start': old_start - 1,  # Convert to 0-indexed
                    'new_start': new_start - 1,
                    'old_lines': [],
                    'new_lines': []
                }
            except (IndexError, ValueError):
                return None
        
        elif current_hunk is not None:
            if line.startswith('-'):
                current_hunk['old_lines'].append(line[1:])
            elif line.startswith('+'):
                current_hunk['new_lines'].append(line[1:])
            elif line.startswith(' '):
                # Context line: keep the space as it matches the actual file content
                current_hunk['old_lines'].append(line)
                current_hunk['new_lines'].append(line)
            elif line.startswith('\\') and 'No newline' in line:
                # Handle "\ No newline at end of file" - ignore
                pass
            # Skip --- and +++ headers
        
        i += 1
    
    if current_hunk is not None:
        hunks.append(current_hunk)
    
    if not hunks:
        return None
    
    # Apply hunks to the original lines
    result = original_lines.copy()
    offset = 0  # Track line offset due to previous hunks
    applied = False  # Track if any hunk was successfully applied
    
    for hunk in hunks:
        old_start = hunk['old_start'] + offset
        old_lines = hunk['old_lines']
        new_lines = hunk['new_lines']
        
        # Find the location in the current result
        if old_start >= len(result):
            # Hunk is beyond file end
            continue
        
        # Check if the old lines match
        match_start = old_start
        match_end = old_start + len(old_lines)
        
        if match_end > len(result):
            # Not enough lines to match
            continue
        
        # Verify the context matches
        actual_old = result[match_start:match_end]
        if actual_old != old_lines:
            # Try to find the match by searching (fuzzy matching)
            found = False
            for search_offset in range(-3, 4):  # Search within 3 lines
                test_start = old_start + search_offset
                if test_start < 0 or test_start + len(old_lines) > len(result):
                    continue
                if result[test_start:test_start + len(old_lines)] == old_lines:
                    match_start = test_start
                    match_end = test_start + len(old_lines)
                    offset += search_offset
                    found = True
                    break
            
            if not found:
                # Context doesn't match, skip this hunk
                continue
        
        # Apply the hunk: replace old_lines with new_lines
        result[match_start:match_end] = new_lines
        applied = True
        
        # Update offset for subsequent hunks
        offset += len(new_lines) - len(old_lines)
    
    return result, applied

tool = {
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
        },
        "implementation": apply_patch
    },
    "critical": True,
    "confirmation_template": "apply a patch to the file {path}"
}
