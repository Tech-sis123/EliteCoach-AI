from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Subject Schemas
class SubjectCreate(BaseModel):
    name: str
    description: str
    difficulty_level: str


class SubjectResponse(SubjectCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Course Schemas
class CourseCreate(BaseModel):
    title: str
    description: str
    subject_id: int
    level: str
    duration_weeks: int


class CourseResponse(CourseCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseWithLessons(CourseResponse):
    lessons: List['LessonResponse'] = []


# Enrollment Schemas
class EnrollmentCreate(BaseModel):
    user_id: str
    course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    user_id: str
    course_id: int
    enrolled_at: datetime
    completed: bool
    
    class Config:
        from_attributes = True


# Lesson Schemas
class LessonCreate(BaseModel):
    course_id: int
    subject_id: int
    title: str
    content: str
    video_url: Optional[str] = None
    order: int


class LessonResponse(LessonCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LessonWithExercises(LessonResponse):
    exercises: List['ExerciseResponse'] = []


# Exercise Schemas
class ExerciseCreate(BaseModel):
    lesson_id: int
    question: str
    question_type: str
    correct_answer: str
    explanation: str
    difficulty: str


class ExerciseResponse(ExerciseCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Exercise Response Schemas
class ExerciseResponseCreate(BaseModel):
    exercise_id: int
    student_answer: str


class ExerciseResponseData(BaseModel):
    id: int
    exercise_id: int
    user_id: str
    student_answer: str
    is_correct: bool
    score: float
    feedback: Optional[str] = None
    attempted_at: datetime
    
    class Config:
        from_attributes = True


# Progress Schemas
class StudentProgressResponse(BaseModel):
    id: int
    user_id: str
    course_id: int
    lessons_completed: int
    total_lessons: int
    exercises_completed: int
    average_score: float
    last_accessed: datetime
    
    class Config:
        from_attributes = True


# Assessment Schemas
class AssessmentCreate(BaseModel):
    student_id: str
    course_id: int
    questions: str  # JSON as string
    answers: str  # JSON as string


class AssessmentResponse(AssessmentCreate):
    id: int
    score: float
    total_questions: int
    ai_feedback: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AssessmentSubmission(BaseModel):
    course_id: int
    questions: List[dict]
    answers: List[dict]


# AI Tutor Session Schemas
class TutorSessionCreate(BaseModel):
    user_id: str
    subject_id: int
    topic: str


class TutorSessionMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class TutorSessionResponse(TutorSessionCreate):
    id: int
    messages: Optional[str] = None
    created_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# AI Tutor Chat
class ChatMessage(BaseModel):
    content: str
    role: str = "user"


class ChatResponse(BaseModel):
    content: str
    role: str = "assistant"
    suggestions: Optional[List[str]] = None


class TutorChat(BaseModel):
    message: str
    subject_id: int
    context: Optional[str] = None


# Update Pydantic forward references
CourseWithLessons.model_rebuild()
LessonWithExercises.model_rebuild()
