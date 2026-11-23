import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq 
load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("API key is required")
client = Groq(api_key=my_api_key)
model = "openai/gpt-oss-120b"
def llm_ans(prompt):
    message = {"role": "user",
                "content": prompt
                }
    messages = [message]
    response=client.chat.completions.create(model=model, messages=messages)
    ans=response.choices[0].message.content
    return ans

bad_prompt="""
this is usre complint:
my laptop is not working
classify this
"""
print(llm_ans(bad_prompt))