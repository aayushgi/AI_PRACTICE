import os 
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("API key is required")
client=Groq(api_key=my_api_key)
model = "openai/gpt-oss-120b"
role="user"
prompt="suggest any nmae for my food brand?"

message_system={
    
    "role":"system",
    "content": "you are my an brand manager who suggest the name for my food brand in one word"
}

message = {"role": role,
           "content": prompt}
messages=[message_system,message]

#temperature by defalut is 0 meaning safe 
response = client.chat.completions.create(model=model, messages=messages, temperature=2)
# print(response)


print("************************************************************************************************************************")
answer=response.choices[0].message.content
print(answer)