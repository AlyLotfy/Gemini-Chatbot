from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os, anyio, datetime as dt
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session

# ---------- PATHS ----------
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
# This path might need adjustment depending on your frontend build setup
FRONTEND_DIR = BACKEND_DIR / "dist" 

DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------- ENVIRONMENT ----------
load_dotenv(BACKEND_DIR / ".env")
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in backend/.env")

genai.configure(api_key=API_KEY)

# ---------- FASTAPI ----------
app = FastAPI(title="Gemini Chatbot with Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# ---------- DATABASE ----------
# --- MODIFIED FOR ASSIGNMENT ---
# This line now reads from the "DATABASE_URL" environment variable (for Postgres)
# If it's not found, it falls back to your original SQLite database.
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'chat.db').as_posix()}")
# -----------------------------

# Add check_same_thread: False only if using SQLite
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), index=True, nullable=True)
    course = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=dt.datetime.utcnow)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(16)) # "user" or "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")

# This line is handled by Alembic when using Postgres
if DB_URL.startswith("sqlite"):
    Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- GEMINI CLIENT ----------
class LLMClient:
    async def complete(self, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Asynchronously calls the Gemini API."""
        def _call():
            m = genai.GenerativeModel(model)
            result = m.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            # Handle response structure
            if hasattr(result, "candidates") and result.candidates:
                parts = result.candidates[0].content.parts
                if parts and hasattr(parts[0], "text"):
                    return parts[0].text.strip()
            return getattr(result, "text", "").strip() # Fallback for older models
        
        # Run the synchronous SDK call in a separate thread
        return await anyio.to_thread.run_sync(_call)

llm = LLMClient()
DEFAULT_MODEL = "gemini-2.5-flash" # Use a modern, fast model

# ---------- SCHEMAS ----------
class Query(BaseModel):
    query: str
    course: Optional[str] = None
    user_email: Optional[str] = None
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: Optional[int] = None

class PlanRequest(BaseModel):
    topic: str

class ValidateRequest(BaseModel):
    plan: str

# ---------- CHATBOT ENDPOINT ----------
@app.post("/v1/ai-student-qa", response_model=ChatResponse)
async def ai_student_qa(req: Query, db: Session = Depends(get_db)):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Field 'query' is required.")
    question = req.query.strip()

    # Find existing conversation or create a new one
    conv = db.query(Conversation).get(req.session_id) if req.session_id else None
    if conv is None:
        conv = Conversation(user_email=req.user_email, course=req.course)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    db.add(Message(conversation_id=conv.id, role="user", content=question))
    db.commit()

    # Build prompt
    prompt = (
        "Role: Formal, clear study assistant for a student.\n"
        "- Answer briefly (one paragraph max).\n"
        f"Course: {req.course or conv.course or 'General'}\n"
        f"Question: {question}\n"
        "Answer:"
    )

    try:
        answer = await llm.complete(DEFAULT_MODEL, prompt, 0.2, 512)
    except Exception as e:
        import traceback
        print("=== GEMINI ERROR TRACE ===")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

    # Save bot message
    db.add(Message(conversation_id=conv.id, role="assistant", content=answer))
    db.commit()

    return ChatResponse(answer=answer, session_id=conv.id)

# ---------- PLANNER ENDPOINTS ----------
@app.post("/Planner/plan")
async def planner_plan(req: PlanRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Field 'topic' is required.")

    prompt = (
        f"Create a 4-week structured learning plan for {topic}. "
        "Return a concise JSON-style text with keys Week1-Week4 and brief goals for each."
    )

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        result = model.generate_content(prompt)

        # Defensive parsing
        text = ""
        if hasattr(result, "candidates") and result.candidates:
            cand = result.candidates[0]
            if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                for p in cand.content.parts:
                    if hasattr(p, "text") and p.text:
                        text += p.text.strip() + "\n"

        if not text:
            text = "⚠️ Gemini did not return text. Try re-running with a simpler prompt."

        return {"plan": text.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planner error: {str(e)}")



@app.post("/Planner/validate")
async def planner_validate(req: ValidateRequest):
    plan_text = req.plan.strip()
    if not plan_text:
        raise HTTPException(status_code=400, detail="Field 'plan' is required.")

    prompt = (
        f"Review and validate the following 4-week study plan. "
        f"Identify missing topics, incorrect ordering, and suggest improvements.\n\n{plan_text}\n\n"
        "Provide a clear, concise paragraph of feedback."
    )

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        result = model.generate_content(prompt)

        # --- Defensive parsing ---
        text = ""
        if hasattr(result, "candidates") and result.candidates:
            cand = result.candidates[0]
            if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                for part in cand.content.parts:
                    if hasattr(part, "text") and part.text:
                        text += part.text.strip() + "\n"

        if not text:
            text = (
                "⚠️ Gemini did not return validation text. Try again with a shorter plan."
            )

        return {"validation": text.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

# ---------- HEALTH CHECK ----------
@app.get("/health")
def health():
    return {"status": "ok", "message": "Backend is running"}

# ---------- SERVE FRONTEND ----------
# This serves your frontend's index.html from the "dist" folder
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    print(f"Warning: Frontend directory not found at {FRONTEND_DISTR}")
    @app.get("/")
    async def frontend_missing():
        return {"error": "Frontend directory not found. Did you build it?"}

# ---------- RUN ----------
if __name__ == "__main__":
    import uvicorn
    # Host 0.0.0.0 makes it accessible inside the Docker container
    uvicorn.run(app, host="0.0.0.0", port=8000)