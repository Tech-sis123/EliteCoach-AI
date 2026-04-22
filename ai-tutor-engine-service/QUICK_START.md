# AI Tutor Engine - Quick Start & Deployment Guide

## ✅ What's Been Built

The AI Tutor Engine Service is now fully scaffolded as a modern microservice following the Elite Coach architecture guide. This is the **Learning Service (Port 3002)**.

### Core Components

```
✓ RAG Pipeline (LangChain + OpenAI)
  → Semantic search over course content
  → GPT-4 integration with context awareness
  → Escalation trigger detection

✓ Event-Driven Architecture (RabbitMQ)
  → Session lifecycle events
  → Analytics event publishing
  → Integration with other microservices

✓ Identity Service Integration
  → JWT token validation via Identity Service (port 8001)
  → User profile retrieval
  → Role-based access control

✓ RESTful API Endpoints
  → Tutor sessions (start, message, end)
  → Learning paths (generate, retrieve)
  → Assessments (quizzes, grading)
  → Health checks

✓ Database Models (SQLAlchemy)
  → TutorSession
  → StudentProgress
  → Assessment
  → Course content indexing

✓ Docker & Kubernetes Ready
  → Multi-stage Dockerfile
  → docker-compose.yml with all dependencies
  → Health checks & readiness probes
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

**Start everything with one command:**

```bash
cd /path/to/ai-tutor-engine-service
docker-compose up -d
```

This starts:

-   **Learning Service** (port 3002) ← Your AI Tutor Engine
-   **PostgreSQL** (port 5432) ← Database
-   **RabbitMQ** (ports 5672, 15672) ← Message queue + admin UI
-   **Redis** (port 6379) ← Caching layer
-   **Weaviate** (port 8080) ← Vector database for RAG

**Verify services are running:**

```bash
curl http://localhost:3002/api/v1/health
# Expected: {"status": "healthy", "service": "learning-service"}
```

**Access RabbitMQ Management UI:**

```
http://localhost:15672
Username: guest
Password: guest
```

### Option 2: Manual Local Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup PostgreSQL manually or use Docker:
docker run -d --name postgres \
  -e POSTGRES_USER=tutor_user \
  -e POSTGRES_PASSWORD=tutor_password \
  -e POSTGRES_DB=tutor_db \
  -p 5432:5432 \
  postgres:15-alpine

# 4. Setup RabbitMQ:
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3.12-management-alpine

# 5. Setup Redis:
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# 6. Update .env with database URLs
cp .env.example .env
# Edit .env and update DATABASE_URL, RABBITMQ_URL, etc.

# 7. Run the service
uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
```

## 📋 Configuration

### Required Environment Variables

```bash
# OpenAI (required for AI tutor)
OPENAI_API_KEY=sk-your-api-key-here

# Identity Service (for authentication)
IDENTITY_SERVICE_URL=http://localhost:8001

# Database
DATABASE_URL=postgresql://tutor_user:tutor_password@postgres:5432/tutor_db

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

### Optional Configuration

```bash
# Vector DB (Pinecone for production RAG)
PINECONE_API_KEY=your-key-here
PINECONE_ENV=us-west1-gcp-free

# Or use local Weaviate
WEAVIATE_HOST=http://localhost:8080

# Redis (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🔌 API Quick Reference

### 1. Start AI Tutoring Session

```bash
curl -X POST http://localhost:3002/api/v1/learning/sessions/start \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "subject_id": 5,
    "topic": "Python Functions",
    "db": null
  }'
```

**Response:**

```json
{
    "session_id": 1,
    "topic": "Python Functions",
    "ai_greeting": "Hello! I'm here to help you learn Python Functions. What would you like to start with?",
    "status": "active"
}
```

### 2. Send Message to AI Tutor

```bash
curl -X POST http://localhost:3002/api/v1/learning/sessions/1/message \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is a lambda function?",
    "subject_id": 5,
    "context": "Python Functions"
  }'
```

**Response:**

```json
{
    "session_id": 1,
    "user_message": "What is a lambda function?",
    "ai_response": "A lambda function is a small anonymous function in Python that can take any number of arguments...",
    "confidence_score": 0.92,
    "escalation_needed": false
}
```

### 3. Generate Personalized Learning Path

```bash
curl -X POST http://localhost:3002/api/v1/learning/paths/generate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_role": "Data Scientist",
    "time_per_week": 10,
    "current_skills": {"python": "beginner"}
  }'
```

### 4. Get All Endpoints

```bash
# API Documentation (Swagger UI)
open http://localhost:3002/api/docs

# ReDoc documentation
open http://localhost:3002/api/redoc
```

## 🧪 Testing the Service

### Health Checks

```bash
# Basic health check
curl http://localhost:3002/api/v1/health

# Readiness check (for k8s)
curl http://localhost:3002/api/v1/health/ready
```

### Test Database Connection

```bash
# View PostgreSQL
docker exec postgres psql -U tutor_user -d tutor_db -c "\dt"

# View RabbitMQ queues
curl -u guest:guest http://localhost:15672/api/queues
```

### Run Unit Tests

```bash
pytest tests/ -v
pytest tests/ --cov=app  # With coverage report
```

## 📊 Monitoring

### View Logs

```bash
# Docker Compose logs
docker-compose logs -f learning-service

# Specific tail
docker-compose logs -f learning-service | grep "error"
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U tutor_user -d tutor_db

# View tables
\dt

# Query sessions
SELECT * FROM tutor_sessions LIMIT 10;
```

### RabbitMQ Monitoring

**Web UI:** http://localhost:15672

-   **Username:** guest
-   **Password:** guest

View:

-   Queues created: `elite-coach-events`
-   Message publishing rates
-   Consumer connections

## 🔗 Integration Points

### With Identity Service (Port 8001)

The Learning Service validates all requests through the Identity Service:

```
User sends request with JWT
    ↓
FastAPI middleware calls Identity Service
    ↓
Identity Service validates JWT and returns user profile
    ↓
Request proceeds with user context
```

### With RabbitMQ (Event Publishing)

Events published to `elite-coach-events` exchange:

```
Session Started
    ↓ (published)
Notification Service listens and sends welcome email
Analytics Service listens and records metric

Session Completed
    ↓ (published)
Certificate Service generates certificate
Analytics Service updates progress

Escalation Triggered
    ↓ (published)
Tutor Service assigns human tutor
```

## 🐳 Docker Commands

```bash
# View running containers
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# View logs
docker-compose logs learning-service

# Rebuild image
docker-compose build --no-cache

# Execute command in container
docker-compose exec learning-service bash

# View container stats
docker stats
```

## 🚨 Troubleshooting

### "Connection refused" to PostgreSQL

```bash
# Check if database is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose up -d postgres
```

### RabbitMQ Connection Errors

```bash
# Verify RabbitMQ is running
docker-compose ps rabbitmq

# Check if port 5672 is open
docker exec rabbitmq rabbitmq-diagnostics check_virtual_host -p /guest

# Reset RabbitMQ
docker-compose down -v
docker-compose up -d rabbitmq
```

### OpenAI API Errors

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check logs for specific error
docker-compose logs learning-service | grep -i "openai\|auth\|api"
```

### Database Migrations Needed

```bash
# Run Alembic migrations (when needed)
docker-compose exec learning-service \
  alembic upgrade head
```

## 📈 Performance Tuning

### Database Query Optimization

```python
# Check slow queries
docker exec postgres psql -U tutor_user -d tutor_db \
  -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### RabbitMQ Optimization

```bash
# Increase queue prefetch
# Edit docker-compose.yml environment:
# RABBITMQ_HEARTBEAT=60
# RABBITMQ_CHANNEL_MAX=2048
```

### Redis Caching

```bash
# Monitor cache hits
docker exec redis redis-cli INFO stats
```

## 🔐 Security Checklist

-   [ ] OpenAI API key stored in `.env`, never committed
-   [ ] JWT tokens validated through Identity Service
-   [ ] Database credentials different for dev/prod
-   [ ] RabbitMQ password changed from default
-   [ ] CORS origins restricted to known domains
-   [ ] SQL injection prevention (using SQLAlchemy ORM)
-   [ ] No sensitive data in logs

## 📝 Next Steps

### Immediate (Before Going to Staging)

1. **Test RAG Pipeline**

    - Index sample course content
    - Verify semantic search works
    - Test escalation triggers

2. **Load Testing**

    ```bash
    pip install locust
    locust -f tests/load_test.py --host=http://localhost:3002
    ```

3. **Security Audit**
    - Rotate all API keys
    - Review CORS settings
    - Test token expiration

### Short-term (Phase 1)

1. **Add Request Validation**

    - Input sanitization
    - Rate limiting middleware

2. **Enhanced Logging**

    - Structured JSON logging
    - ELK stack integration

3. **Distributed Tracing**
    - OpenTelemetry setup
    - Jaeger collector

### Medium-term (Phase 2+)

1. **Production Deployment**

    - Kubernetes manifests
    - Helm charts
    - ArgoCD configuration

2. **Advanced RAG**

    - Pinecone production integration
    - Multi-query retrieval
    - Streaming responses

3. **ML Features**
    - Learner skill prediction
    - Escalation prediction model
    - Adaptive content sequencing

## 📚 Documentation Files

-   **README.md** - Full API documentation
-   **BACKEND_IMPLEMENTATION_GUIDE.md** - Architecture overview
-   **docker-compose.yml** - Local environment setup
-   **Dockerfile** - Container build definition

## 🆘 Support

### Getting Help

1. Check logs: `docker-compose logs learning-service`
2. Review README.md API examples
3. Check BACKEND_IMPLEMENTATION_GUIDE.md for architecture details
4. Review Swagger docs: http://localhost:3002/api/docs

### Reporting Issues

When reporting issues include:

-   Docker Compose version: `docker-compose --version`
-   Service logs: `docker-compose logs learning-service`
-   Your `.env` settings (without secrets)
-   Curl command that's failing

---

**You're all set!** The AI Tutor Engine is ready for local development and testing. 🚀
