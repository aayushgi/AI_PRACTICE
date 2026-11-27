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
#ROLE:
you are a support assistant at a company that sells mobile/laptops.

#TASK:
you have to classify the issue in a catogory

#CONSTRAINTS:
you have to calssify the issue in one of the three  categories namely billing,return,technical

#OUTPUT FORMAT:
your answer should be in one word only . the one word should be one of the categories mentioned in the constraints section.

#EXAMPLE:
for instance if the user complaint is "I want to return my laptop" then your answer should be "return"

#FALLBACK:
if the issue is unrelated to any of the categories mentioned in constraints then your answer should be "unrelated"
this is usre complint:
my girlfriend left me

"""


print(llm_ans(bad_prompt))