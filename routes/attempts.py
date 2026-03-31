"""Quiz attempt and results routes"""
from fastapi import APIRouter, HTTPException, Depends
from models.quiz_models import AttemptSubmit
from services.ai_service import generate_feedback
from .dependencies import db_admin

router = APIRouter(tags=["Attempts"])


def _resolve_quiz_id(quiz_id: str, db) -> str:
    """
    Resolve quiz_id which could be UUID or quiz_code.
    Returns actual_quiz_id (UUID format)
    """
    try:
        # First try UUID
        print(f"[DEBUG] Trying UUID lookup...")
        quiz_res = db.table("quizzes").select("id").eq("id", quiz_id).execute()
        if quiz_res.data:
            return quiz_res.data[0]["id"]
    except Exception as uuid_err:
        pass
    
    # If UUID fails, try quiz_code
    print(f"[DEBUG] UUID lookup failed, trying quiz_code...")
    quiz_res = db.table("quizzes").select("id").eq("quiz_code", quiz_id).execute()
    
    if quiz_res.data:
        return quiz_res.data[0]["id"]
    
    raise HTTPException(status_code=404, detail="Quiz not found")


@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, attempt_data: AttemptSubmit, db=Depends(db_admin)):
    """Submit quiz and generate AI feedback"""
    try:
        print(f"[DEBUG] Submitting quiz: {quiz_id}")
        print(f"[DEBUG] User ID: {attempt_data.user_id}")
        print(f"[DEBUG] Answers: {attempt_data.answers}")
        
        # Resolve quiz_id
        actual_quiz_id = _resolve_quiz_id(quiz_id, db)
        
        # Get quiz details
        quiz_res = db.table("quizzes").select("*").eq("id", actual_quiz_id).execute()
        if not quiz_res.data:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        quiz_data = quiz_res.data[0]
        print(f"[DEBUG] Found quiz: {quiz_data['title']}")
        topic = quiz_data["topic"]
        
        # Get questions
        questions_res = db.table("questions").select("*").eq("quiz_id", actual_quiz_id).execute()
        questions = questions_res.data
        print(f"[DEBUG] Found {len(questions)} questions")
        
        # Calculate score
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
            
            print(f"[DEBUG] Q: {q_id}, Expected: {correct}, Got: {user_ans}, Correct: {is_correct}")
            
            eval_data.append({
                "question": q["question_text"],
                "user_answer": user_ans,
                "is_correct": is_correct,
                "correct_answer": correct
            })
        
        print(f"[DEBUG] Score: {score}/{total}")
        
        # Generate AI feedback
        print(f"[DEBUG] Generating AI feedback...")
        ai_feedback = await generate_feedback(score, total, topic, eval_data)
        print(f"[DEBUG] AI feedback generated")
        
        # Insert attempt record
        print(f"[DEBUG] Inserting attempt record...")
        attempt_insert = db.table("attempts").insert({
            "user_id": attempt_data.user_id,
            "quiz_id": actual_quiz_id,
            "answers": attempt_data.answers,
            "score": score,
            "ai_feedback": ai_feedback
        }).execute()
        print(f"[DEBUG] Attempt inserted successfully")
        
        return {
            "attempt_id": attempt_insert.data[0]["id"],
            "score": score,
            "total": total,
            "ai_feedback": ai_feedback
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in submit_quiz: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/quiz/{quiz_id}/results")
async def get_results(quiz_id: str, user_id: str, db=Depends(db_admin)):
    """Get quiz results for a user"""
    try:
        print(f"[DEBUG] Fetching results for quiz: {quiz_id}, user: {user_id}")
        
        # Resolve quiz_id
        actual_quiz_id = _resolve_quiz_id(quiz_id, db)
        print(f"[DEBUG] Using actual_quiz_id: {actual_quiz_id}")
        
        # Get the most recent attempt
        attempts = db.table("attempts").select("*") \
            .eq("quiz_id", actual_quiz_id) \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if not attempts.data:
            print(f"[DEBUG] No attempts found")
            raise HTTPException(status_code=404, detail="Attempt not found")
        
        print(f"[DEBUG] Attempt found successfully")
        return attempts.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in get_results: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
