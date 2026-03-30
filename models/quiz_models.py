from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class QuestionItem(BaseModel):
    id: str
    quiz_id: str
    question_text: str
    options: List[str]
    correct_answer: str

class QuizItem(BaseModel):
    id: str
    title: str
    topic: str
    created_by: Optional[str] = None
    is_default: bool = False
    quiz_code: Optional[str] = None
    created_at: Optional[datetime] = None

class QuestionCreate(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str

class QuizCreate(BaseModel):
    title: str
    topic: str
    created_by: Optional[str] = None
    questions: List[QuestionCreate]

class AttemptSubmit(BaseModel):
    user_id: str
    answers: dict[str, str]

class AttemptResponse(BaseModel):
    id: str
    user_id: str
    quiz_id: str
    score: int
    ai_feedback: Optional[str]
    created_at: Optional[datetime] = None
