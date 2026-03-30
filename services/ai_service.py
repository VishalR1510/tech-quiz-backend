import google.generativeai as genai
from core.config import settings
import logging

logger = logging.getLogger(__name__)

async def generate_feedback(score: int, total: int, topic: str, user_answers_eval: list) -> str:
    """
    Generate AI learning feedback based on quiz performance.
    user_answers_eval: list of dicts [{"question": "..", "user_answer": "..", "is_correct": bool}]
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not found. Returning mock AI feedback.")
        return f"Mock Feedback: You scored {score} out of {total} in {topic}. Great effort! Make sure to review the topics you missed."
        
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Try models in order of preference
        models_to_try = ['gemini-1.5-flash', 'gemini-2.5-flash', 'gemini-1.0-pro']
        model = None
        
        for model_name in models_to_try:
            try:
                print(f"[DEBUG] Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                break
            except Exception as model_err:
                print(f"[DEBUG] Model {model_name} failed: {str(model_err)[:100]}")
                continue
        
        if not model:
            logger.error("No available AI models found")
            return f"Quick Feedback: You scored {score} out of {total} in {topic}. Review the questions you missed for improvement."
        
        prompt = f"""
        You are an expert technical tutor. A student just completed a quiz on {topic}.
        They scored {score} out of {total}.
        Here is a breakdown of their performance:
        {user_answers_eval}
        
        Provide constructive educational feedback in 2-3 short readable paragraphs.
        Include:
        - Strengths
        - Weak topics based on wrong answers
        - Actionable improvement suggestions
        
        Keep it professional, encouraging, and easy to read. Avoid heavy unstructured text; make sentences clear.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[ERROR] Error generating AI feedback: {e}")
        logger.error(f"Error generating AI feedback: {e}")
        return f"Quick Feedback: You scored {score} out of {total} in {topic}. Review your performance and focus on the topics where you had difficulty."
