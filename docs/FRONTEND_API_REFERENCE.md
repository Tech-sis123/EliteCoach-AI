# Frontend API Reference - Elite Coach AI

This document provides detailed API specifications for frontend developers, including request/response JSON examples and workflow explanations.

## 1. Authentication (`/auth`)

### Register (`POST /auth/register`)
**Purpose**: Create a new learner account.
- **Request JSON**:
```json
{
  "email": "learner@example.com",
  "password": "StrongPassword123!",
  "full_name": "John Doe",
  "role": "solo_learner"
}
```
- **Response JSON (201 Created)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "learner@example.com",
  "full_name": "John Doe"
}
```

### Login (`POST /auth/login`)
**Purpose**: Standard OAuth2 Password flow login.
- **Request (Form Data)**:
  - `username`: email@example.com
  - `password`: yourpassword
- **Response JSON (200 OK)**:
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "refresh_token": "eyJhbG..."
}
```

---

## 2. Onboarding & Diagnostics (`/onboarding`)

### Start Onboarding (`POST /onboarding/start`)
**Purpose**: Initialize the learner's profile and retrieve diagnostic questions.
- **Request JSON**:
```json
{
  "current_role": "Junior Finance Analyst",
  "years_experience": 2,
  "career_goal": "Portfolio Manager",
  "hours_per_week": 10
}
```
- **Response JSON**:
```json
[
  {
    "id": "a1b2c3d4...",
    "question_text": "How do you calculate the NPV of a project?",
    "question_type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C"]
  }
]
```

### Submit Diagnostic (`POST /onboarding/submit`)
**Purpose**: Submit answers to calculate the skill gap and generate an adaptive learning path.
- **Request JSON**:
```json
{
  "answers": {
    "a1b2c3d4...": "Option B",
    "f5g6h7i8...": "42"
  }
}
```
- **Response JSON (Learning Path)**:
```json
{
  "id": "e5f6g7h8...",
  "generated_at": "2024-01-20T12:00:00Z",
  "version": 1,
  "status": "ready",
  "items": [
    {
      "id": "item-uuid-1",
      "position": 1,
      "status": "unlocked",
      "course_id": "course-uuid-123",
      "course_title": "Fundamentals of Finance",
      "total_minutes": 120
    }
  ]
}
```

---

## 3. Learning & Courses (`/learning`, `/courses`)

### Get Learning Path (`GET /onboarding/path`)
**Purpose**: Retrieve the current roadmap of courses.
- **Response JSON**: (Same as `submit_onboarding` response)

### Start Lesson (`POST /learning/lesson/{lesson_id}/start`)
**Purpose**: Initialize a chat session with the AI Tutor for a specific lesson.
- **Response JSON**:
```json
{
  "session_id": "session-uuid-999",
  "lesson": {
    "id": "lesson-uuid-456",
    "title": "Module 1: Asset Valuation",
    "content": "Full lesson text here..."
  },
  "checks_count": 3
}
```

### Complete Lesson (`POST /learning/lesson/{lesson_id}/complete`)
**Purpose**: Finalize a lesson and check for next steps.
- **Response JSON**:
```json
{
  "session_id": "session-uuid-999",
  "completed_at": "2024-01-20T13:00:00Z",
  "next_lesson_id": "next-lesson-uuid",
  "module_assessment_unlocked": false,
  "final_exam_unlocked": false
}
```

### Get Course Detail (`GET /learning/course/{course_id}`)
**Purpose**: Get full course structure (modules and lesson counts).
- **Response JSON**:
```json
{
  "id": "course-uuid-123",
  "title": "Fundamentals of Finance",
  "description": "Introductory course...",
  "domain": "Finance",
  "difficulty": 1,
  "author_name": "Dr. Smith",
  "total_lessons": 12,
  "total_minutes": 120,
  "modules": [
    {
      "id": "mod-uuid-1",
      "title": "Introduction",
      "position": 1,
      "lesson_count": 3
    }
  ]
}
```

---

## 4. AI Tutor Experience (`/ai`)

### Send Message (`POST /ai/chat`)
**Purpose**: Send a message to the AI and get a pedagogically sound response.
- **Request JSON**:
```json
{
  "session_id": "session-uuid-999",
  "message": "I don't understand how DCF works."
}
```
- **Response JSON**:
```json
{
  "reply": "DCF stands for Discounted Cash Flow. It's used to...",
  "escalated": false,
  "rag_sources": 3
}
```

### Manual Escalation (`POST /ai/session/{id}/escalate`)
**Purpose**: Request a human tutor if the AI isn't helpful.
- **Request JSON**:
```json
{
  "reason": "The AI is stuck in a loop."
}
```
- **Response JSON**:
```json
{
  "status": "assigned",
  "escalation_id": "esc-uuid-777",
  "approximate_wait_time": "15 minutes"
}
```

---

## 5. Enterprise Management (`/enterprise`)

### Create Organization (`POST /enterprise/organizations`)
**Purpose**: Register a legal entity for enterprise training.
- **Request JSON**:
```json
{
  "name": "Global Bank Inc",
  "slug": "global-bank",
  "primary_admin_id": "user-uuid"
}
```

### Enterprise Dashboard (`GET /enterprise/dashboard`)
**Purpose**: Analytics overview for the Org Admin.
- **Response JSON**:
```json
{
  "total_employees": 150,
  "avg_progress": 0.65,
  "top_skills": ["Risk Management", "Ethics"],
  "active_subscriptions": 120
}
```

---

## 6. Tutor Inbox (`/tutor-inbox`)

### List Escalations (`GET /tutor-inbox/escalations?status=open`)
**Purpose**: For human tutors to see pending help requests.
- **Response JSON**:
```json
[
  {
    "id": "esc-uuid-777",
    "learner_id": "learner-uuid",
    "session_id": "session-uuid",
    "reason": "Need help with valuation",
    "status": "open",
    "created_at": "2024-01-20T14:30:00Z"
  }
]
```

---

## 7. Payments (`/payments`)

### Subscribe (`POST /payments/subscribe`)
**Purpose**: Initialize a payment via Paystack.
- **Request JSON**:
```json
{
  "plan": "monthly"
}
```
- **Response JSON**:
```json
{
  "authorization_url": "https://checkout.paystack.com/...",
  "access_code": "060p1dfsvw",
  "reference": "T12345678"
}
```

### Check Status (`GET /payments/status`)
**Purpose**: Confirm if the user has an active subscription.
- **Response JSON**:
```json
{
  "status": "active",
  "active": true,
  "current_period_end": "2024-02-20T00:00:00Z",
  "plan": "monthly"
}
```

---

## 9. Certificates (`/certificates`)

### List My Certificates (`GET /certificates/me`)
- **Response JSON**:
```json
[
  {
    "id": "cert-uuid",
    "course_title": "Fundamentals of Finance",
    "issued_at": "2024-01-20T15:00:00Z",
    "verification_id": "v-uuid-123",
    "pdf_url": "https://certificates.elitecoach.ai/v-uuid-123.pdf"
  }
]
```

### Download Certificate (`POST /certificates/{id}/download`)
- **Response JSON**:
```json
{
  "download_url": "https://storage.elitecoach.ai/certs/abcd.pdf",
  "expires_in_seconds": 3600
}
```
