from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os
import anyio
import datetime as dt
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import SessionLocal  # our central DB session
from models import Conversation, Message  # unified models

# ---------- PATHS ----------
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DB DEPENDENCY ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- GEMINI CLIENT ----------
class LLMClient:
    async def complete(
        self, model: str, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Asynchronously call Gemini."""

        def _call():
            m = genai.GenerativeModel(model)
            result = m.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            if hasattr(result, "candidates") and result.candidates:
                parts = result.candidates[0].content.parts
                if parts and hasattr(parts[0], "text"):
                    return parts[0].text.strip()
            return getattr(result, "text", "").strip()

        return await anyio.to_thread.run_sync(_call)


llm = LLMClient()
DEFAULT_MODEL = "gemini-2.5-flash"

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

    # Get or create conversation
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

    # Save assistant message
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
        "Review and validate the following 4-week study plan. "
        "Identify missing topics, incorrect ordering, and suggest improvements.\n\n"
        f"{plan_text}\n\n"
        "Provide a clear, concise paragraph of feedback."
    )

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        result = model.generate_content(prompt)

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
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    print(f"Warning: Frontend directory not found at {FRONTEND_DIR}")

    @app.get("/")
    async def frontend_missing():
        return {"error": "Frontend directory not found. Did you build it?"}


# ---------- RUN ----------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
