import openai
from core.config import settings
from typing import Optional, List
import json

# Configure OpenAI
openai.api_key = settings.OPENAI_API_KEY


class AITutorService:
    """Service for AI tutoring interactions"""
    
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7
    
    async def generate_explanation(
        self,
        topic: str,
        level: str = "beginner",
        context: Optional[str] = None
    ) -> str:
        """Generate an explanation for a topic"""
        
        prompt = f"""You are an expert tutor. Explain the following topic clearly and concisely:

Topic: {topic}
Level: {level}
{f'Additional Context: {context}' if context else ''}

Provide a clear, engaging explanation suitable for a {level} level student."""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educational tutor. Provide clear, concise, and engaging explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    async def evaluate_answer(
        self,
        question: str,
        correct_answer: str,
        student_answer: str,
        question_type: str = "short_answer"
    ) -> dict:
        """Evaluate a student's answer"""
        
        prompt = f"""You are an educational AI evaluator. Please evaluate the student's answer:

Question: {question}
Correct Answer: {correct_answer}
Student Answer: {student_answer}
Question Type: {question_type}

Provide your evaluation in the following JSON format:
{{
    "is_correct": boolean,
    "score": number between 0 and 100,
    "feedback": "detailed feedback for the student",
    "explanation": "explanation of why this is right or wrong"
}}"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educational AI that evaluates student answers fairly and constructively."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            # Try to extract JSON from response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
            except:
                pass
            
            return {
                "is_correct": False,
                "score": 0,
                "feedback": response_text,
                "explanation": "Could not parse evaluation"
            }
        except Exception as e:
            return {
                "is_correct": False,
                "score": 0,
                "feedback": f"Error evaluating answer: {str(e)}",
                "explanation": ""
            }
    
    async def generate_quiz(
        self,
        topic: str,
        num_questions: int = 5,
        level: str = "beginner"
    ) -> List[dict]:
        """Generate quiz questions on a topic"""
        
        prompt = f"""Generate {num_questions} {level} level multiple-choice questions about: {topic}

Format your response as a JSON array with this structure:
[
    {{
        "question": "the question text",
        "options": ["option1", "option2", "option3", "option4"],
        "correct_answer": "the correct option",
        "explanation": "why this is correct"
    }}
]"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educator creating quality quiz questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            # Parse JSON from response
            try:
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
            except:
                pass
            
            return []
        except Exception as e:
            return []
    
    async def create_tutor_response(
        self,
        user_message: str,
        subject: str,
        conversation_history: Optional[List[dict]] = None
    ) -> dict:
        """Generate a tutor response to a student query"""
        
        system_prompt = f"""You are an expert tutor specializing in {subject}. 
Your goal is to:
1. Help students understand complex concepts
2. Ask probing questions to encourage deeper understanding
3. Provide clear explanations with examples when needed
4. Adapt your teaching style to the student's level
5. Encourage critical thinking and problem-solving

Be warm, encouraging, and patient. Use simple language when explaining complex topics."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            assistant_message = response.choices[0].message.content
            
            return {
                "success": True,
                "response": assistant_message,
                "suggestions": self._generate_follow_up_suggestions(assistant_message)
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"Error: {str(e)}",
                "suggestions": []
            }
    
    def _generate_follow_up_suggestions(self, response: str) -> List[str]:
        """Generate follow-up question suggestions based on tutor response"""
        # This is a simple implementation; could be enhanced with AI generation
        suggestions = [
            "Can you explain that differently?",
            "Can you give me an example?",
            "How do I apply this?",
            "What if I change this variable?"
        ]
        return suggestions[:3]  # Return top 3 suggestions
    
    async def generate_study_plan(
        self,
        subject: str,
        current_level: str,
        goal_level: str,
        available_weeks: int
    ) -> str:
        """Generate a personalized study plan"""
        
        prompt = f"""Create a personalized study plan with these parameters:

Subject: {subject}
Current Level: {current_level}
Goal Level: {goal_level}
Available Time: {available_weeks} weeks

Provide a week-by-week breakdown with:
- Topics to cover each week
- Recommended resources
- Practice exercises
- Assessment checkpoints"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert curriculum designer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating study plan: {str(e)}"


# Initialize the service
ai_tutor_service = AITutorService()
