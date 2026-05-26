# API Flow & Implementation Confirmations

This document clarifies common questions regarding the Elite Coach AI Backend API.

## 1. Onboarding Flow

-   **Flow**: background info + hours per week → diagnostic questions → generated path.
-   **Calls**: 2 API calls.
    1. `POST /onboarding/start`: Accepts `current_role`, `years_experience`, `career_goal`, AND `hours_per_week`. Returns diagnostic questions.
    2. `POST /onboarding/submit`: Accepts answers. Returns generated `LearningPath`.
-   **Note**: There is no separate "Step 3" for hours per week; it is integrated into the first call.

## 2. AI Tutor & Personalization

-   **Context Injection**: `POST /ai/session/{id}/message` automatically injects:
    -   Learner's `career_goal`
    -   `weak_skills` (skills with score < 60)
    -   Recent mistakes in the current session (failed knowledge checks)
-   **RAG**: Only answering from lesson context is enforced via system prompt.

## 3. Lesson Content & Knowledge Checks

-   **Structure**: Lessons now return `content_blocks` in `POST /learning/lesson/{id}/start`.
-   **Positioning**:
    -   `ContentBlock.position` (1-indexed) defines the order of content.
    -   `KnowledgeCheck.section_index` matches the `position` of the `ContentBlock` after which the check should appear.
-   **Idempotency**: `POST /learning/lesson/{id}/start` is idempotent for active sessions; calling it multiple times returns the same `session_id`.

## 4. Assessment & Reinforcement

-   **Failures**: Failing an assessment creates a `ReinforcementTask`.
-   **Path Updates**: `GET /learning/path` now includes a `reinforcement_tasks` array when an assessment is failed.
-   **Locking**: Assessment retakes are locked (`403 Forbidden`) until reinforcement tasks are completed.
-   **Summaries**: `POST /learning/lesson/{id}/complete` automatically triggers AI summary generation. `GET /ai/session/{id}/summary` returns the cached summary.

## 5. Escalation & Verification

-   **Status**: `GET /ai/session/{id}/escalation-status` provides real-time state (`open`, `assigned`, etc.) and `assigned_tutor` details.
-   **Public Verification**: `GET /certificates/{verification_id}` is a fully public endpoint. It should be excluded from frontend auth guards.
