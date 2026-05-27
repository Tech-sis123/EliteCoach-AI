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
## 5. Security & RBAC

The system uses a strict Role-Based Access Control (RBAC) model with 6 primary roles:
- `solo_learner`: Standard registration user.
- `org_learner`: Users associated with an Enterprise organization.
- `tutor_author`: Content creators and curriculum designers.
- `tutor_responder`: Human backup for AI escalations.
- `enterprise_admin`: Manages team subscriptions and analytics.
- `platform_admin`: Full system access.

### Administrative Hardening
- **Bootstrapping**: The first `platform_admin` MUST be created via the CLI script provided in `scripts/create_admin.py`.
- **API Isolation**: The API explicitly blocks the registration of `platform_admin` roles via any public endpoint.
- **Token Claims**: JWT tokens include a `roles` claim used by the `RoleChecker` dependency to enforce access at the route level.

## 6. Deployment Recommendation

-   **Containerization**: Use the provided `Dockerfile` (multi-stage build).
-   **Orchestration**: Kubernetes or AWS ECS.
-   **Caching**: Redis is recommended for API response caching and Celery task management.
-   **Vector DB**: While currently using SQL-based search for RAG chunks, migrating to `pgvector` on the same PostgreSQL instance is recommended for scale.

## 6. Audit & Logging

Every administrative action (toggling flags, deleting users, approving content) is logged in the `admin_actions` table.
System events (logins, failed attempts) are logged in the `events` table for security monitoring.

## 7. Administrative CLI Tools

To bootstrap the system or perform privileged operations, use the provided CLI scripts:

- **Admin Creation**: `scripts/create_admin.py` creates the first `platform_admin` without going through public API registration.
- **Documentation**: See [Admin Scripts README](scripts/README.md) for usage instructions.

## 8. Development Prerequisites (Windows)

Due to dependencies like `greenlet` and `SQLAlchemy` (Async), Windows users must ensure:
1. **Python 3.13+** is installed.
2. **Microsoft Visual C++ Redistributable** is installed (specifically the latest version of `vc_redist.x64.exe`).
3. Virtual environment initialized with `python -m venv .venv`.
