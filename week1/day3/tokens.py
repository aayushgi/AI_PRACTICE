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


# 3 prompt

prompt1="Hi"
prompt2="write an essay on ML in 1000 words"
prompt3="About the future of AI"
promts=[prompt1,prompt2,prompt3]
for prompt in promts:

    message = {"role": role,
            "content": prompt}
    messages=[message]
    response = client.chat.completions.create(model=model, messages=messages, max_tokens=100)
    usage=response.usage
    print(f"Prompt: {prompt} --> your_token:{usage.prompt_tokens} complerion_token: {usage.completion_tokens} total_token: {usage.total_tokens}finish_reason:{response.choices[0].finish_reason}")
#     
# print(response)


# print("************************************************************************************************************************")
# answer=response.choices[0].message.content
# print(answer)