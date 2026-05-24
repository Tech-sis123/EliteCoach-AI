# Technical Documentation - Elite Coach AI

This document provides in-depth technical details regarding the core logic, integration patterns, and architectural decisions of the Elite Coach AI project.

## 1. AI Tutor Engine & RAG

The AI Tutor uses a Retrieval-Augmented Generation (RAG) architecture to ensure responses are grounded in course material.

### Workflow:

1. **Context Loading**: When a lesson starts, the tutor service identifies the relevant `RagChunk` entries associated with the `LessonID`.
2. **Vector Retrieval**: User queries are embedded using OpenAI's `text-embedding-3-small`.
3. **Prompt Construction**:
    - Current Lesson Content
    - Learner Progress (Skill Scores)
    - Past Conversation History (Last 20 messages)
4. **LLM Execution**: The prompt is processed by the Anthropic Claude API to generate a pedagogically sound response.
5. **Escalation Trigger**: If the AI detects high frustration or repetitive failure to understand, it automatically creates an `Escalation` record and notifies a human tutor.

## 2. Adaptive Learning Paths

Learning personalization is driven by the `OnboardingService`.

-   **Diagnostic Run**: Users take a skill-based diagnostic test.
-   **Skill Mapping**: Results are mapped to a spider-graph of skills.
-   **Path Generation**: The system selects courses from the catalog that bridge the gap between "Current Skill" and "Career Goal".
-   **Dynamic Re-shuffling**: If a user fails an assessment, the system generates "Reinforcement Tasks", potentially inserting remedial lessons into the learning path.

## 3. Payment & Subscription State Machine

We use Paystack for payment processing with a reliable webhook-first approach.

| Event                    | Action                     | New Status  |
| ------------------------ | -------------------------- | ----------- |
| `charge.success`         | Update/Create Subscription | `active`    |
| `subscription.disable`   | Mark auto-renew off        | `cancelled` |
| `invoice.payment_failed` | Notify user                | `past_due`  |

-   **Security**: Webhooks are validated using HMAC-SHA512 signatures using the Paystack Secret Key.

## 4. Database Schema Patterns

-   **BaseMixin**: All models inherit from a `BaseMixin` which provides `id` (UUID), `created_at`, and `updated_at` automatically.
-   **JSONB Usage**: Complex data like diagnostic answers, AI summaries, and audit log payloads are stored as JSONB for flexibility and performance on PostgreSQL.
-   **Soft Deletion**: For NDPR compliance, we use an `is_deleted` flag and data anonymization instead of hard-deleting record references initially.

## 5. Deployment Recommendation

-   **Containerization**: Use the provided `Dockerfile` (multi-stage build).
-   **Orchestration**: Kubernetes or AWS ECS.
-   **Caching**: Redis is recommended for API response caching and Celery task management.
-   **Vector DB**: While currently using SQL-based search for RAG chunks, migrating to `pgvector` on the same PostgreSQL instance is recommended for scale.

## 6. Audit & Logging

Every administrative action (toggling flags, deleting users, approving content) is logged in the `admin_actions` table.
System events (logins, failed attempts) are logged in the `events` table for security monitoring.
