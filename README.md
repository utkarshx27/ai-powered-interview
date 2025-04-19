# 🤖 AI-Powered Interviewer Bot

An intelligent, resume-aware interviewer built using **Streamlit**, **LangChain**, and **OpenAI**, capable of conducting technical interviews based on a candidate’s resume and job description.

---

## 🚀 Features

- 📄 **Smart Resume Parsing**
  - Upload a resume (PDF), and the system extracts key details like name, email, experience, skills, projects, and more using LLM-based parsing.

- 💬 **AI-Led Technical Interview**
  - Starts the interview automatically based on extracted resume data.
  - Asks tailored technical questions derived from the candidate's tech stack.
  - Handles candidate responses one by one, with follow-ups if needed.
  - Waits for input — no pre-filled answers or handholding.

- 📈 **Automatic Evaluation**
  - After the candidate types `exit`, the system evaluates the interview and returns:
    - ✅ Verdict (`Proceed` / `Reject`)
    - 🌟 Rating (0–1)
    - 💪 Strong skills
    - 🧠 Areas to improve
    - 📝 Summary of performance

- 📊 **Data Logging**
  - Candidate details, chat history, and feedback are stored in a CSV file with a timestamp and unique ID.

---

## 🛠️ Tech Stack

- **Streamlit** – Interactive front-end
- **LangChain** – LLM chaining and prompt engineering
- **OpenAI (via langchain_openai)** – For GPT-based parsing and conversation
- **PyPDFLoader** – Text extraction from resumes
- **Pydantic** – Schema validation for resume and feedback data
- **CSV** – Simple logging format for interview data

---

## 🧑‍💼 How It Works

1. **Resume Upload**
   - Candidate uploads a PDF resume.

2. **Resume Parsing**
   - Key fields are extracted using an LLM chain.

3. **Interview Begins**
   - The AI interviewer greets the candidate and starts asking questions.

4. **Chat Interaction**
   - Questions are based on tech stack; candidate responds in the chat.

5. **Feedback Generation**
   - When the candidate types `exit`, detailed feedback is generated.

6. **Data Storage**
   - All details + feedback are saved in `candidate_details.csv`.

---

## 📂 Project Structure

