from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Subject(Base):
    """Subjects/Topics for tutoring"""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    difficulty_level = Column(String)  # beginner, intermediate, advanced
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    courses = relationship("Course", back_populates="subject")
    lessons = relationship("Lesson", back_populates="subject")


class Course(Base):
    """Course model"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    level = Column(String)  # beginner, intermediate, advanced
    duration_weeks = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")


class Enrollment(Base):
    """Student enrollment in courses"""
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # UUID from identity service
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    completion_date = Column(DateTime, nullable=True)
    
    # Relationships
    course = relationship("Course", back_populates="enrollments")


class Lesson(Base):
    """Individual lessons within a course"""
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    title = Column(String, index=True)
    content = Column(Text)
    video_url = Column(String, nullable=True)
    order = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    subject = relationship("Subject", back_populates="lessons")
    exercises = relationship("Exercise", back_populates="lesson")


class Exercise(Base):
    """Exercises and practice problems"""
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    question = Column(Text)
    question_type = Column(String)  # multiple_choice, short_answer, essay
    correct_answer = Column(Text)
    explanation = Column(Text)
    difficulty = Column(String)  # easy, medium, hard
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="exercises")
    responses = relationship("ExerciseResponse", back_populates="exercise")


class ExerciseResponse(Base):
    """Student responses to exercises"""
    __tablename__ = "exercise_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    user_id = Column(String, index=True)  # UUID from identity service
    student_answer = Column(Text)
    is_correct = Column(Boolean)
    score = Column(Float)
    feedback = Column(Text)
    attempted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exercise = relationship("Exercise", back_populates="responses")


class StudentProgress(Base):
    """Track student progress in courses"""
    __tablename__ = "student_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # UUID from identity service
    course_id = Column(Integer, ForeignKey("courses.id"))
    lessons_completed = Column(Integer, default=0)
    total_lessons = Column(Integer)
    exercises_completed = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    last_accessed = Column(DateTime, default=datetime.utcnow)


class Assessment(Base):
    """Assessments and quizzes"""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)  # UUID from identity service
    course_id = Column(Integer, ForeignKey("courses.id"))
    questions = Column(Text)  # JSON stored as text
    answers = Column(Text)  # JSON stored as text
    score = Column(Float)
    total_questions = Column(Integer)
    ai_feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TutorSession(Base):
    """Sessions between student and AI tutor"""
    __tablename__ = "tutor_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # UUID from identity service
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    topic = Column(String)
    messages = Column(Text)  # JSON stored as text
    duration_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
