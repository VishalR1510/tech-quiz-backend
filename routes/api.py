from fastapi import APIRouter, HTTPException, Depends
from models.quiz_models import QuizCreate, AttemptSubmit
from database.supabase import get_supabase
from services.ai_service import generate_feedback
import uuid

router = APIRouter()

def db_client():
    client = get_supabase()
    if not client:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return client

@router.get("/quizzes/default")
async def get_default_quizzes(db=Depends(db_client)):
    try:
        res = db.table("quizzes").select("*").eq("is_default", True).execute()
        return {"data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quiz/{quiz_id}")
async def get_quiz(quiz_id: str, db=Depends(db_client)):
    try:
        quiz_res = db.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not quiz_res.data:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        questions_res = db.table("questions").select("*").eq("quiz_id", quiz_id).execute()
        questions = questions_res.data
        for q in questions:
            q.pop("correct_answer", None) # Hide correct answer from frontend
            
        return {
            "quiz": quiz_res.data[0],
            "questions": questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quiz/code/{code}")
async def get_quiz_by_code(code: str, db=Depends(db_client)):
    try:
        quiz_res = db.table("quizzes").select("*").eq("quiz_code", code).execute()
        if not quiz_res.data:
            raise HTTPException(status_code=404, detail="Invalid quiz code")
        return {"quiz_id": quiz_res.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quiz/create")
async def create_quiz(quiz_data: QuizCreate, db=Depends(db_client)):
    try:
        quiz_code = str(uuid.uuid4())[:8].upper()
        
        quiz_insert = db.table("quizzes").insert({
            "title": quiz_data.title,
            "topic": quiz_data.topic,
            "created_by": quiz_data.created_by,
            "is_default": False,
            "quiz_code": quiz_code
        }).execute()
        
        quiz_id = quiz_insert.data[0]["id"]
        
        questions_data = []
        for q in quiz_data.questions:
            questions_data.append({
                "quiz_id": quiz_id,
                "question_text": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer
            })
            
        if questions_data:
            db.table("questions").insert(questions_data).execute()
            
        return {"message": "Quiz created successfully", "quiz_code": quiz_code, "quiz_id": quiz_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, attempt_data: AttemptSubmit, db=Depends(db_client)):
    try:
        quiz_res = db.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not quiz_res.data:
            raise HTTPException(status_code=404, detail="Quiz not found")
        topic = quiz_res.data[0]["topic"]

        questions_res = db.table("questions").select("*").eq("quiz_id", quiz_id).execute()
        questions = questions_res.data
        
        score = 0
        total = len(questions)
        eval_data = []
        
        for q in questions:
            q_id = str(q["id"])
            correct = q["correct_answer"]
            user_ans = attempt_data.answers.get(q_id, "")
            is_correct = (user_ans == correct)
            if is_correct:
                score += 1
            
            eval_data.append({
                "question": q["question_text"],
                "user_answer": user_ans,
                "is_correct": is_correct
            })
            
        ai_feedback = await generate_feedback(score, total, topic, eval_data)
        
        attempt_insert = db.table("attempts").insert({
            "user_id": attempt_data.user_id,
            "quiz_id": quiz_id,
            "answers": attempt_data.answers,
            "score": score,
            "ai_feedback": ai_feedback
        }).execute()
        
        return {
            "attempt_id": attempt_insert.data[0]["id"],
            "score": score,
            "total": total,
            "ai_feedback": ai_feedback
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quiz/{quiz_id}/results")
async def get_results(quiz_id: str, user_id: str, db=Depends(db_client)):
    try:
        attempts = db.table("attempts").select("*").eq("quiz_id", quiz_id).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        if not attempts.data:
            raise HTTPException(status_code=404, detail="Attempt not found")
        return attempts.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
