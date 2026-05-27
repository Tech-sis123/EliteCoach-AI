# EliteCoach Backend System Workflow Guide

This document provides a detailed walkthrough of how the EliteCoach backend operates, covering individual API modules and the overall system architecture.

## 1. System Architecture

The backend is a high-performance, asynchronous REST API built with **FastAPI**.

-   **API Layer:** FastAPI with Pydantic v2 for strict data validation and serialization.
-   **Database Layer:** SQLAlchemy 2.0 (Async) connecting to PostgreSQL (Supabase).
-   **Concurrency:** Built entirely with `async/await` to handle high I/O loads (AI calls, DB queries).
-   **AI Integration:** Hybrid RAG (Retrieval-Augmented Generation) using Anthropic/OpenAI and Vector Search.
-   **Background Workers:** Celery with Redis/Valkey for non-blocking tasks (emails, notifications).

---

## 2. API Module Workflows

### A. Authentication & User Management (`/auth`)

1.  **Registration:**
    -   Receives `UserCreate` (email, password, role).
    -   Hashes password using `passlib` (bcrypt).
    -   Creates user in DB and returns JWT tokens immediately.
    -   Triggers background task for email verification.
2.  **Login:**
    -   Validates credentials against DB.
    -   Generates Access (15m) and Refresh (30d) tokens.
    -   Returns nested user data including assigned roles for frontend RBAC logic.

### B. Adaptive Learning & AI Tutor (`/ai`, `/learning`)

1.  **Diagnostic Assessment:**
    -   New users take a diagnostic test.
    -   `OnboardingService` calculates a "Strength/Weakness" profile.
    -   Personalized learning paths are generated based on these results.
2.  **AI Tutoring Loop:**
    -   **Context Retrieval:** When a learner asks a question, the system queries the knowledge base using vector similarity search.
    -   **Prompt Engineering:** Combines lesson content, user profile, and chat history into a system prompt.
    -   **Inference:** Streams or returns a response from the LLM (Anthropic Claude 3.5/OpenAI).
3.  **Knowledge Checks:**
    -   Tracks user progress through a lesson.
    -   Forces "Checkpoints" where the learner must answer a question before proceeding.

### C. Human-in-the-Loop Escalation (`/escalations`)

1.  **Trigger:** Can be manual (user button click) or automatic (AI detects frustration/error).
2.  **Creation:** An `Escalation` record is created, linked to the `LessonSession`.
3.  **Assignment:** Tutors are notified. The first tutor to "claim" the escalation gets assigned.
4.  **Resolution:** Once the tutor helps the user, they mark the escalation as resolved, and the session can return to AI-led instruction.

### D. Content Management System (`/cms`)

1.  **Hierarchy:** Course > Module > Lesson > ContentBlocks.
2.  **Media:** Images/Videos are uploaded to **Cloudinary** and only the URLs are stored in the DB.
3.  **Version Control:** Lessons support versioning. Updating a lesson creates a new version while preserving old session data for existing users.

### E. Payments & Subscriptions (`/payments`)

1.  **Initialization:** User requests to buy a course. Backend calls **Paystack API** to initialize a transaction.
2.  **Verification:** Uses a Webhook listener (`/payments/webhook`) to receive notifications from Paystack.
3.  **Access Grant:** Upon `charge.success`, the system creates an entry in the `user_courses` table, unlocking the content.

---

## 3. Global Orchestration

### Dependency Injection

We use FastAPI's `Depends` for:

-   `get_db`: Managing database session lifecycles.
-   `get_current_user`: Extracting and validating the user from the JWT Bearer token.
-   `RoleChecker`: Validating permissions (`platform_admin`, `enterprise_admin`, etc.).

### Middleware

-   **CORS:** Configured to allow traffic from authorized frontend domains.
-   **Logging:** `structlog` captures every request, AI response time, and database error for production monitoring.

### Error Handling

A global exception handler catches common database errors (like `UniqueViolation`) and converts them into standard HTTP 400/404/409 responses with clear error messages for the frontend.
