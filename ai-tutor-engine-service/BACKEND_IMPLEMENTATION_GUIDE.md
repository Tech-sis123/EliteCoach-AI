# Elite Coach AI - Backend Implementation Documentation

## Microservice Architecture Guide

**Document Version**: 1.0  
**Date**: April 2026  
**Status**: Implementation Guide for Engineering Team  
**Architecture Pattern**: Event-Driven Microservices with API Gateway

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Microservices Breakdown](#microservices-breakdown)
3. [Technology Stack & Justification](#technology-stack--justification)
4. [Service Communication Patterns](#service-communication-patterns)
5. [API Gateway Design](#api-gateway-design)
6. [Database Strategy](#database-strategy)
7. [Core Service Specifications](#core-service-specifications)
8. [API Specifications](#api-specifications)
9. [Authentication & Authorization](#authentication--authorization)
10. [Error Handling & Resilience](#error-handling--resilience)
11. [Monitoring & Observability](#monitoring--observability)
12. [Deployment Strategy](#deployment-strategy)
13. [Security Implementation](#security-implementation)
14. [Data Flow Diagrams](#data-flow-diagrams)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                  │
│         (Web, Mobile, Enterprise Admin Portal)          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │         API Gateway                │
        │  (Request routing, Auth, Logging)  │
        └────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌────────┐    ┌──────────┐    ┌──────────────┐
    │ Auth   │    │ Learning │    │ Enterprise   │
    │ Service│    │ Service  │    │ Service      │
    └────────┘    └──────────┘    └──────────────┘
        │                │                │
        ▼                ▼                ▼
    ┌────────┐    ┌──────────┐    ┌──────────────┐
    │ Course │    │ Assessment│   │ Analytics    │
    │ Service│    │ Service   │   │ Service      │
    └────────┘    └──────────┘    └──────────────┘
        │                │                │
        ▼                ▼                ▼
    ┌────────────────────────────────────────┐
    │         Message Queue (RabbitMQ)       │
    │      (Async event propagation)         │
    └────────────────────────────────────────┘
        │
        ▼
    ┌────────────┐
    │ PostgreSQL │
    │ (Primary)  │
    └────────────┘

    ┌──────────────────────────────┐
    │ Pinecone/Weaviate Vector DB  │
    │ (RAG embeddings)             │
    └──────────────────────────────┘

    ┌──────────────────────────────┐
    │ Redis Cache Layer            │
    │ (Sessions, Rate Limiting)    │
    └──────────────────────────────┘
```

### Key Architecture Principles

1. **Single Responsibility** — Each microservice owns one business capability
2. **Database Per Service** — Services maintain independent databases where appropriate
3. **Asynchronous Communication** — Event-driven via message queue for cross-service events
4. **API Gateway Pattern** — Single entry point for all client requests
5. **Circuit Breaker Pattern** — Resilience against cascading failures
6. **Service Discovery** — Dynamic service registration and location
7. **Distributed Tracing** — End-to-end request tracking across services

---

## Microservices Breakdown

Elite Coach AI's 9 core modules map to the following microservices:

### Service Inventory

| Service                  | Module                    | Responsibility                                        | Port | Priority |
| ------------------------ | ------------------------- | ----------------------------------------------------- | ---- | -------- |
| **Auth Service**         | N/A                       | User authentication, JWT, SAML SSO, MFA               | 3001 | P0       |
| **Learning Service**     | AI Tutor + Learning Paths | AI interactions, session management, personalization  | 3002 | P0       |
| **Course Service**       | CMS                       | Course management, content versioning, publishing     | 3003 | P0       |
| **Assessment Service**   | Assessments               | Quizzes, exams, scoring, certification generation     | 3004 | P0       |
| **Tutor Service**        | Human Tutor Integration   | Escalation management, tutor queues, video responses  | 3005 | P1       |
| **Enterprise Service**   | Enterprise Admin Portal   | Organization management, team management, assignments | 3006 | P0       |
| **Analytics Service**    | Analytics & Reporting     | Metrics collection, dashboards, reporting             | 3007 | P1       |
| **Notification Service** | Notification Engine       | Email, WhatsApp, SMS, push notifications              | 3008 | P1       |
| **Career Service**       | AI Career Coach           | CV analysis, mock interviews, job readiness           | 3009 | P2       |
| **Tutor Matching**       | Human Tutor Integration   | ML-based escalation routing                           | 3010 | P2       |

### Phase-Based Service Rollout

**Phase 0 (PoC) — Weeks 1-8**

-   Auth Service
-   Learning Service (AI Tutor Engine only)
-   Course Service (basic)
-   Assessment Service (basic)

**Phase 1 (MVP) — Weeks 9-24**

-   Full Auth Service (SSO/SAML)
-   Full Learning Service
-   Full Course Service
-   Full Assessment Service
-   Enterprise Service
-   Notification Service (Email + WhatsApp)
-   Tutor Service (basic escalation queue)
-   Analytics Service (basic dashboards)

**Phase 2 (Full Product) — Months 7-18**

-   Career Service
-   Tutor Matching (ML-based)
-   Advanced Analytics
-   Mentorship Service

---

## Technology Stack & Justification

### Core Components

#### **Runtime & Language**

```
Node.js + TypeScript
├── Rationale: Consistent across frontend/backend, strong async handling
├── Version: Node 20 LTS
├── Speed: Rapid development, strong npm ecosystem
└── Talent: Large pool in Nigeria and diaspora
```

#### **Framework & HTTP**

```
Express.js or Fastify
├── Express: Familiar, mature, vast middleware ecosystem
├── Fastify: Faster, JSON schema validation built-in
├── Recommendation: Start with Express MVP, migrate to Fastify in Phase 2 if performance required
└── HTTP: RestAPI primary, WebSocket for real-time AI interactions
```

#### **Database**

```
Primary (Relational):
├── PostgreSQL 15+
├── Hosted: AWS RDS or Supabase
├── RAG Vector DB: Pinecone or Weaviate (for AI embeddings)
└── Caching: Redis (session store, rate limiting, real-time leaderboards)

Per-Service Databases (Phase 2):
├── Each service owns PostgreSQL schema or dedicated database
├── Shared PostgreSQL cluster with namespace isolation initially
└── Migrate to service-specific databases when scale demands
```

#### **Message Queue**

```
RabbitMQ or AWS SQS
├── RabbitMQ: Recommended for PoC/MVP (self-hosted or managed)
├── SQS: Serverless option, better for AWS-native deployment
├── Pattern: Publish-subscribe for domain events
├── Use Case: Learner enrollment → send email, update analytics, track in learning service
```

#### **API & Contract**

```
OpenAPI 3.0 / Swagger
├── Specification: All APIs documented in OpenAPI
├── Code-gen: Generate TypeScript types from spec
├── Validation: Use OpenAPI for request/response validation
└── Portal: SwaggerUI for team reference
```

#### **API Gateway & Routing**

```
Kong API Gateway or AWS API Gateway
├── Kong: Self-hosted, comprehensive plugin ecosystem, rate limiting
├── AWS API Gateway: Managed, serverless, integrates with AWS ecosystem
├── Features: Request routing, rate limiting, auth enforcement, logging
└── Recommendation: Kong for MVP (more control), AWS API Gateway for Phase 2 (managed)
```

#### **Authentication**

```
Supabase Auth (Built-in to platform) or Firebase Auth
├── JWT tokens (signed, expiry 8 hours)
├── Refresh tokens (stored in secure HTTP-only cookies, 30 days)
├── SAML 2.0 for enterprise SSO
├── MFA via TOTP (Google Authenticator)
└── Social login (Google, LinkedIn for B2C)
```

#### **CI/CD**

```
GitHub Actions (free tier, integrates with GitHub)
├── Trigger: Push to develop/main branches
├── Pipeline: Lint → Test → Build → Deploy to staging → Smoke tests
└── Secrets: Environment variables managed via GitHub secrets
```

#### **Container Orchestration**

```
Docker + Kubernetes (Phase 1) or Docker + AWS ECS (Phase 1)
├── MVP: Docker Compose locally, single-server deployment with Docker
├── Phase 1: Kubernetes (EKS on AWS) or AWS ECS
├── Each service: Containerized independently
└── Registry: Amazon ECR (Elastic Container Registry)
```

#### **Monitoring & Logging**

```
ELK Stack or Datadog
├── Elasticsearch: Centralized log aggregation
├── Logstash: Log parsing and transformation
├── Kibana: Log visualization and dashboards
├── Alternative: Datadog (managed, better UI but higher cost)
├── Application Metrics: Prometheus + Grafana or Datadog APM
└── Distributed Tracing: Jaeger or NewRelic
```

### Dependency Management

```json
{
    "dependencies": {
        "express": "^4.18.2",
        "typescript": "^5.2.0",
        "@types/node": "^20.0.0",
        "dotenv": "^16.0.0",
        "joi": "^17.9.0",
        "axios": "^1.4.0",
        "pg": "^8.11.0",
        "redis": "^4.6.0",
        "amqplib": "^0.10.3",
        "jsonwebtoken": "^9.0.0",
        "@supabase/supabase-js": "^2.30.0",
        "winston": "^3.10.0",
        "pino": "^8.15.0",
        "openai": "^4.12.0",
        "pinecone-client": "^2.2.0",
        "nodemailer": "^6.9.0"
    },
    "devDependencies": {
        "jest": "^29.6.0",
        "@types/jest": "^29.5.0",
        "ts-jest": "^29.1.0",
        "eslint": "^8.46.0",
        "@typescript-eslint/eslint-plugin": "^6.2.0",
        "@typescript-eslint/parser": "^6.2.0",
        "supertest": "^6.3.0"
    }
}
```

---

## Service Communication Patterns

### 1. Synchronous Communication (REST/gRPC)

**When to Use:**

-   User-facing operations requiring immediate responses
-   Operations that need strong consistency
-   Simple request-response patterns

**Pattern: Service-to-Service HTTP**

```typescript
// In Learning Service calling Course Service
async function fetchCourseDetails(courseId: string) {
    try {
        const response = await axios.get(
            `http://course-service:3003/api/v1/courses/${courseId}`,
            {
                headers: { Authorization: `Bearer ${getServiceToken()}` },
                timeout: 5000, // 5 second timeout
            }
        );
        return response.data;
    } catch (error) {
        // Circuit breaker logic here
        throw new ServiceUnavailableError(
            "Course Service temporarily unavailable"
        );
    }
}
```

**Circuit Breaker Implementation:**

```typescript
import CircuitBreaker from "opossum";

const courseServiceBreaker = new CircuitBreaker(
    async (courseId) => {
        return await fetchCourseDetails(courseId);
    },
    {
        timeout: 5000, // 5 seconds
        errorThresholdPercentage: 50, // Open after 50% error rate
        resetTimeout: 30000, // Attempt recovery after 30 seconds
    }
);
```

### 2. Asynchronous Communication (Event-Driven)

**When to Use:**

-   Side effects (sending emails, updating analytics)
-   Non-blocking operations
-   Events that multiple services need to react to

**Pattern: Publish-Subscribe via RabbitMQ**

**Example: Course Completion Event**

```typescript
// Learning Service publishes event
import amqp from "amqplib";

const channel = await connection.createChannel();

await channel.publish(
    "elite-coach-events",
    "learner.course.completed",
    Buffer.from(
        JSON.stringify({
            event: "COURSE_COMPLETED",
            learnerId: "user-123",
            courseId: "course-456",
            score: 85,
            completedAt: new Date().toISOString(),
            timestamp: Date.now(),
        })
    )
);
```

**Multiple Services Subscribe and React:**

```typescript
// Notification Service
channel.assertQueue("notification-queue", { durable: true });
channel.bindQueue(
    "notification-queue",
    "elite-coach-events",
    "learner.course.completed"
);
channel.consume("notification-queue", async (msg) => {
    const event = JSON.parse(msg.content.toString());
    await sendCourseCompletionEmail(event.learnerId, event.courseId);
    channel.ack(msg);
});

// Analytics Service
channel.assertQueue("analytics-queue", { durable: true });
channel.bindQueue(
    "analytics-queue",
    "elite-coach-events",
    "learner.course.completed"
);
channel.consume("analytics-queue", async (msg) => {
    const event = JSON.parse(msg.content.toString());
    await updateLearnerMetrics(event.learnerId, event.score);
    channel.ack(msg);
});

// Certificate Service (part of Assessment Service)
channel.assertQueue("cert-queue", { durable: true });
channel.bindQueue(
    "cert-queue",
    "elite-coach-events",
    "learner.course.completed"
);
channel.consume("cert-queue", async (msg) => {
    const event = JSON.parse(msg.content.toString());
    if (event.score >= 70) {
        await generateCertificate(event.learnerId, event.courseId);
    }
    channel.ack(msg);
});
```

**Event Taxonomy:**

```
Domain Events (across all services):
├── Learner Events
│   ├── learner.created
│   ├── learner.enrolled
│   ├── learner.session.started
│   ├── learner.session.completed
│   └── learner.course.completed
├── Course Events
│   ├── course.created
│   ├── course.published
│   ├── course.updated
│   └── course.archived
├── Assessment Events
│   ├── assessment.submitted
│   ├── assessment.graded
│   └── certificate.generated
├── Organization Events
│   ├── organization.created
│   ├── team.assigned
│   └── deadline.approaching
├── Tutor Events
│   ├── escalation.triggered
│   ├── tutor.response.submitted
│   └── session.resolved
└── Analytics Events
    ├── metric.recorded
    ├── dashboard.updated
    └── report.generated
```

### 3. Data Consistency Patterns

**Saga Pattern for Distributed Transactions:**

Example: Learner Enrollment (involves multiple services)

```typescript
// Orchestrator Pattern (managed by Learning Service)

async function enrollLearner(learnerId: string, courseId: string) {
    try {
        // Step 1: Check course availability (Course Service)
        const course = await courseService.getCourse(courseId);
        if (!course.published) throw new Error("Course not available");

        // Step 2: Create enrollment record (Learning Service)
        const enrollment = await createEnrollmentRecord(learnerId, courseId);

        // Step 3: Generate personalized learning path (Learning Service)
        const learnerProfile = await getLearnerProfile(learnerId);
        const path = await generateLearningPath(learnerProfile, courseId);

        // Step 4: Publish event for other services
        await eventBus.publish("learner.enrolled", {
            learnerId,
            courseId,
            enrollmentId: enrollment.id,
            learnerProfile,
            path,
        });

        // Step 5: Notify via async channels
        // (handled by event subscribers)

        return enrollment;
    } catch (error) {
        // Compensating transaction: rollback enrollment
        await deleteEnrollmentRecord(learnerId, courseId);
        throw error;
    }
}
```

---

## API Gateway Design

### Gateway Responsibilities

```
┌──────────────────────────────────────────┐
│         API Gateway (Kong/AWS)           │
├──────────────────────────────────────────┤
│ ✓ Request routing to appropriate service │
│ ✓ Authentication & authorization         │
│ ✓ Rate limiting per user/client          │
│ ✓ Request logging & auditing             │
│ ✓ API versioning management              │
│ ✓ Response transformation                │
│ ✓ CORS handling                          │
│ ✓ Load balancing                         │
│ ✓ SSL/TLS termination                    │
└──────────────────────────────────────────┘
```

### Kong Configuration (docker-compose)

```yaml
version: "3.8"
services:
    postgres:
        image: postgres:15
        environment:
            POSTGRES_DB: kong
            POSTGRES_USER: kong
            POSTGRES_PASSWORD: kong
        ports:
            - "5432:5432"
        volumes:
            - kong_data:/var/lib/postgresql/data

    kong:
        image: kong:3.3-alpine
        environment:
            KONG_DATABASE: postgres
            KONG_PG_HOST: postgres
            KONG_PG_USER: kong
            KONG_PG_PASSWORD: kong
        ports:
            - "8000:8000" # Proxy port
            - "8001:8001" # Admin API
        depends_on:
            - postgres
        command: kong start

    konga:
        image: pantsel/konga:latest
        ports:
            - "1337:1337"
        environment:
            NODE_ENV: production
            DB_ADAPTER: postgres
        depends_on:
            - postgres
```

### Gateway Route Configuration

```javascript
// Routes defined via Kong Admin API or declaratively

const routes = [
    // Auth Service routes
    {
        route: "/api/v1/auth/login",
        methods: ["POST"],
        upstream_url: "http://auth-service:3001/login",
        plugins: ["rate-limiting"],
    },
    {
        route: "/api/v1/auth/refresh",
        methods: ["POST"],
        upstream_url: "http://auth-service:3001/refresh",
        plugins: ["rate-limiting"],
    },

    // Learning Service routes
    {
        route: "/api/v1/learning/sessions",
        methods: ["POST", "GET"],
        upstream_url: "http://learning-service:3002/sessions",
        plugins: ["jwt", "rate-limiting"],
    },
    {
        route: "/api/v1/learning/sessions/:sessionId",
        methods: ["GET"],
        upstream_url: "http://learning-service:3002/sessions",
        plugins: ["jwt", "rate-limiting"],
    },

    // Course Service routes
    {
        route: "/api/v1/courses",
        methods: ["GET"],
        upstream_url: "http://course-service:3003/courses",
        plugins: ["rate-limiting"],
    },
    {
        route: "/api/v1/courses",
        methods: ["POST"],
        upstream_url: "http://course-service:3003/courses",
        plugins: ["jwt", "admin-only", "rate-limiting"],
    },

    // Enterprise Service routes
    {
        route: "/api/v1/organizations",
        methods: ["GET", "POST"],
        upstream_url: "http://enterprise-service:3006/organizations",
        plugins: ["jwt", "rate-limiting"],
    },

    // Assessment Service routes
    {
        route: "/api/v1/assessments/submit",
        methods: ["POST"],
        upstream_url: "http://assessment-service:3004/submit",
        plugins: ["jwt", "rate-limiting"],
    },
];
```

---

## Database Strategy

### Database Architecture

```
┌──────────────────────────────────────────┐
│   PostgreSQL Primary (Shared initially)  │
├──────────────────────────────────────────┤
│ Schema: auth                             │
│ Schema: learning                         │
│ Schema: courses                          │
│ Schema: assessments                      │
│ Schema: organizations                    │
│ Schema: notifications                    │
│ Schema: analytics                        │
└──────────────────────────────────────────┘

Phase 2 Migration:
├── auth_service_db
├── learning_service_db
├── course_service_db
├── assessment_service_db
├── enterprise_service_db
├── analytics_service_db
└── notification_service_db
```

### Shared Database Schema (MVP)

```sql
-- Auth Schema
CREATE SCHEMA auth;

CREATE TABLE auth.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  salt VARCHAR(255) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  phone_number VARCHAR(20),
  user_type ENUM('learner', 'tutor', 'org_admin', 'super_admin') NOT NULL,
  organization_id UUID,
  status ENUM('active', 'suspended', 'deleted') DEFAULT 'active',
  email_verified BOOLEAN DEFAULT FALSE,
  mfa_enabled BOOLEAN DEFAULT FALSE,
  mfa_secret VARCHAR(255),
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (organization_id) REFERENCES organizations.orgs(id)
);

CREATE TABLE auth.sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  token_id VARCHAR(255) UNIQUE NOT NULL,
  refresh_token VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  device_info JSONB,
  ip_address INET,
  FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Learning Schema
CREATE SCHEMA learning;

CREATE TABLE learning.learners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
  current_skill_level JSONB,
  learning_style VARCHAR(50),
  preferred_language VARCHAR(10) DEFAULT 'en',
  time_available_per_week INTEGER, -- minutes
  career_goal VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE learning.enrollments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learner_id UUID NOT NULL REFERENCES learning.learners(id),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  enrolled_at TIMESTAMP DEFAULT NOW(),
  deadline TIMESTAMP,
  progress_percentage INTEGER DEFAULT 0,
  status ENUM('active', 'completed', 'dropped') DEFAULT 'active',
  last_accessed_at TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  final_score DECIMAL(5,2),
  certificate_id UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(learner_id, course_id)
);

CREATE TABLE learning.learning_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learner_id UUID NOT NULL REFERENCES learning.learners(id),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  module_id UUID,
  session_type ENUM('ai_tutor', 'human_tutor', 'practice', 'assessment'),
  started_at TIMESTAMP DEFAULT NOW(),
  ended_at TIMESTAMP,
  duration_minutes INTEGER,
  ai_model_used VARCHAR(50),
  escalated BOOLEAN DEFAULT FALSE,
  escalation_reason VARCHAR(500),
  tutor_id UUID REFERENCES auth.users(id),
  learner_messages_count INTEGER DEFAULT 0,
  ai_responses_count INTEGER DEFAULT 0,
  session_transcript JSONB,
  feedback JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (course_id) REFERENCES courses.courses(id)
);

CREATE TABLE learning.learning_paths (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learner_id UUID NOT NULL REFERENCES learning.learners(id),
  current_skill_profile JSONB NOT NULL,
  target_role VARCHAR(255),
  target_skill_profile JSONB NOT NULL,
  recommended_courses JSONB NOT NULL, -- Array of course IDs in sequence
  estimated_completion_weeks INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(learner_id)
);

-- Course Schema
CREATE SCHEMA courses;

CREATE TABLE courses.courses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  domain VARCHAR(100),
  difficulty_level ENUM('beginner', 'intermediate', 'advanced'),
  duration_hours DECIMAL(10,2),
  creator_id UUID NOT NULL REFERENCES auth.users(id),
  organization_id UUID,
  status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
  thumbnail_url VARCHAR(500),
  skills_covered JSONB,
  prerequisites JSONB, -- Array of course IDs
  version_number INTEGER DEFAULT 1,
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (organization_id) REFERENCES organizations.orgs(id)
);

CREATE TABLE courses.modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  title VARCHAR(255) NOT NULL,
  sequence_order INTEGER NOT NULL,
  description TEXT,
  duration_minutes INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE courses.lessons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id UUID NOT NULL REFERENCES courses.modules(id),
  title VARCHAR(255) NOT NULL,
  sequence_order INTEGER NOT NULL,
  content_type ENUM('text', 'video', 'interactive', 'exercise'),
  content_data JSONB,
  video_url VARCHAR(500),
  duration_minutes INTEGER,
  learning_objectives JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE courses.content_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  lesson_id UUID REFERENCES courses.lessons(id),
  chunk_type VARCHAR(50),
  content TEXT NOT NULL,
  embedding_vector VECTOR(1536), -- OpenAI embedding dimension
  token_count INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (course_id) REFERENCES courses.courses(id)
);

-- Assessments Schema
CREATE SCHEMA assessments;

CREATE TABLE assessments.assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  title VARCHAR(255) NOT NULL,
  assessment_type ENUM('quiz', 'module_test', 'final_exam', 'practical'),
  passing_score DECIMAL(5,2) DEFAULT 70,
  total_questions INTEGER,
  duration_minutes INTEGER,
  is_proctored BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (course_id) REFERENCES courses.courses(id)
);

CREATE TABLE assessments.questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments.assessments(id),
  question_type ENUM('multiple_choice', 'short_answer', 'essay', 'code'),
  question_text TEXT NOT NULL,
  options JSONB,
  correct_answer JSONB,
  explanation TEXT,
  difficulty ENUM('easy', 'medium', 'hard'),
  sequence_order INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (assessment_id) REFERENCES assessments.assessments(id)
);

CREATE TABLE assessments.submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments.assessments(id),
  learner_id UUID NOT NULL REFERENCES learning.learners(id),
  started_at TIMESTAMP DEFAULT NOW(),
  submitted_at TIMESTAMP,
  score DECIMAL(5,2),
  passed BOOLEAN,
  answers JSONB, -- Learner's answers
  time_taken_seconds INTEGER,
  proctoring_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (assessment_id) REFERENCES assessments.assessments(id)
);

CREATE TABLE assessments.certificates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  enrollment_id UUID NOT NULL REFERENCES learning.enrollments(id),
  learner_id UUID NOT NULL REFERENCES learning.learners(id),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  verification_code VARCHAR(50) UNIQUE NOT NULL,
  pdf_url VARCHAR(500),
  issued_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (learner_id) REFERENCES learning.learners(id),
  FOREIGN KEY (course_id) REFERENCES courses.courses(id)
);

-- Organizations Schema
CREATE SCHEMA organizations;

CREATE TABLE organizations.orgs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL UNIQUE,
  industry VARCHAR(100),
  country VARCHAR(100),
  website VARCHAR(500),
  logo_url VARCHAR(500),
  plan_tier ENUM('starter', 'growth', 'enterprise', 'institutional') DEFAULT 'starter',
  max_learners INTEGER,
  admin_user_id UUID NOT NULL REFERENCES auth.users(id),
  ndpr_dpa_signed BOOLEAN DEFAULT FALSE,
  dpa_signed_date TIMESTAMP,
  data_residency_country VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE organizations.teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations.orgs(id),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE organizations.course_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations.orgs(id),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  team_id UUID REFERENCES organizations.teams(id),
  assigned_learners JSONB, -- Array of user IDs
  deadline TIMESTAMP,
  assignment_date TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (organization_id) REFERENCES organizations.orgs(id),
  FOREIGN KEY (course_id) REFERENCES courses.courses(id)
);

-- Tutors Schema
CREATE SCHEMA tutoring;

CREATE TABLE tutoring.tutors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
  expertise_areas JSONB NOT NULL,
  bio TEXT,
  credentials JSONB,
  verification_status ENUM('unverified', 'verified', 'super_verified'),
  hourly_rate DECIMAL(10,2),
  availability_schedule JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tutoring.escalations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES learning.learning_sessions(id),
  learner_id UUID NOT NULL REFERENCES learning.learners(id),
  escalation_reason VARCHAR(500),
  assigned_tutor_id UUID REFERENCES tutoring.tutors(id),
  status ENUM('pending', 'assigned', 'in_progress', 'resolved') DEFAULT 'pending',
  escalated_at TIMESTAMP DEFAULT NOW(),
  resolved_at TIMESTAMP,
  tutor_response JSONB,
  resolution_notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (learner_id) REFERENCES learning.learners(id)
);

-- Analytics Schema
CREATE SCHEMA analytics;

CREATE TABLE analytics.learner_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learner_id UUID NOT NULL REFERENCES learning.learners(id),
  metric_date DATE DEFAULT CURRENT_DATE,
  courses_completed INTEGER DEFAULT 0,
  total_hours_learned DECIMAL(10,2) DEFAULT 0,
  average_assessment_score DECIMAL(5,2),
  streak_days INTEGER DEFAULT 0,
  ai_escalation_rate DECIMAL(5,2),
  engagement_score DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(learner_id, metric_date)
);

CREATE TABLE analytics.course_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id UUID NOT NULL REFERENCES courses.courses(id),
  metric_date DATE DEFAULT CURRENT_DATE,
  total_enrollments INTEGER DEFAULT 0,
  completions INTEGER DEFAULT 0,
  completion_rate DECIMAL(5,2),
  average_score DECIMAL(5,2),
  average_time_to_completion_hours DECIMAL(10,2),
  dropout_rate DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(course_id, metric_date)
);

-- Notifications Schema
CREATE SCHEMA notifications;

CREATE TABLE notifications.notification_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
  email_enabled BOOLEAN DEFAULT TRUE,
  whatsapp_enabled BOOLEAN DEFAULT TRUE,
  sms_enabled BOOLEAN DEFAULT FALSE,
  push_enabled BOOLEAN DEFAULT FALSE,
  prefer_language VARCHAR(10) DEFAULT 'en',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notifications.notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  notification_type VARCHAR(100),
  title VARCHAR(255),
  body TEXT,
  channel ENUM('email', 'whatsapp', 'sms', 'push'),
  status ENUM('pending', 'sent', 'failed', 'delivered'),
  sent_at TIMESTAMP,
  delivery_metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Create indices for performance
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX idx_enrollments_learner_course ON learning.enrollments(learner_id, course_id);
CREATE INDEX idx_sessions_learner_course ON learning.learning_sessions(learner_id, course_id);
CREATE INDEX idx_courses_domain ON courses.courses(domain);
CREATE INDEX idx_submissions_learner ON assessments.submissions(learner_id);
CREATE INDEX idx_escalations_status ON tutoring.escalations(status);
CREATE INDEX idx_metrics_date ON analytics.learner_metrics(metric_date);
```

### Caching Strategy (Redis)

```typescript
// Redis cache layer for performance
import Redis from "redis";

const redis = Redis.createClient({
    host: process.env.REDIS_HOST,
    port: process.env.REDIS_PORT,
});

// Cache Patterns

// 1. Session/Learner Profile Cache
const LEARNER_PROFILE_KEY = "learner:{learnerId}:profile";
const CACHE_TTL_PROFILE = 3600; // 1 hour

async function getLearnerProfile(learnerId: string) {
    // Try cache first
    const cached = await redis.get(
        LEARNER_PROFILE_KEY.replace("{learnerId}", learnerId)
    );
    if (cached) return JSON.parse(cached);

    // Miss: fetch from DB
    const profile = await db.query(
        "SELECT * FROM learning.learners WHERE id = $1",
        [learnerId]
    );

    // Store in cache
    await redis.setex(
        LEARNER_PROFILE_KEY.replace("{learnerId}", learnerId),
        CACHE_TTL_PROFILE,
        JSON.stringify(profile.rows[0])
    );

    return profile.rows[0];
}

// 2. Course Content Cache (rarely changes, long TTL)
const COURSE_CONTENT_KEY = "course:{courseId}:content:v{version}";
const CACHE_TTL_COURSE = 86400; // 1 day

// 3. Rate Limiting (sliding window)
const RATE_LIMIT_KEY = "rate_limit:{userId}:{endpoint}";
const RATE_LIMIT_WINDOW = 60; // 1 minute
const RATE_LIMIT_MAX_REQUESTS = 100;

async function checkRateLimit(
    userId: string,
    endpoint: string
): Promise<boolean> {
    const key = RATE_LIMIT_KEY.replace("{userId}", userId).replace(
        "{endpoint}",
        endpoint
    );
    const count = await redis.incr(key);

    if (count === 1) {
        // First request in window, set expiry
        await redis.expire(key, RATE_LIMIT_WINDOW);
    }

    return count <= RATE_LIMIT_MAX_REQUESTS;
}

// 4. Session Cache (temporary, fast access)
const SESSION_KEY = "session:{sessionId}";
const CACHE_TTL_SESSION = 3600; // 1 hour

// 5. Leaderboard Cache (frequently updated, real-time)
const LEADERBOARD_KEY = "leaderboard:{courseId}:week";
const CACHE_TTL_LEADERBOARD = 3600; // 1 hour
```

---

## Core Service Specifications

### 1. Auth Service

**Responsibility:** User authentication, authorization, session management

**Endpoints:**

```typescript
// POST /api/v1/auth/register
// - Create new user account
// - Validate email uniqueness
// - Generate JWT + refresh token
// - Send verification email
Request: {
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  userType: 'learner' | 'tutor' | 'org_admin'
}
Response: {
  userId: UUID,
  token: JWT,
  refreshToken: string,
  expiresIn: number
}

// POST /api/v1/auth/login
// - Verify credentials
// - Generate JWT + refresh token
// - Log session
Request: {
  email: string,
  password: string,
  rememberMe?: boolean
}
Response: {
  userId: UUID,
  token: JWT,
  refreshToken: string,
  expiresIn: number,
  user: UserObject
}

// POST /api/v1/auth/refresh
// - Verify refresh token
// - Generate new JWT
Request: {
  refreshToken: string
}
Response: {
  token: JWT,
  expiresIn: number
}

// POST /api/v1/auth/logout
// - Invalidate refresh token
// - Clear session
Request: {
  sessionId: UUID
}
Response: {
  success: boolean
}

// POST /api/v1/auth/mfa/enable
// - Generate TOTP secret
// - Return QR code
Request: {}
Response: {
  secret: string,
  qrCode: string
}

// POST /api/v1/auth/mfa/verify
// - Verify TOTP code
// - Enable MFA
Request: {
  code: 6-digit-string,
  secret: string
}
Response: {
  success: boolean,
  backupcodes: string[]
}

// POST /api/v1/auth/sso/saml
// - SAML 2.0 SSO endpoint for enterprise
// - Process SAML assertion
// - Auto-create/link user
Request: {
  samlAssertion: XML
}
Response: {
  token: JWT,
  redirectUrl: string
}
```

**Key Implementation Details:**

```typescript
// Password hashing (bcrypt)
import bcrypt from "bcrypt";

async function hashPassword(password: string): Promise<string> {
    const salt = await bcrypt.genSalt(12);
    return bcrypt.hash(password, salt);
}

async function verifyPassword(
    password: string,
    hash: string
): Promise<boolean> {
    return bcrypt.compare(password, hash);
}

// JWT generation
import jwt from "jsonwebtoken";

function generateTokens(userId: string, role: string) {
    const accessToken = jwt.sign(
        { userId, role, type: "access" },
        process.env.JWT_SECRET,
        { expiresIn: "8h" }
    );

    const refreshToken = jwt.sign(
        { userId, type: "refresh" },
        process.env.JWT_REFRESH_SECRET,
        { expiresIn: "30d" }
    );

    return { accessToken, refreshToken };
}

// Token verification middleware
function authenticateToken(req, res, next) {
    const authHeader = req.headers["authorization"];
    const token = authHeader && authHeader.split(" ")[1];

    if (!token) return res.sendStatus(401);

    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
}
```

---

### 2. Learning Service (Core AI Tutor Engine)

**Responsibility:** AI tutor interactions, session management, personalized learning paths, RAG pipeline

**Endpoints:**

```typescript
// POST /api/v1/learning/sessions/start
// - Create new learning session
// - Initialize RAG pipeline with course content
// - Return initial AI greeting
Request: {
  learnerId: UUID,
  courseId: UUID,
  moduleId?: UUID
}
Response: {
  sessionId: UUID,
  aiGreeting: string,
  currentModule: ModuleObject,
  userProgress: {
    completionPercentage: number,
    assessmentScores: object
  }
}

// POST /api/v1/learning/sessions/:sessionId/message
// - Process learner message
// - Run RAG retrieval
// - Generate AI response
// - Check escalation conditions
// - Store transcript
Request: {
  message: string,
  messageType: 'question' | 'answer' | 'feedback'
}
Response: {
  sessionId: UUID,
  aiResponse: string,
  responseMetadata: {
    relevantChunks: number,
    confidenceScore: number,
    modelUsed: string
  },
  escalated?: {
    reason: string,
    ticket: UUID
  }
}

// GET /api/v1/learning/sessions/:sessionId
// - Retrieve session transcript and context
Response: {
  sessionId: UUID,
  learnerId: UUID,
  courseId: UUID,
  transcript: Message[],
  duration: number,
  escalated: boolean,
  feedback: object
}

// POST /api/v1/learning/sessions/:sessionId/end
// - End learning session
// - Generate session summary
// - Publish event
// - Update learner profile
Request: {
  feedback?: string,
  difficulty?: 1-5
}
Response: {
  sessionId: UUID,
  summary: {
    topicsLearned: string[],
    questionsAsked: number,
    correctAnswers: number,
    suggestedNextSteps: string[]
  }
}

// POST /api/v1/learning/paths/generate
// - Generate personalized learning path
// - Use skill taxonomy
// - Consider time availability
Request: {
  learnerId: UUID,
  targetRole: string,
  timePerWeek: number,
  currentSkills: object
}
Response: {
  pathId: UUID,
  recommendedCourses: CourseObject[],
  estimatedWeeks: number,
  skillGaps: string[],
  nextCourseToStart: CourseObject
}

// GET /api/v1/learning/paths/:learnerId
// - Retrieve current learning path
Response: {
  pathId: UUID,
  learnerId: UUID,
  targetRole: string,
  progress: number,
  completedCourses: CourseObject[],
  nextSteps: CourseObject[],
  estimatedCompletion: DateTime
}
```

**RAG Pipeline Implementation:**

```typescript
import { OpenAIEmbeddings } from "langchain/embeddings/openai";
import { Pinecone } from "@pinecone-database/pinecone";
import { ChatOpenAI } from "langchain/chat_models/openai";
import { PromptTemplate } from "langchain/prompts";

class RAGTutorEngine {
    private embeddings: OpenAIEmbeddings;
    private vectorDb: Pinecone;
    private model: ChatOpenAI;

    constructor() {
        this.embeddings = new OpenAIEmbeddings({
            openAIApiKey: process.env.OPENAI_API_KEY,
        });

        this.vectorDb = new Pinecone({
            apiKey: process.env.PINECONE_API_KEY,
            environment: process.env.PINECONE_ENV,
        });

        this.model = new ChatOpenAI({
            modelName: "gpt-4o",
            temperature: 0.7,
            maxTokens: 1000,
        });
    }

    async generateResponse(
        learnerId: string,
        courseId: string,
        learnerMessage: string,
        conversationHistory: Message[]
    ): Promise<AIResponse> {
        try {
            // Step 1: Embed the learner's question
            const messageEmbedding = await this.embeddings.embedQuery(
                learnerMessage
            );

            // Step 2: Retrieve relevant content chunks
            const index = this.vectorDb.Index(`course-${courseId}`);
            const retrievalResults = await index.query({
                vector: messageEmbedding,
                topK: 5,
                includeMetadata: true,
            });

            const relevantChunks = retrievalResults.matches.map((match) => ({
                text: match.metadata.text,
                score: match.score,
                source: match.metadata.source,
            }));

            // Step 3: Build prompt with context
            const systemPrompt = `You are Elite Coach AI, an expert tutor helping learners master professional skills.

Course Name: ${await this.getCourseTitle(courseId)}

Guidelines:
- Answer ONLY based on the provided course content below
- If you cannot answer from the content, say "I don't have that information in this course"
- Provide clear, concise explanations suitable for professionals
- Give practical examples when relevant
- If learner seems frustrated or is asking the same question 3+ times, suggest escalation to a human tutor

Course Content:
${relevantChunks
    .map(
        (chunk) =>
            `- ${chunk.text} (confidence: ${(chunk.score * 100).toFixed(1)}%)`
    )
    .join("\n")}
`;

            const conversationContext = conversationHistory
                .slice(-5) // Last 5 messages for context
                .map((msg) => `${msg.role}: ${msg.content}`)
                .join("\n");

            // Step 4: Call LLM
            const response = await this.model.predictMessages([
                {
                    role: "system",
                    content: systemPrompt,
                },
                {
                    role: "user",
                    content: `${conversationContext}\n\nLearner: ${learnerMessage}`,
                },
            ]);

            // Step 5: Check for escalation triggers
            const isEscalationNeeded = this.checkEscalationTriggers(
                learnerId,
                learnerMessage,
                conversationHistory,
                relevantChunks
            );

            return {
                response: response.content,
                relevantChunksCount: relevantChunks.length,
                averageConfidence:
                    relevantChunks.reduce((a, b) => a + b.score, 0) /
                    relevantChunks.length,
                escalationNeeded: isEscalationNeeded,
                modelUsed: "gpt-4o",
                costTokens: response.usage?.totalTokens || 0,
            };
        } catch (error) {
            console.error("RAG pipeline error:", error);
            throw new Error("Failed to generate AI response");
        }
    }

    private checkEscalationTriggers(
        learnerId: string,
        currentMessage: string,
        history: Message[],
        retrievedChunks: any[]
    ): boolean {
        // Trigger 1: Average relevance too low
        const avgRelevance =
            retrievedChunks.reduce((a, b) => a + b.score, 0) /
            retrievedChunks.length;
        if (avgRelevance < 0.6) return true;

        // Trigger 2: Same question repeated 3+ times
        const lastQuestion = currentMessage.toLowerCase();
        const similarQuestions = history
            .filter((msg) => msg.role === "learner")
            .slice(-3)
            .filter(
                (msg) =>
                    this.similarityScore(
                        msg.content.toLowerCase(),
                        lastQuestion
                    ) > 0.8
            );
        if (similarQuestions.length >= 3) return true;

        // Trigger 3: Frustration detected
        const frustrationKeywords = [
            "confused",
            "don't understand",
            "this doesn't make sense",
            "help",
        ];
        if (
            frustrationKeywords.some((keyword) =>
                currentMessage.toLowerCase().includes(keyword)
            )
        ) {
            if (history.filter((msg) => msg.role === "ai").length > 3)
                return true;
        }

        return false;
    }

    private similarityScore(str1: string, str2: string): number {
        // Simple Jaccard similarity
        const set1 = new Set(str1.split(/\s+/));
        const set2 = new Set(str2.split(/\s+/));
        const intersection = new Set([...set1].filter((x) => set2.has(x)));
        const union = new Set([...set1, ...set2]);
        return intersection.size / union.size;
    }

    private async getCourseTitle(courseId: string): Promise<string> {
        const result = await db.query(
            "SELECT title FROM courses.courses WHERE id = $1",
            [courseId]
        );
        return result.rows[0]?.title || "Unknown Course";
    }
}
```

---

### 3. Course Service

**Responsibility:** Course management, content versioning, publishing, CMS functionality

**Endpoints:**

```typescript
// GET /api/v1/courses
// - List all published courses with pagination/filtering
Request: {
  page?: number,
  limit?: number,
  domain?: string,
  difficulty?: 'beginner' | 'intermediate' | 'advanced'
}
Response: {
  courses: CourseObject[],
  total: number,
  page: number,
  totalPages: number
}

// POST /api/v1/courses (Admin/Tutor only)
// - Create new course
// - Initialize with default structure
Request: {
  title: string,
  description: string,
  domain: string,
  difficulty: string,
  estimatedHours: number,
  skillsTaught: string[]
}
Response: {
  courseId: UUID,
  status: 'draft',
  versionNumber: 1
}

// GET /api/v1/courses/:courseId
// - Retrieve full course structure with all modules/lessons
Response: {
  id: UUID,
  title: string,
  description: string,
  modules: ModuleObject[],
  skills: string[],
  difficulty: string,
  estimatedHours: number,
  enrollmentCount: number,
  rating: number
}

// PUT /api/v1/courses/:courseId
// - Update course metadata
// - Create new version
Request: {
  title?: string,
  description?: string,
  skills?: string[]
}
Response: {
  courseId: UUID,
  versionNumber: number,
  status: string
}

// POST /api/v1/courses/:courseId/modules
// - Add new module to course
Request: {
  title: string,
  description: string,
  sequenceOrder: number,
  estimatedMinutes: number
}
Response: {
  moduleId: UUID,
  courseId: UUID,
  sequenceOrder: number
}

// POST /api/v1/courses/:courseId/modules/:moduleId/lessons
// - Add new lesson to module
Request: {
  title: string,
  contentType: 'text' | 'video' | 'interactive' | 'exercise',
  contentData: object,
  videoUrl?: string,
  durationMinutes: number,
  learningObjectives: string[]
}
Response: {
  lessonId: UUID,
  moduleId: UUID,
  sequenceOrder: number
}

// POST /api/v1/courses/:courseId/publish
// - Publish course (make immutable version)
// - Generate content embeddings for RAG
// - Make available for enrollment
Request: {}
Response: {
  courseId: UUID,
  status: 'published',
  publishedAt: DateTime,
  totalLessons: number,
  embeddingsGenerated: boolean
}

// POST /api/v1/courses/:courseId/generate-embeddings
// - Generate OpenAI embeddings for all content
// - Store in Pinecone
// - Called on publish or content update
Request: {}
Response: {
  success: boolean,
  embeddingsCreated: number,
  vectorDbUpdated: boolean
}

// GET /api/v1/courses/:courseId/versions
// - Retrieve version history
Response: {
  versions: {
    versionNumber: number,
    publishedAt: DateTime,
    changes: string[],
    enrollmentCount: number
  }[]
}
```

---

### 4. Assessment Service

**Responsibility:** Quizzes, exams, scoring, certification generation

**Endpoints:**

```typescript
// POST /api/v1/assessments
// - Create new assessment
Request: {
  courseId: UUID,
  title: string,
  type: 'quiz' | 'module_test' | 'final_exam' | 'practical',
  passingScore: number,
  durationMinutes: number,
  isProctored: boolean
}
Response: {
  assessmentId: UUID,
  courseId: UUID
}

// POST /api/v1/assessments/:assessmentId/questions
// - Add question to assessment
Request: {
  type: 'multiple_choice' | 'short_answer' | 'essay' | 'code',
  questionText: string,
  options?: string[],
  correctAnswer: string | object,
  explanation: string,
  difficulty: 'easy' | 'medium' | 'hard'
}
Response: {
  questionId: UUID,
  assessmentId: UUID
}

// POST /api/v1/assessments/:assessmentId/start
// - Start assessment attempt
// - Randomize question order (if configured)
// - Initialize proctoring (if needed)
Request: {
  learnerId: UUID
}
Response: {
  submissionId: UUID,
  questions: QuestionObject[],
  timeLimit: number,
  protoringUrl?: string
}

// POST /api/v1/assessments/submissions/:submissionId/submit-answer
// - Submit answer to single question
Request: {
  questionId: UUID,
  answer: string | object,
  timeSpentSeconds: number
}
Response: {
  nextQuestion?: QuestionObject,
  isLastQuestion: boolean
}

// POST /api/v1/assessments/submissions/:submissionId/submit
// - Submit entire assessment
// - Auto-grade (MCQ, auto-score)
// - Queue for human grading (essays, practical)
Request: {}
Response: {
  submissionId: UUID,
  score: number,
  passed: boolean,
  feedback: string,
  nextSteps: string[]
}

// GET /api/v1/assessments/submissions/:submissionId/results
// - Retrieve submitted assessment results
Response: {
  assessmentId: UUID,
  learnerId: UUID,
  score: number,
  passed: boolean,
  submittedAt: DateTime,
  answers: object[],
  incorrectQuestions: object[]
}

// POST /api/v1/certificates/generate
// - Trigger certificate generation
// - Called after passing final assessment
Request: {
  enrollmentId: UUID,
  learnerId: UUID,
  courseId: UUID
}
Response: {
  certificateId: UUID,
  verificationCode: string,
  pdfUrl: string,
  linkedinShareUrl: string
}

// GET /api/v1/certificates/:verificationCode
// - Public endpoint to verify certificate authenticity
Response: {
  valid: boolean,
  learnerName: string,
  courseName: string,
  issuedDate: DateTime,
  expiryDate?: DateTime
}
```

---

### 5. Enterprise Service

**Responsibility:** Organization management, team management, course assignments, permissions

**Endpoints:**

```typescript
// POST /api/v1/organizations
// - Create new organization
Request: {
  name: string,
  industry: string,
  country: string,
  website?: string,
  adminUserId: UUID,
  planTier: 'starter' | 'growth' | 'enterprise' | 'institutional'
}
Response: {
  organizationId: UUID,
  planTier: string,
  maxLearners: number,
  createdAt: DateTime
}

// GET /api/v1/organizations/:organizationId
// - Retrieve organization details and stats
Response: {
  organizationId: UUID,
  name: string,
  planTier: string,
  activeLearnersCount: number,
  maxLearners: number,
  courses: CourseObject[],
  administrators: UserObject[]
}

// POST /api/v1/organizations/:organizationId/import-learners
// - Bulk import learners from CSV
Request: {
  csvFile: File // CSV: email, firstName, lastName, department
}
Response: {
  imported: number,
  failed: number,
  errors: {learnerId: string, error: string}[]
}

// POST /api/v1/organizations/:organizationId/assign-course
// - Assign course to individual learner or team
Request: {
  courseId: UUID,
  learnersOrTeamIds: UUID[],
  deadline?: DateTime
}
Response: {
  assignmentId: UUID,
  learnersAssigned: number
}

// GET /api/v1/organizations/:organizationId/dashboard
// - Retrieve dashboard statistics
Response: {
  activeLearners: number,
  completionRate: number,
  averageScore: number,
  atRiskLearners: number,
  courseProgress: {
    courseId: UUID,
    completionRate: number,
    enrolledCount: number
  }[]
}

// GET /api/v1/organizations/:organizationId/reports/learner-progress
// - Generate learner progress report
Request: {
  startDate?: DateTime,
  endDate?: DateTime,
  format: 'pdf' | 'excel'
}
Response: {
  reportUrl: string,
  format: string,
  generatedAt: DateTime
}

// GET /api/v1/organizations/:organizationId/reports/compliance
// - Generate compliance audit report
Response: {
  learnersWithCertificates: number,
  completionDeadlines: object,
  auditTrail: object,
  reportUrl: string
}
```

---

### 6. Notification Service

**Responsibility:** Email, WhatsApp, SMS, push notifications

**Endpoints:**

```typescript
// POST /api/v1/notifications/preferences
// - Update notification preferences for user
Request: {
  emailEnabled: boolean,
  whatsappEnabled: boolean,
  smsEnabled: boolean,
  pushEnabled: boolean,
  preferLanguage: string
}
Response: {
  preferencesUpdated: boolean
}

// POST /api/v1/notifications/send-test
// - Send test notification to user
Request: {
  channel: 'email' | 'whatsapp' | 'sms'
}
Response: {
  sent: boolean,
  status: string
}
```

**Internal Event Handlers (not exposed via API):**

```typescript
// Email notifications
async function handleLearnerEnrolled(event: EnrollmentEvent) {
    const learner = await db.query("SELECT * FROM auth.users WHERE id = $1", [
        event.learnerId,
    ]);
    await sendEmail(learner.email, {
        subject: `Welcome to ${event.courseName}!`,
        template: "course_enrollment",
        context: { courseName: event.courseName, deadline: event.deadline },
    });
}

// WhatsApp nudges
async function handleLearnerInactive(learnerId: string) {
    const learner = await getLearnerProfile(learnerId);
    const enrollment = await getActiveEnrollment(learnerId);

    await sendWhatsApp(learner.phone_number, {
        body: `Hi ${learner.firstName}, you haven't logged in for 3 days. Your course "${enrollment.courseName}" is waiting! 🎓 Complete your next 20-minute lesson: ${shortUrl}`,
        buttons: [{ text: "Start Learning", url: environmentUrl }],
    });
}

// Assessment completion notifications
async function handleAssessmentPassed(event: AssessmentPassedEvent) {
    const learner = await getLearnerProfile(event.learnerId);

    // Email: certificate
    await sendEmail(learner.email, {
        subject: "Congratulations! You passed!",
        template: "certificate_earned",
        context: {
            courseName: event.courseName,
            certificateUrl: event.certificateUrl,
            linkedinShareUrl: event.linkedinShareUrl,
        },
        attachments: [{ path: event.certificatePdf }],
    });

    // WhatsApp: quick congratulation
    await sendWhatsApp(learner.phone_number, {
        body: `🎉 Congrats ${learner.firstName}! You passed "${event.courseName}"! Your certificate is ready: ${shortUrl}`,
    });
}
```

**Integrations:**

```typescript
// Resend for email
import { Resend } from "resend";
const resend = new Resend(process.env.RESEND_API_KEY);

async function sendEmail(to: string, options: EmailOptions) {
    return resend.emails.send({
        from: "noreply@elitecoach.ai",
        to,
        subject: options.subject,
        html: renderTemplate(options.template, options.context),
    });
}

// Twilio for WhatsApp
import twilio from "twilio";
const twilioClient = twilio(
    process.env.TWILIO_ACCOUNT_SID,
    process.env.TWILIO_AUTH_TOKEN
);

async function sendWhatsApp(phoneNumber: string, message: string) {
    return twilioClient.messages.create({
        body: message,
        from: process.env.TWILIO_WHATSAPP_NUMBER,
        to: `whatsapp:${phoneNumber}`,
    });
}

// SendGrid for transactional email (alternative)
import sgMail from "@sendgrid/mail";
sgMail.setApiKey(process.env.SENDGRID_API_KEY);

async function sendTransactionalEmail(
    to: string,
    templateId: string,
    context: object
) {
    return sgMail.send({
        to,
        from: "noreply@elitecoach.ai",
        templateId,
        dynamicTemplateData: context,
    });
}
```

---

## Core Data Structures

This continues in the next documentation file...

Would you like me to continue with:

-   Authentication & Authorization (detailed JWT implementation, RBAC)
-   Error Handling & Resilience Patterns
-   Monitoring & Observability
-   Deployment Strategy (Docker, K8s)
-   Security Implementation Details
-   API Specifications (OpenAPI specs)
-   Data Flow Diagrams

Create the continuation document?
