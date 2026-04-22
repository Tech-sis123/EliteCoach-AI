# AI Tutor Engine Service

Advanced AI-powered tutoring platform built with FastAPI, leveraging RAG (Retrieval-Augmented Generation) for intelligent content delivery and microservice architecture for scalability.

**Service Port:** 3002  
**Framework:** FastAPI + Python  
**Architecture:** Event-Driven Microservices

## Overview

The AI Tutor Engine is the core learning service in the Elite Coach microservice ecosystem. It provides:

-   **RAG-Powered AI Tutoring**: Semantically-aware responses based on course content
-   **Interactive Learning Sessions**: Real-time AI-student dialogue
-   **Personalized Learning Paths**: AI-generated study plans tailored to learner goals
-   **Assessment & Feedback**: Automated quiz generation and intelligent grading
-   **Event-Driven Architecture**: Pub/Sub communication via RabbitMQ
-   **Microservice Integration**: Delegates authentication to Identity Service

## Project Structure

```
ai-tutor-engine-service/
├── app/
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── database.py          # Database setup (SQLAlchemy)
│   │   └── security.py          # JWT validation & auth middleware
│   ├── models/
│   │   └── models.py            # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── services/
│   │   ├── ai_tutor.py          # AI tutor business logic
│   │   ├── rag_engine.py        # RAG pipeline for semantic search
│   │   ├── event_publisher.py   # RabbitMQ event publishing
│   │   └── identity_service_client.py  # Identity Service integration
│   ├── routes/
│   │   ├── tutor_sessions.py    # AI tutor endpoints
│   │   ├── learning_paths.py    # Learning path endpoints
│   │   ├── assessments.py       # Assessment endpoints
│   │   └── health.py            # Health check endpoints
│   └── main.py                  # FastAPI app initialization
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Local development stack
├── Dockerfile                   # Container image definition
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Key Technologies

| Layer             | Technology              | Purpose                        |
| ----------------- | ----------------------- | ------------------------------ |
| **Runtime**       | Python 3.11             | Language runtime               |
| **Framework**     | FastAPI                 | REST API with async support    |
| **AI/ML**         | OpenAI GPT-4, LangChain | LLM integration & RAG pipeline |
| **Vector DB**     | Pinecone/Weaviate       | Semantic search & embeddings   |
| **Message Queue** | RabbitMQ                | Event-driven communication     |
| **Database**      | PostgreSQL              | Primary data storage           |
| **Cache**         | Redis                   | Session/response caching       |
| **ORM**           | SQLAlchemy              | Database abstraction           |

## API Endpoints

### Health & Monitoring

```bash
GET /api/v1/health                           # Health check
GET /api/v1/health/ready                     # Readiness check
```

### Tutor Sessions (Core AI Interaction)

```bash
POST   /api/v1/learning/sessions/start        # Start new session
POST   /api/v1/learning/sessions/{id}/message # Send message to tutor
GET    /api/v1/learning/sessions/{id}         # Get session transcript
POST   /api/v1/learning/sessions/{id}/end     # End session & get summary
GET    /api/v1/learning/sessions              # List user's sessions
```

### Learning Paths (Personalized Study Plans)

```bash
POST   /api/v1/learning/paths/generate        # Generate personalized path
GET    /api/v1/learning/paths/{user_id}       # Get current path
PUT    /api/v1/learning/paths/{user_id}       # Update path preferences
```

### Assessments (Quizzes & Exams)

```bash
POST   /api/v1/assessments/generate-quiz      # Generate quiz
POST   /api/v1/assessments/submit             # Submit answers
GET    /api/v1/assessments/results/{id}       # Get graded results
```

## Getting Started

### Prerequisites

-   Python 3.11+
-   Docker & Docker Compose (optional, for containerized setup)
-   OpenAI API Key
-   PostgreSQL (or use Docker Compose)

### Local Development Setup

1. **Clone and navigate to project:**

```bash
cd ai-tutor-engine-service
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Copy environment template:**

```bash
cp .env.example .env
```

4. **Update .env with your API keys:**

```bash
OPENAI_API_KEY=sk-your-key-here
IDENTITY_SERVICE_URL=http://localhost:8001
```

5. **Install dependencies:**

```bash
pip install -r requirements.txt
```

6. **Run with Docker Compose (recommended):**

```bash
docker-compose up -d
```

This starts:

-   Learning Service (port 3002)
-   PostgreSQL (port 5432)
-   RabbitMQ (ports 5672, 15672)
-   Redis (port 6379)
-   Weaviate (port 8080)

7. **Or run locally:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
```

8. **Access API documentation:**

-   Swagger UI: http://localhost:3002/api/docs
-   ReDoc: http://localhost:3002/api/redoc

## Usage Examples

### Start an AI Tutoring Session

```bash
curl -X POST http://localhost:3002/api/v1/learning/sessions/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "subject_id": 5,
    "topic": "Python Functions"
  }'
```

Response:

```json
{
    "session_id": 42,
    "topic": "Python Functions",
    "ai_greeting": "Hello! I'm excited to help you master Python functions. What aspect would you like to focus on today?",
    "status": "active"
}
```

### Send Message to AI Tutor

```bash
curl -X POST http://localhost:3002/api/v1/learning/sessions/42/message \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is a lambda function?",
    "subject_id": 5,
    "context": "Python Functions"
  }'
```

### Generate Personalized Learning Path

```bash
curl -X POST http://localhost:3002/api/v1/learning/paths/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_role": "Data Scientist",
    "time_per_week": 10,
    "current_skills": {
      "python": "beginner",
      "sql": "none",
      "statistics": "none"
    }
  }'
```

### Generate and Submit Quiz

```bash
# Generate quiz
curl -X POST http://localhost:3002/api/v1/assessments/generate-quiz \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "course_id": 1,
    "topic": "List Comprehensions",
    "num_questions": 5,
    "level": "intermediate"
  }'

# Submit answers
curl -X POST http://localhost:3002/api/v1/assessments/submit \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "course_id": 1,
    "questions": [...],
    "answers": [...]
  }'
```

## Architecture Highlights

### RAG Pipeline (rag_engine.py)

The RAG (Retrieval-Augmented Generation) pipeline enables context-aware AI responses:

```python
1. Embed learner question using OpenAI embeddings
2. Retrieve top-5 semantically similar course content chunks from vector DB
3. Build system prompt with relevant context
4. Generate AI response using GPT-4 with course context
5. Check escalation triggers (low confidence, frustration, repeated questions)
```

### Event-Driven Communication (event_publisher.py)

Events published to RabbitMQ for async processing:

-   `learner.session.started` → Notification service sends welcome email
-   `learner.session.completed` → Analytics service updates metrics
-   `learner.course.completed` → Certificate service generates certificate
-   `escalation.triggered` → Tutor service assigns human tutor
-   `ai.response.generated` → Analytics service tracks engagement

### Microservice Integration (identity_service_client.py)

Delegates authentication to the Identity Service:

-   Verifies JWT tokens
-   Retrieves user profiles
-   Manages refresh tokens
-   Handles logout

## Configuration

### Environment Variables

```bash
# API Configuration
API_TITLE=AI Tutor Engine
API_VERSION=1.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost/tutor_db

# OpenAI
OPENAI_API_KEY=sk-...

# Identity Service (existing auth service)
IDENTITY_SERVICE_URL=http://localhost:8001

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost/

# Vector DB (choose one)
PINECONE_API_KEY=...
# OR
WEAVIATE_HOST=http://localhost:8080

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Data Models

### TutorSession

Stores AI-learner conversations with metadata.

### StudentProgress

Tracks learner progress across courses.

### Assessment

Records quiz/exam submissions and scores.

### Course Content Chunks

Indexed for RAG semantic search.

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t elite-coach/learning-service:1.0.0 .

# Run container
docker run -p 3002:3002 \
  -e OPENAI_API_KEY=sk-... \
  -e DATABASE_URL=postgresql://... \
  elite-coach/learning-service:1.0.0
```

### Kubernetes Deployment

See `k8s/deployment.yaml` for production-grade Kubernetes manifests.

###Environment-Specific Configuration

-   **Development**: SQLite, local services via Docker Compose
-   **Staging**: PostgreSQL, remote RabbitMQ, Pinecone
-   **Production**: PostgreSQL cluster, managed RabbitMQ, Pinecone, CDN for assets

## Error Handling

All endpoints follow standard error responses:

```json
{
    "detail": "User not found",
    "status_code": 404,
    "error_code": "USER_NOT_FOUND"
}
```

## Logging

Structured logging with JSON format:

```python
logger.info("Session started", extra={
    "user_id": "123e4567",
    "session_id": "456",
    "course_id": "789"
})
```

View logs:

```bash
docker logs learning-service
```

## Testing

Run tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Performance Optimization

-   **Caching**: User profiles, course content cached in Redis
-   **Batch Processing**: RAG queries optimized for <100ms response
-   **Connection Pooling**: Database connections pooled via SQLAlchemy
-   **Async/Await**: All I/O operations non-blocking

## Monitoring & Observability

-   **Metrics**: Prometheus endpoint at `/metrics`
-   **Distributed Tracing**: OpenTelemetry integration (Phase 1)
-   **Logging**: ELK stack integration (Phase 1)
-   **Alerting**: PagerDuty integration (Phase 1)

## Known Limitations

-   Vector embeddings stored in-memory (production uses Pinecone/Weaviate)
-   No rate limiting on tutor endpoints (add Redis-based RATELIMIT middleware)
-   Single-instance deployment (use load balancer for HA)

## Future Enhancements

-   [ ] Real-time collaboration with CodePen integration
-   [ ] Voice input/output for accessibility
-   [ ] Mobile app support (WebSocket optimization)
-   [ ] Advanced RAG with multi-query retrieval
-   [ ] ML-based escalation prediction
-   [ ] Interactive code execution environment

## Support & Contributing

For issues, email: engineering@elite-coach.ai

## License

Proprietary - Elite Coach AI © 2026
