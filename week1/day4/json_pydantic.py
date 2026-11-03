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
#stuructured data extraction from unstructured data
from pydantic import BaseModel
class Ticket(BaseModel):
    name:str
    email:str
    phone:int
    issue:str
    
schema=Ticket.model_json_schema()

response_format={
    "type":"json_object"
} 

system_prompt=f"""
Extract the  information from ticket stricly based on this schema and give json output:
{schema}"""

message_system={
    "role":"user",
    "content":system_prompt
}


text = "hellow my name is ayush i am purchasing an car from you and its mboil will leaked i want my money back my phjone number is 1234567890 and my email id is abc@gmail.com my address is delhi"
prompt=f"""
this is a costumer ticket extract informtion and give it to me
{text}
"""

message = {"role": role,
           "content": prompt}
messages=[message_system,message]
response = client.chat.completions.create(model=model, messages=messages,response_format=response_format)



answer=response.choices[0].message.content
print(answer)


#how to read it 
import json
raw_json=answer
data_file=json.loads(raw_json)
ticket=Ticket(**data_file)
print(ticket.name)
print(ticket.email)
print(ticket.phone)