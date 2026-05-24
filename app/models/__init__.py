from app.core.database import Base
from app.models.users import User, RefreshToken, UserRole
from app.models.content import Course, Module, Lesson, RagChunk
from app.models.learning import LearnerProfile, LearningPath, PathItem, Skill, SkillScore, ReinforcementTask, DiagnosticQuestion, DiagnosticAttempt
from app.models.ai_tutor import SessionStatus, LessonSession, SessionMessage, Escalation, KnowledgeCheck, KnowledgeCheckResponse
from app.models.assessments import Assessment, AssessmentQuestion, AssessmentAttempt, Certificate
from app.models.enterprise import Organization, OrgBranding, Team, OrgMembership, AdminAction
from app.models.communication import Conversation, ConversationParticipant, Message
from app.models.payments import Subscription, PaymentEvent
from app.models.analytics import Event
from app.models.notification import Notification

# This file ensures all models are registered with the Base metadata.
