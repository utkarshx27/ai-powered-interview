from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from typing import TypedDict, Annotated, Optional, Literal
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv
import csv

model  = ChatOpenAI()

# JD
job_description = "Job Title: Data Scientist, Experience: 1+ years"

# Parsing Resume
resume_loader = PyPDFLoader(r"C:\Users\utkar\Downloads\Utkarsh_Singh_Resume2.pdf")
resume_content =  resume_loader.load()
texts = [doc.page_content for doc in resume_content]
full_resume = "\n\n".join(texts)

class Person(BaseModel):
    name: str = Field(description="Full name")
    email: str = Field(description="Email Address")
    total_experience: int =  Field(description="Years of Experience (In numbers)")
    ph_number: int =  Field(description="Phone Number") 
    city: Optional[str] = Field(description="City of residence")
    technical_skills: Optional[list[str]]= Field(description="Tech Stack (All technical skills)")
    work_history: Optional[str] =  Field(description="Previous Work History (Summary)")
    previous_projects: Optional[list[str]] = Field(description="Projects done like Personal Projects or Opensource Projects")
    links: Optional[list[str]] = Field(description="external links")


parser = PydanticOutputParser(pydantic_object=Person)

prompt = PromptTemplate(
    template=(
        "Here is a resume:\n\n{resume}\n\n"
        "Extract the person’s name, email, phone number, technical skills, work history, projects, total experiance, age, and city.\n"
        "{format_instructions}"
    ),
    input_variables=["resume"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | model | parser

candidates_details_raw = chain.invoke({'resume':full_resume})


def format_resume_data(data: Person) -> str:
    lines = []
    lines.append(f"Name: {data.name}")
    lines.append(f"Email: {data.email}")
    lines.append(f"Phone Number: {data.ph_number}")
    lines.append(f"City: {data.city}")
    lines.append(f"Total Experience: {data.total_experience} years")

    if data.technical_skills:
        skills_formatted = ', '.join(data.technical_skills)
        lines.append(f"Technical Skills: {skills_formatted}")

    if data.work_history:
        lines.append(f"Work History: {data.work_history}")

    if data.previous_projects:
        projects_formatted = ', '.join(data.previous_projects)
        lines.append(f"Previous Projects: {projects_formatted}")

    if data.links:
        links_formatted = ', '.join(data.links)
        lines.append(f"Links: {links_formatted}")

    return '\n'.join(lines)

candidates_details = format_resume_data(candidates_details_raw)


# Interview Chatbot
chat_history = [
    SystemMessage(content="You are a highly intelligent and professional interviewer conducting a job interview. "
        "Your role is to ask questions and evaluate the candidate's responses. "
        "You must NEVER answer on behalf of the candidate. "
        f"Here are the candidate detils: {candidates_details}"
        f"Here is the job description: {job_description}"
        "Start by greeting the candidate and if any candidate detils field is empty then ask for their details one by one in a conversational manner: "
        "Use Technical Skills and , generate 5 technical questions tailored to their skills. "
        "Ask only one question at a time and wait for their response before moving forward. "
        "If they struggle with a question, provide follow-up questions for clarification before moving to the next topic. "
        "If their answer is incomplete, ask for elaboration. If still unsatisfactory, proceed to the next question. "
        "You should only ask questions, acknowledge responses, and encourage further elaboration—DO NOT provide answers or explanations. "
        "End the interview by thanking the candidate for their time and interest in the position. Inform them that they will be contacted regarding the outcome of the interview.")
]


initial_response = model.invoke(chat_history)
chat_history.append(AIMessage(content=initial_response.content))
print("Bot:", initial_response.content)


while True:
    user_input = input("You: ")
    if user_input.lower().strip() == "exit":
        break
    chat_history.append(HumanMessage(content=user_input))
    result = model.invoke(chat_history)
    chat_history.append(AIMessage(content=result.content))
    print("Bot:", result.content)



# Insight

class InterviewFeedback(BaseModel):
    verdict: Literal["Proceed", "Reject"]
    rating: float = Field(..., ge=0, le=1, description="Overall rating from 0 to 1")
    strong_skills: list[str]
    improvement_areas: list[str]
    summary: str  # A concise summary of the evaluation


feedback_parser = PydanticOutputParser(pydantic_object=InterviewFeedback)

evaluation_prompt = PromptTemplate(
    template=(
        "You are an expert technical interviewer.\n\n"
        "Based on the job description:\n{job_description}\n\n"
        "And the candidate details:\n{candidate_details}\n\n"
        "And the full chat history of the interview:\n{chat_history}\n\n"
        "Evaluate the candidate and fill in the following fields:\n"
        "{format_instructions}"
    ),
    input_variables=["job_description", "candidate_details", "chat_history"],
    partial_variables={"format_instructions": feedback_parser.get_format_instructions()}
)

evaluation_chain = evaluation_prompt | model | feedback_parser

interview_feedback = evaluation_chain.invoke({
    "job_description": job_description,
    "candidate_details": candidates_details,
    "chat_history": "\n".join([f"{msg.type.capitalize()}: {msg.content}" for msg in chat_history])
})

print(interview_feedback)


# Store Data
def save_candidate_details_to_csv(candidate_details, chat_history, filename="candidate_details.csv"):
    # Convert list of tuples to dictionary
    candidate_dict = dict(candidate_details)

    # Flatten list-type fields to strings
    for key, value in candidate_dict.items():
        if isinstance(value, list):
            candidate_dict[key] = ", ".join(map(str, value))

    # Add timestamp and chat history
    candidate_dict['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    candidate_dict['ChatHistory'] = chat_history
    candidate_dict['interview_feedback']=interview_feedback

    # Assign a simple ID (based on current row count)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            row_count = sum(1 for row in reader) - 1  
            candidate_dict['id'] = row_count + 1
    else:
        candidate_dict['id'] = 1

    # Write to CSV in append mode
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=candidate_dict.keys())
        if not file_exists or os.path.getsize(filename) == 0:
            writer.writeheader()
        writer.writerow(candidate_dict)

    print(f"Candidate details appended to {filename}")