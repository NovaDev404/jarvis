from groq import Groq

with open("prompt.txt", "r") as file:
    SYSTEM_PROMPT = file.read()

with open("key.txt", "r") as file:
    API_KEY = file.read()

client = Groq(api_key=API_KEY)

def prompt(user_message):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            }
        ],
        model="qwen/qwen3.8-27b",
        temperature=0.6,
        max_completion_tokens=1000,
        top_p=0.95,
        stream=False,
    )
    return response.choices[0].message.content