import json
import re
from groq import Groq
import tools
import tts
import stt

with open("prompt.txt", "r") as file:
    SYSTEM_PROMPT = file.read()

with open("key.txt", "r") as file:
    API_KEY = file.read()

client = Groq(api_key=API_KEY)

def get_confirmation(action_description):
    """Ask user for confirmation via TTS and STT for critical actions."""
    yes_words = ["yes", "yeah", "yep", "sure", "okay", "ok", "please do", "go ahead", "confirm"]
    no_words = ["no", "nope", "don't", "dont", "stop", "cancel", "decline", "not"]
    
    # Speak confirmation prompt
    prompt_text = f"Just to confirm sir, may I {action_description}?"
    tts.speak(prompt_text)
    
    # Listen for response
    stt.flush()
    response = stt.listen(no_speech_timeout=5.0)
    
    if not response:
        return None
    
    response_lower = response.lower()
    
    # Check for yes/no words
    for word in yes_words:
        if re.search(rf'\b{re.escape(word)}\b', response_lower):
            return True
    
    for word in no_words:
        if re.search(rf'\b{re.escape(word)}\b', response_lower):
            return False
    
    # Neither yes nor no detected
    tts.speak("Sorry Sir, I didn't quite catch that.")
    return None

def prompt(user_message, conversation_history=None):
    # Load memory content
    try:
        with open("memory.txt", "r") as f:
            memory_content = f.read().strip()
    except FileNotFoundError:
        memory_content = ""
    
    # Build system prompt with memory appended
    system_prompt = SYSTEM_PROMPT
    if memory_content:
        system_prompt += "\n\nPERMANENT MEMORY\n\n" + memory_content
    
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message,
    })

    # Loop to handle multiple rounds of tool calls
    while True:
        response = client.chat.completions.create(
            messages=messages,
            model="qwen/qwen3.8-27b",
            temperature=0.6,
            max_completion_tokens=1000,
            top_p=0.95,
            stream=False,
            tools=tools.tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # If no tool calls, return the response
        if not tool_calls:
            return response_message.content

        # Add assistant's response to conversation
        messages.append(response_message)

        # Execute each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = tools.available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            # Check if tool is critical and requires confirmation
            tool_def = next((t for t in tools.tools if t["function"]["name"] == function_name), None)
            is_critical = tool_def and tool_def.get("critical", False)
            
            if is_critical:
                # Generate action description for confirmation
                action_desc = f"{function_name} with {function_args}"
                confirmation = get_confirmation(action_desc)
                
                if confirmation is None:
                    function_response = "Confirmation failed - unclear response"
                elif confirmation is False:
                    function_response = "Action declined by user"
                else:
                    # User confirmed, proceed with execution
                    print(f"[TOOL] Calling {function_name} with args: {function_args}")
                    function_response = function_to_call(**function_args)
                    print(f"[TOOL] {function_name} result: {function_response}")
            else:
                # Non-critical tool, execute directly
                print(f"[TOOL] Calling {function_name} with args: {function_args}")
                function_response = function_to_call(**function_args)
                print(f"[TOOL] {function_name} result: {function_response}")

            # Add tool response to conversation
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(function_response)
            })