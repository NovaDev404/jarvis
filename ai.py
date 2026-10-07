import json
import re
import time
from groq import Groq
import tools
import tts
import stt
import web_server

with open("prompt.txt", "r") as file:
    SYSTEM_PROMPT = file.read()

with open("key.txt", "r") as file:
    API_KEY = file.read()

client = Groq(api_key=API_KEY)

def get_confirmation(action_description, text_mode=False, conversation_id=None):
    """Ask user for confirmation via TTS/STT (voice) or WebSocket (text) for critical actions."""
    if text_mode:
        # Text mode: request confirmation via WebSocket
        return web_server.request_text_confirmation(action_description, conversation_id)
    
    # Voice mode: use TTS and STT
    yes_words = ["yes", "yeah", "yep", "sure", "okay", "ok", "please do", "go ahead", "confirm"]
    no_words = ["no", "nope", "don't", "dont", "stop", "cancel", "decline", "not"]
    
    while True:
        # Speak confirmation prompt
        prompt_text = f"Just to confirm sir, may I {action_description}?"
        audio_path = tts.speak(prompt_text)
        if audio_path is not None:
            web_server.send_tts(audio_path)
            web_server.wait_for_tts_finished()
        
        # Listen for response
        stt.flush()
        response = stt.listen(no_speech_timeout=5.0)
        
        if not response:
            # No response, repeat the question
            continue
        
        response_lower = response.lower()
        
        # Check for yes/no words
        for word in yes_words:
            if re.search(rf'\b{re.escape(word)}\b', response_lower):
                return True
        
        for word in no_words:
            if re.search(rf'\b{re.escape(word)}\b', response_lower):
                return False
        
        # Neither yes nor no detected, repeat the question
        audio_path = tts.speak("Sorry Sir, I didn't quite catch that.")
        if audio_path is not None:
            web_server.send_tts(audio_path)
            web_server.wait_for_tts_finished()

def prompt(user_message, conversation_history=None, text_mode=False, conversation_id=None):
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
        start_time = time.time()
        print(f"[AI] Calling Groq API...")
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
        elapsed = time.time() - start_time
        print(f"[AI] Groq API call completed in {elapsed:.2f}s")

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
                # Generate action description for confirmation using template
                template = tool_def.get("confirmation_template")
                if template:
                    try:
                        action_desc = template.format(**function_args)
                    except (KeyError, ValueError):
                        # Fallback if template formatting fails
                        action_desc = f"{function_name} with {function_args}"
                else:
                    # Fallback if no template defined
                    action_desc = f"{function_name} with {function_args}"
                confirmation = get_confirmation(action_desc, text_mode=text_mode, conversation_id=conversation_id)

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