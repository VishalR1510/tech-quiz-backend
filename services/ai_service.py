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
        models_to_try = ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-1.0-pro']
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
        
        Here is a detailed breakdown of their performance, including the questions, their answers, and the correct answers:
        {user_answers_eval}
        
        Please provide a comprehensive, detailed, and constructive educational feedback. Do not give a generic 2-line response.
        Your feedback should include:
        1. An overall summary of their performance (strengths and areas for improvement).
        2. A specific analysis of the questions they answered incorrectly. For each wrong answer, explain why their answer was wrong and why the correct answer is right. Provide context or a brief explanation of the underlying concept.
        3. If they answered everything correctly, outline advanced topics they can explore next based on this quiz.
        4. Actionable recommendations on what to study next.
        
        Format the feedback clearly using human-readable paragraphs. IMPORTANT: DO NOT use any Markdown formatting. DO NOT use asterisks (*), hashes (#), dashes (-), or bold/italic markers. Output pure, plain text only. Be encouraging but deeply informative and educational.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[ERROR] Error generating AI feedback: {e}")
        logger.error(f"Error generating AI feedback: {e}")
        return f"Quick Feedback: You scored {score} out of {total} in {topic}. Review your performance and focus on the topics where you had difficulty."
