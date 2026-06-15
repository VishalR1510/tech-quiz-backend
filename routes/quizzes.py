"""Quiz management routes"""
from fastapi import APIRouter, HTTPException, Depends
from models.quiz_models import QuizCreate
from .dependencies import db_client, db_admin
import uuid

# Note: This router handles both /quizzes and /quiz prefixes
# List endpoints: /quizzes/default, /quizzes/my-quizzes/{user_id}
# Action endpoints: /quiz/*, /quiz/{quiz_id}
router = APIRouter(tags=["Quizzes"])


@router.get("/quizzes/default")
async def get_default_quizzes(db=Depends(db_client)):
    """Get all default quizzes"""
    try:
        res = db.table("quizzes").select("*").eq("is_default", True).execute()
        return {"data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quizzes/my-quizzes/{user_id}")
async def get_user_quizzes(user_id: str, db=Depends(db_client)):
    """Get quizzes created by a specific user"""
    try:
        res = db.table("quizzes").select("*").eq("created_by", user_id).execute()
        return {"data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_quiz_id(quiz_id: str, db) -> tuple:
    """
    Resolve quiz_id which could be UUID or quiz_code.
    Returns (actual_quiz_id, quiz_data)
    """
    quiz_res = None
    
    try:
        # First try UUID
        print(f"[DEBUG] Trying UUID query...")
        quiz_res = db.table("quizzes").select("*").eq("id", quiz_id).execute()
        print(f"[DEBUG] UUID query result: {len(quiz_res.data) if quiz_res.data else 0} quizzes found")
    except Exception as uuid_err:
        # If UUID fails, try quiz_code
        print(f"[DEBUG] UUID query failed, trying quiz_code...")
        quiz_res = db.table("quizzes").select("*").eq("quiz_code", quiz_id).execute()
        print(f"[DEBUG] Quiz code query result: {len(quiz_res.data) if quiz_res.data else 0} quizzes found")
    
    if not quiz_res.data:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return quiz_res.data[0]["id"], quiz_res.data[0]


@router.get("/quiz/{quiz_id}")
async def get_quiz(quiz_id: str, db=Depends(db_admin)):
    """Get a single quiz with questions"""
    try:
        print(f"[DEBUG] Fetching quiz with ID/code: {quiz_id}")
        
        actual_quiz_id, quiz_data = _resolve_quiz_id(quiz_id, db)
        print(f"[DEBUG] Quiz found: {quiz_data.get('title')}")
        
        questions_res = db.table("questions").select("*").eq("quiz_id", actual_quiz_id).execute()
        print(f"[DEBUG] Questions found: {len(questions_res.data) if questions_res.data else 0}")
        
        if not questions_res.data:
            print(f"[DEBUG] No questions found for this quiz")
            raise HTTPException(status_code=404, detail="Quiz has no questions")
        
        questions = questions_res.data
        for q in questions:
            q.pop("correct_answer", None)  # Hide correct answer from frontend
        
        return {
            "quiz": quiz_data,
            "questions": questions
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in get_quiz: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/quiz/code/{code}")
async def get_quiz_by_code(code: str, db=Depends(db_client)):
    """Get quiz ID by quiz code"""
    try:
        quiz_res = db.table("quizzes").select("*").eq("quiz_code", code).execute()
        if not quiz_res.data:
            raise HTTPException(status_code=404, detail="Invalid quiz code")
        return {"quiz_id": quiz_res.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quiz/create")
async def create_quiz(quiz_data: QuizCreate, db=Depends(db_admin)):
    """Create a new quiz with questions"""
    try:
        print(f"[DEBUG] Creating new quiz: {quiz_data.title}")
        quiz_code = str(uuid.uuid4())[:8].upper()
        
        quiz_insert = db.table("quizzes").insert({
            "title": quiz_data.title,
            "topic": quiz_data.topic,
            "created_by": quiz_data.created_by,
            "is_default": False,
            "quiz_code": quiz_code
        }).execute()
        
        quiz_id = quiz_insert.data[0]["id"]
        print(f"[DEBUG] Quiz created with ID: {quiz_id}, Code: {quiz_code}")
        
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
            print(f"[DEBUG] {len(questions_data)} questions inserted")
        
        return {"message": "Quiz created successfully", "quiz_code": quiz_code, "quiz_id": quiz_id}
    except Exception as e:
        print(f"[ERROR] Exception in create_quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/quiz/{quiz_id}")
async def delete_quiz(quiz_id: str, user_id: str, db=Depends(db_admin)):
    """Delete a quiz (only creator can delete)"""
    try:
        print(f"[DEBUG] Delete request for quiz: {quiz_id}, user: {user_id}")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        actual_quiz_id, quiz_data = _resolve_quiz_id(quiz_id, db)
        print(f"[DEBUG] Resolved to quiz: {quiz_data.get('title')}")
        
        # Check if the user is the creator
        creator = quiz_data.get("created_by")
        print(f"[DEBUG] Creator: {creator}, Current user: {user_id}")
        
        if creator != user_id:
            print(f"[DEBUG] User {user_id} is not the creator ({creator})")
            raise HTTPException(status_code=403, detail="Only the quiz creator can delete this quiz")
        
        # Delete all attempts for this quiz first
        print(f"[DEBUG] Deleting attempts...")
        attempts_del = db.table("attempts").delete().eq("quiz_id", actual_quiz_id).execute()
        print(f"[DEBUG] Deleted attempts")
        
        # Delete all questions for this quiz
        print(f"[DEBUG] Deleting questions...")
        questions_del = db.table("questions").delete().eq("quiz_id", actual_quiz_id).execute()
        print(f"[DEBUG] Deleted questions")
        
        # Delete the quiz
        print(f"[DEBUG] Deleting quiz...")
        quiz_del = db.table("quizzes").delete().eq("id", actual_quiz_id).execute()
        print(f"[DEBUG] Deleted quiz")
        
        print(f"[DEBUG] Quiz deleted successfully")
        return {"message": "Quiz deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in delete_quiz: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
