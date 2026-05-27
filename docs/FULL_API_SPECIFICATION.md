# Full API Specification - Elite Coach AI

This document provides a comprehensive technical reference for all API endpoints in the Elite Coach AI platform, including descriptions, request JSON, and response JSON for frontend integration.

---

## 1. Authentication & Identity (`/api/v1/auth`)

### Register User
**Method**: `POST /register`  
**Description**: Creates a new user account. Role defaults to `solo_learner`. `platform_admin` registration is prohibited via this path.  
**Request JSON**:
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "full_name": "Full Name",
  "phone": "+2348000000000",
  "role": "solo_learner"
}
```
**Response JSON (201 Created)**:
```json
{
  "access_token": "eyJhb...",
  "refresh_token": "eyJhb...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Full Name",
    "phone": "+2348000000000",
    "avatar_url": null,
    "org_id": null,
    "email_verified_at": null,
    "roles": ["solo_learner"]
  }
}
```

### Login
**Method**: `POST /login`  
**Description**: OAuth2 Password grant login. Returns access and refresh tokens.  
**Request (Form Data)**: `username=email&password=pass`  
**Response JSON (200 OK)**:
```json
{
  "access_token": "eyJhb...",
  "refresh_token": "eyJhb...",
  "token_type": "bearer",
  "user": { 
    "id": "uuid", 
    "email": "user@example.com", 
    "roles": ["solo_learner"] 
  }
}
```

### Refresh Token
**Method**: `POST /refresh`  
**Description**: Exchange a refresh token for a new access token.  
**Request JSON**:
```json
{
  "refresh_token": "eyJ..."
}
```
**Response JSON**: Same as Login Response.

### Logout
**Method**: `POST /logout`  
**Description**: Invalidate a refresh token.  
**Request JSON**:
```json
{
  "refresh_token": "eyJ..."
}
```

### Get Current User Profile
**Method**: `GET /me`  
**Description**: Retrieve the profile of the authenticated user.  
**Response JSON**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+234...",
  "avatar_url": "https://...",
  "org_id": "uuid",
  "email_verified_at": "2024-01-01T12:00:00Z",
  "roles": ["solo_learner"]
}
```

### Verify Email
**Method**: `GET /verify-email/{token}`  
**Description**: Verify user's email address using the token sent via email.  

### Forgot Password
**Method**: `POST /forgot-password`  
**Description**: Initiate password reset process.  
**Request JSON**:
```json
{
  "email": "user@example.com"
}
```

### Reset Password
**Method**: `POST /reset-password/{token}`  
**Description**: Reset password using the secret token.  
**Request JSON**:
```json
{
  "new_password": "NewStrongPassword123!"
}
```

### Social Login
**Method**: `POST /social`  
**Description**: Exchange social provider token (Google/LinkedIn) for platform JWT.  
**Request Parameters**: `provider` (query), `token` (query)  

---

## 2. Onboarding & Adaptive Paths (`/api/v1/onboarding`)

### Start Onboarding
**Method**: `POST /start`  
**Description**: Initialize profile and retrieve diagnostic questions.  
**Request JSON**:
```json
{
  "current_role": "Junior Analyst",
  "years_experience": 1,
  "career_goal": "Senior Analyst",
  "hours_per_week": 5
}
```
**Response JSON**:
```json
[
  {
    "id": "q1",
    "question_text": "How do you value a company?",
    "question_type": "multiple_choice",
    "options": ["DCF", "Comps", "LBO", "All of the above"]
  }
]
```

### Submit Diagnostics
**Method**: `POST /submit`  
**Description**: Process answers and generate the initial roadmap.  
**Request JSON**:
```json
{
  "answers": {
    "uuid-q1": "All of the above"
  }
}
```
**Response JSON**:
```json
{
  "id": "path-uuid",
  "generated_at": "2024-05-27T10:00:00Z",
  "version": 1,
  "status": "active",
  "items": [
    {
      "id": "item-uuid",
      "position": 1,
      "status": "unlocked",
      "course_id": "course-uuid",
      "course_title": "Accounting 101",
      "total_minutes": 120
    }
  ]
}
```

### Get Learning Path
**Method**: `GET /path`  
**Description**: Retrieve the current learner's adaptive roadmap.  

### Regenerate Learning Path
**Method**: `POST /path/regenerate`  
**Description**: Force recalculation of the roadmap if profile goals change.  

---

## 3. Learning Experience (`/api/v1/learning`)

### Get Course Details
**Method**: `GET /course/{course_id}`  
**Description**: Returns modular structure for the learning interface.  
**Response JSON**:
```json
{
  "id": "uuid",
  "title": "Investment Banking 101",
  "description": "Comprehensive guide...",
  "domain": "Finance",
  "difficulty": 3,
  "author_name": "Senior Partner",
  "total_lessons": 15,
  "total_minutes": 450,
  "modules": [
    {
      "id": "mod1",
      "title": "Accounting Fundamentals",
      "position": 1,
      "lesson_count": 5
    }
  ]
}
```

### Start/Resume Lesson
**Method**: `POST /lesson/{lesson_id}/start`  
**Description**: Triggered when a user clicks 'Enter Lesson'. Initializes AI Tutor session.  
**Response JSON**:
```json
{
  "session_id": "session-uuid",
  "lesson": {
    "id": "lesson-uuid",
    "title": "3 Statements",
    "position": 1,
    "estimated_minutes": 15,
    "status": "active",
    "content_blocks": [
      {
        "id": "block-uuid",
        "position": 1,
        "block_type": "text",
        "content": "Lesson markdown..."
      }
    ]
  },
  "checks_count": 2
}
```

### Mark Lesson Complete
**Method**: `POST /lesson/{lesson_id}/complete`  
**Description**: Saves progress and checks for unlocked content/assessments.  
**Response JSON**:
```json
{
  "session_id": "session-uuid",
  "completed_at": "2024-05-27T10:15:00Z",
  "next_lesson_id": "uuid",
  "module_assessment_unlocked": false,
  "final_exam_unlocked": false
}
```

### Get Active Sessions
**Method**: `GET /sessions/active`  
**Description**: List in-progress lessons for the learner's "Resume" dashboard.  

---

## 4. AI Tutor Experience (`/api/v1/ai`)

### Chat with AI
**Method**: `POST /session/{id}/message`  
**Description**: Send a message to the RAG-powered tutor within a specific session.  
**Request JSON**:
```json
{
  "message": "Explain the relationship between the 3 statements"
}
```
**Response JSON**:
```json
{
  "reply": "The Income Statement flows into...",
  "is_escalated": false
}
```

### Get Session Summary
**Method**: `GET /session/{id}/summary`  
**Description**: AI-generated summary of key learnings and areas for improvement.  
**Response JSON**:
```json
{
  "topics_covered": ["DCF", "WACC"],
  "understood_well": ["DCF Concepts"],
  "needs_revisit": ["Terminal Value Calculation"],
  "tutor_notes": "Student showed strong understanding of flows..."
}
```

### Request Manual Escalation
**Method**: `POST /session/{id}/escalate`  
**Description**: Flags the interaction for human tutor assistance.  
**Request JSON**:
```json
{
  "reason": "I am confused by the formula on slide 4."
}
```
**Response JSON**:
```json
{
  "escalation_id": "esc-uuid",
  "status": "open",
  "message": "A human tutor has been notified."
}
```

### Check Escalation Status
**Method**: `GET /session/{id}/escalation-status`  
**Description**: Check if a tutor has responded or taken over.  

### Get Knowledge Checks
**Method**: `GET /learning/lesson/{id}/checks`  
**Description**: Retrieve mini-quizzes embedded in the lesson.  

### Submit Check Response
**Method**: `POST /learning/lesson/{id}/checks/{check_id}`  
**Request JSON**:
```json
{
  "answer": "Option A"
}
```
**Response JSON**:
```json
{
  "is_correct": true,
  "explanation": "Correct because...",
  "attempts": 1,
  "re_ask": false
}
```

---

## 5. Assessments (`/api/v1/assessments`)

### Get Diagnostic Intro
**Method**: `GET /diagnostic`  
**Description**: Returns metadata and initial diagnostic questions.  

### Submit Diagnostic
**Method**: `POST /diagnostic/submit`  
**Request JSON**:
```json
{
  "answers": { "q-uuid": "Selected Option" }
}
```

### Start Assessment
**Method**: `POST /{assessment_id}/start`  
**Description**: Create a new attempt record and fetch detailed questions.  
**Response JSON**:
```json
{
  "attempt_id": "attempt-uuid",
  "assessment": {
    "id": "uuid",
    "title": "Final Exam",
    "passing_score": 75.0
  },
  "questions": [
    {
      "id": "q-uuid",
      "question_text": "Calculate the WACC...",
      "question_type": "multiple_choice",
      "options": { "a": "10%", "b": "12%" },
      "points": 5
    }
  ]
}
```

### Submit Assessment
**Method**: `POST /attempt/{attempt_id}/submit`  
**Request JSON**:
```json
{
  "answers": [
    { "question_id": "uuid", "answer": "a" }
  ]
}
```
**Response JSON**:
```json
{
  "score": 85.0,
  "is_passed": true,
  "ai_feedback": "Great focus on valuation...",
  "reinforcement_lessons": []
}
```

---

## 6. Certificates (`/api/v1/certificates`)

### List My Certificates
**Method**: `GET /me`  
**Response JSON**:
```json
[
  {
    "id": "cert-uuid",
    "course_title": "Ethics in Finance",
    "issue_date": "2024-05-27",
    "verification_url": "https://..."
  }
]
```

### Public Verification
**Method**: `GET /{verification_id}`  
**Description**: Publicly accessible URL for LinkedIn/sharing.  

### Download Certificate
**Method**: `POST /{id}/download`  
**Response JSON**:
```json
{
  "download_url": "https://s3.amazonaws.com/...",
  "expires_in_seconds": 3600
}
```

---

## 7. Tutor CMS & Content Lifecycle (`/api/v1/cms`)

### Create Course
**Method**: `POST /courses`  
**Request JSON**:
```json
{
  "title": "LBO Modeling",
  "slug": "lbo-modeling",
  "domain": "Finance",
  "difficulty": 4
}
```

### Upload RAG Data
**Method**: `POST /lessons/{id}/rag`  
**Description**: Upload proprietary text content for the AI to learn.  
**Request JSON**:
```json
{
  "content": "Full proprietary content text..."
}
```
**Response JSON**:
```json
{
  "message": "RAG content indexed successfully", "chunks": 42
}
```

### Add Lesson Block
**Method**: `POST /lessons/{id}/blocks`  
**Description**: Add dynamic content like Video URLs or Quizzes.  

### Preview Lesson
**Method**: `GET /lessons/{id}/preview`  
**Description**: See lesson as a student would before publishing.  

---

## 8. Enterprise Dashboard (`/api/v1/enterprise`)

### Register Organization
**Method**: `POST /organizations`  
**Request JSON**:
```json
{
  "name": "Goldman Sachs",
  "slug": "goldman",
  "plan": "enterprise_plus",
  "budget_ngn": 10000000.0
}
```

### Invite Employee
**Method**: `POST /invite`  
**Request JSON**:
```json
{
  "email": "analyst@goldman.com",
  "team_id": "uuid"
}
```

### Bulk Import Users
**Method**: `POST /users/import`  
**Request JSON**:
```json
[
  { "email": "a@org.com", "full_name": "A Analyst", "team_name": "Valuations" }
]
```

### Update Branding
**Method**: `PATCH /branding`  
**Request JSON**:
```json
{
  "logo_url": "https://...",
  "primary_color": "#002046",
  "secondary_color": "#ffffff"
}
```

---

## 9. Platform Administration (`/api/v1/admin`)

### List All Users
**Method**: `GET /users`  
**Description**: Global search and management of users.  

### Platform Analytics
**Method**: `GET /analytics/platform`  
**Response JSON**:
```json
{
  "active_learners_60d": 1250,
  "ai_escalation_rate": 8.5
}
```

### Toggle Feature Flag
**Method**: `POST /feature-flags/{key}`  
**Request Parameters**: `enabled` (query boolean)  

### NDPR Delete User
**Method**: `DELETE /ndpr/delete/{user_id}`  
**Description**: Irreversibly anonymize user PII.  

---

## 10. Tutor Expert Inbox (`/api/v1/inbox`)

### List Escalations
**Method**: `GET /escalations`  
**Description**: View pending student requests for my expertise.  

### Respond to Escalation
**Method**: `POST /escalations/{id}/respond`  
**Request JSON**:
```json
{
  "message": "Hi! You need to subtract net debt from equity value...",
  "close_session": true
}
```

### Push to RAG
**Method**: `POST /escalations/{id}/push-to-rag`  
**Description**: Feedback this expert interaction back into the AI model.  

---

## 11. Payments & Billing (`/api/v1/payments`)

### Initialize Subscription
**Method**: `POST /subscribe`  
**Request JSON**:
```json
{
  "plan": "monthly"
}
```
**Response JSON**:
```json
{
  "authorization_url": "https://checkout.paystack.com/...",
  "access_code": "...",
  "reference": "..."
}
```

### Check Subscription status
**Method**: `GET /status`  
**Response JSON**:
```json
{
  "status": "active",
  "active": true,
  "current_period_end": "2024-06-27T00:00:00Z",
  "plan": "monthly"
}
```

---

## 12. Notifications (`/api/v1/notifications`)

### List Notifications
**Method**: `GET /`  
**Response JSON**:
```json
[
  {
    "id": "uuid",
    "title": "New Lesson Unlocked",
    "message": "You can now start LBO basics.",
    "is_read": false,
    "created_at": "..."
  }
]
```

### Mark Read
**Method**: `POST /{id}/read`  

---

## 13. Escalations Manager (`/api/v1/escalations`)

### Update Escalation
**Method**: `PATCH /{id}`  
**Request JSON**:
```json
{
  "status": "in_progress"
}
```

---
*Note: This documentation is generated based on the latest backend deployment. For manual testing, visit the integrated Swagger UI at `/docs`.*

