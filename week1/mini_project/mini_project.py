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
class Recruitment(BaseModel):
    name:str
    email:str
    phone:int
    skills:str
    projects:str
    experience:str
    
schema=Recruitment.model_json_schema()

response_format={
    "type":"json_object"
} 

system_prompt=f"""
Extract the  information from recruitment ticket stricly based on this schema and give json output:
{schema}"""

message_system={
    "role":"user",
    "content":system_prompt
}


text = "AYUSH SHARMA | AI/ML Engineer | Email: ayush.sharma@example.com | Phone: +91 9876543210 | Location: Lucknow, Uttar Pradesh | LinkedIn: linkedin.com/in/ayushsharma | GitHub: github.com/ayushsharma | Education: B.Tech Computer Science Engineering, ABC Institute of Technology, Lucknow (2022–2026), CGPA: 8.4/10 | Class XII: XYZ Public School, 2022, 85% | Technical Skills: Python, SQL, Java, Machine Learning, Deep Learning, NLP, LLMs, LangChain, NumPy, Pandas, Scikit-learn, Matplotlib, Flask, FastAPI, HTML, CSS, MySQL, Git, GitHub | Projects: AI-Powered Resume Analyzer (Python, NLP, Pydantic), House Price Prediction (Linear Regression, Random Forest, 89% R² score), Movie Recommendation System (Python, Cosine Similarity, TMDB API, Streamlit) | Internship: Machine Learning Intern at Tech Solutions Pvt. Ltd. (January 2025 – March 2025) | Responsibilities: Data cleaning, preprocessing, EDA, ML model development, visualization | Certifications: Machine Learning – IIT Kanpur, Data Analysis with Python – IIT Roorkee, Python Programming – Coursera, SQL for Data Science – Great Learning | Achievements: Participated in national-level hackathon, solved 150+ coding problems, developed 3+ projects | Soft Skills: Problem Solving, Communication, Teamwork, Critical Thinking, Adaptability | Languages: English, Hindi"
prompt=f"""
this is a recuritment extract informtion and give it to me
{text}
"""

message = {"role": role,
           "content": prompt}
messages=[message_system,message]
response = client.chat.completions.create(model=model, messages=messages,response_format=response_format)



answer=response.choices[0].message.content
# print(answer)


#how to read it 
import json
raw_json=answer
data_file=json.loads(raw_json)
recruitment=Recruitment(**data_file)
print(recruitment.name)
print(recruitment.email)
print(recruitment.phone)
print(recruitment.skills)
print(recruitment.projects)
print(recruitment.experience)