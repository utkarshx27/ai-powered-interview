import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Literal
from datetime import datetime
import os
import tempfile
from typing import TypedDict, Annotated, Optional, Literal
import csv

# Init OpenAI model
model = ChatOpenAI()

# Pydantic fields for candidates details
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


# Pydantic fields for candidates interview result
class InterviewFeedback(BaseModel):
    verdict: Literal["Proceed", "Reject"]
    rating: float = Field(..., ge=0, le=1, description="Overall rating from 0 to 1")
    strong_skills: list[str]
    improvement_areas: list[str]
    summary: str 


# Init session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'welcome'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

# Job description
job_description = "Job Title: Data Scientist, Experience: 1+ years"


# Resume Parseing
def process_resume(uploaded_file):
    """Process uploaded resume and extract details"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    loader = PyPDFLoader(tmp_file_path)
    resume_content = loader.load()
    texts = [doc.page_content for doc in resume_content]
    full_resume = "\n\n".join(texts)
    
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
    return chain.invoke({'resume': full_resume})


# Interview 
def run_interview():
    """Run the interview conversation"""
    if len(st.session_state.chat_history) == 0:
        system_message = SystemMessage(content=
            "You are a highly intelligent and professional interviewer conducting a job interview. "
            "Your role is to ask questions and evaluate the candidate's responses. "
            "You must NEVER answer on behalf of the candidate. "
            f"Here are the candidate details: {st.session_state.candidate_details}"
            f"Here is the job description: {job_description}"
            "Start by greeting the candidate and if any candidate detils field is empty then ask for their details one by one in a conversational manner: "
            "Use Technical Skills and , generate 5 technical questions tailored to their skills. "
            "Ask only one question at a time and wait for their response before moving forward. "
            "If they struggle with a question, provide follow-up questions for clarification before moving to the next topic. "
            "If their answer is incomplete, ask for elaboration. If still unsatisfactory, proceed to the next question. "
            "You should only ask questions, acknowledge responses, and encourage further elaboration—DO NOT provide answers or explanations. "
            "End the interview by thanking the candidate for their time and interest in the position. Inform them to Type exit to see interview results.")
        st.session_state.chat_history.append(system_message)
        ai_response = model.invoke(st.session_state.chat_history)
        st.session_state.chat_history.append(AIMessage(content=ai_response.content))


# Feedback
def generate_feedback():
    """Generate interview feedback"""
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
    return evaluation_chain.invoke({
        "job_description": job_description,
        "candidate_details": st.session_state.candidate_details,
        "chat_history": "\n".join([f"{msg.type.capitalize()}: {msg.content}" for msg in st.session_state.chat_history])
    })


# Store Data
def save_candidate_details_to_csv(candidate_details, chat_history, interview_feedback, filename="candidate_details.csv"):

    candidate_dict = dict(candidate_details)

    for key, value in candidate_dict.items():
        if isinstance(value, list):
            candidate_dict[key] = ", ".join(map(str, value))

    candidate_dict['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    candidate_dict['chat_history'] = chat_history
    candidate_dict['verdict'] = interview_feedback.verdict
    candidate_dict['rating'] = interview_feedback.rating
    candidate_dict['summary'] = interview_feedback.summary

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            row_count = sum(1 for row in reader) - 1  
            candidate_dict['id'] = row_count + 1
    else:
        candidate_dict['id'] = 1

    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=candidate_dict.keys())
        if not file_exists or os.path.getsize(filename) == 0:
            writer.writeheader()
        writer.writerow(candidate_dict)

    print(f"Candidate details appended to {filename}")


# App layout
def main():
    st.title("AI Powered Interview")
    
    if st.session_state.stage == 'welcome':
        st.subheader("Job Description")
        st.write(job_description)
        
        uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
        if uploaded_file:
            with st.spinner("Processing resume..."):
                st.session_state.candidate_details = process_resume(uploaded_file)
                st.session_state.stage = 'interview'
                st.rerun()
    
    elif st.session_state.stage == 'interview':
        run_interview() 
        st.subheader("Interview Session")
        

        for msg in st.session_state.chat_history[1:]: 
            if isinstance(msg, AIMessage):
                with st.chat_message("assistant"):
                    st.write(msg.content)
            elif isinstance(msg, HumanMessage):
                with st.chat_message("user"):
                    st.write(msg.content)
        
        if prompt := st.chat_input("Type your response..."):
            if prompt.lower() == 'exit':
                with st.spinner("Generating feedback..."):
                    st.session_state.feedback = generate_feedback()
                    st.session_state.stage = 'insights'
                    st.rerun()
            else:
                st.session_state.chat_history.append(HumanMessage(content=prompt))
                with st.spinner("Analyzing response..."):
                    ai_response = model.invoke(st.session_state.chat_history)
                    st.session_state.chat_history.append(AIMessage(content=ai_response.content))
                    st.rerun()
    
    elif st.session_state.stage == 'insights':
        st.subheader("Interview Insights")
        
        if st.session_state.feedback:
            feedback = st.session_state.feedback
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Verdict", feedback.verdict)
                st.metric("Overall Rating", f"{feedback.rating*100:.1f}%")
            
            with col2:
                st.write("**Strong Skills:**")
                for skill in feedback.strong_skills:
                    st.write(f"- {skill}")
                
                st.write("**Improvement Areas:**")
                for area in feedback.improvement_areas:
                    st.write(f"- {area}")
            
            st.subheader("Summary")
            st.write(feedback.summary)
            save_candidate_details_to_csv(
                candidate_details=st.session_state.candidate_details,
                chat_history="\n".join([f"{msg.type}: {msg.content}" for msg in st.session_state.chat_history]),
            interview_feedback=st.session_state.feedback
        )
            
            if st.button("Start New Interview"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()