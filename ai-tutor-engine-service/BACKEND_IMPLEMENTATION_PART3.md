# Elite Coach AI - Backend Implementation Documentation

## Part 3: Security, API Specs & Implementation Checklist

---

## Security Implementation

### Network Security

**HTTPS/TLS Configuration:**

```typescript
// src/server.ts

import https from 'https';
import fs from 'fs';
import express from 'express';
import helmet from 'helmet';
import hpp from 'hpp';
import cors from 'cors';

const app = express();

// Security headers via Helmet
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", 'https:'],
      connectSrc: ["'self'", 'https://api.openai.com', 'https://control.pinecone.io']
    }
  },
  hsts: {
    maxAge: 31536000, // 1 year
    includeSubDomains: true,
    preload: true
  },
  frameguard: { action: 'deny' },
  xssFilter: true,
  noSniff: true,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' }
}));

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGINS?.split(',') || ['https://app.elitecoach.ai'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400
}));

// Prevent HTTP Parameter Pollution
app.use(hpp());

// Rate limiting for all routes
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    res.status(429).json({
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests, please try again later'
      }
    });
  }
});

app.use('/api/', limiter);

// Stricter rate limiting for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 5 attempts per 15 minutes
  skipSuccessfulRequests: true
});

app.post('/api/v1/auth/login', authLimiter, ...);
app.post('/api/v1/auth/mfa/verify-login', authLimiter, ...);

// HTTPS/TLS Server
const credentials = {
  key: fs.readFileSync(process.env.TLS_KEY_PATH),
  cert: fs.readFileSync(process.env.TLS_CERT_PATH)
};

https.createServer(credentials, app).listen(3000, () => {
  logger.info('Secure HTTPS server running on port 3000');
});
```

### Data Protection

**Encryption at Rest:**

```typescript
// src/utils/encryption.ts

import crypto from "crypto";

export class EncryptionService {
    private algorithm = "aes-256-gcm";
    private encryptionKey = Buffer.from(process.env.ENCRYPTION_KEY!, "hex");

    encrypt(plaintext: string, userId: string): string {
        const iv = crypto.randomBytes(12);
        const cipher = crypto.createCipheriv(
            this.algorithm,
            this.encryptionKey,
            iv
        );

        let encrypted = cipher.update(plaintext, "utf8", "hex");
        encrypted += cipher.final("hex");

        const authTag = cipher.getAuthTag();

        // Include IV and auth tag with ciphertext
        return `${iv.toString("hex")}:${authTag.toString("hex")}:${encrypted}`;
    }

    decrypt(encryptedData: string): string {
        const [ivHex, authTagHex, encrypted] = encryptedData.split(":");

        const iv = Buffer.from(ivHex, "hex");
        const authTag = Buffer.from(authTagHex, "hex");

        const decipher = crypto.createDecipheriv(
            this.algorithm,
            this.encryptionKey,
            iv
        );
        decipher.setAuthTag(authTag);

        let decrypted = decipher.update(encrypted, "hex", "utf8");
        decrypted += decipher.final("utf8");

        return decrypted;
    }

    // Hash sensitive data (irreversible)
    hash(data: string): string {
        return crypto
            .createHash("sha256")
            .update(data + process.env.HASH_SALT!)
            .digest("hex");
    }
}

// Usage for sensitive fields
async function storeSensitiveData(userId: string, data: string) {
    const encryptionService = new EncryptionService();
    const encrypted = encryptionService.encrypt(data, userId);

    await pool.query(
        "UPDATE auth.users SET credential_data = $1 WHERE id = $2",
        [encrypted, userId]
    );
}

// PostgreSQL native encryption (pgcrypto extension)
// CREATE EXTENSION IF NOT EXISTS pgcrypto;

// For highly sensitive data:
async function storeHighlySensitiveData(data: string) {
    await pool.query(
        `INSERT INTO sensitive_data (encrypted_value)
     VALUES (pgp_sym_encrypt($1, $2))`,
        [data, process.env.PGP_KEY]
    );
}
```

**PII Masking & Anonymization:**

```typescript
// src/utils/dataProtection.ts

export class DataProtectionService {
    // Mask personally identifiable information
    maskPII(obj: any): any {
        const masked = { ...obj };

        if (masked.email) {
            masked.email = this.maskEmail(masked.email);
        }

        if (masked.phone_number) {
            masked.phone_number = this.maskPhoneNumber(masked.phone_number);
        }

        if (masked.password) {
            masked.password = "[REDACTED]";
        }

        return masked;
    }

    maskEmail(email: string): string {
        const [localPart, domain] = email.split("@");
        const masked =
            localPart.substring(0, 2) + "*".repeat(localPart.length - 2);
        return `${masked}@${domain}`;
    }

    maskPhoneNumber(phone: string): string {
        return (
            phone.substring(0, 3) +
            "*".repeat(phone.length - 6) +
            phone.substring(phone.length - 3)
        );
    }

    // Anonymize user for analytics
    async anonymizeUser(userId: string): Promise<void> {
        const anonymousId = `anon_${crypto.randomUUID()}`;

        await pool.query(
            `UPDATE auth.users
       SET email = $1, first_name = 'Anonymous', last_name = 'User',
           phone_number = NULL, password_hash = NULL
       WHERE id = $2`,
            [anonymousId, userId]
        );

        // Update related records
        await pool.query(
            `UPDATE learning.learners SET current_skill_level = '{}'
       WHERE user_id = $1`,
            [userId]
        );
    }

    // Data retention policy
    async enforceDataRetention(): Promise<void> {
        // Delete ceased learner data after 2 years
        await pool.query(
            `DELETE FROM learning.learning_sessions
       WHERE learner_id IN (
         SELECT id FROM learning.learners
         WHERE user_id IN (
           SELECT id FROM auth.users WHERE status = 'deleted'
           AND updated_at < NOW() - INTERVAL '2 years'
         )
       )`
        );

        // Archive old analytics
        await pool.query(
            `DELETE FROM analytics.learner_metrics
       WHERE metric_date < NOW() - INTERVAL '7 years'`
        );
    }
}
```

### SQL Injection Prevention

```typescript
// Always use parameterized queries

// VULNERABLE (DO NOT USE)
const query = `SELECT * FROM users WHERE email = '${email}'`;

// SECURE
const query = "SELECT * FROM users WHERE email = $1";
const result = await pool.query(query, [email]);

// Using TypeScript/ORM example with type safety
import { sql } from "postgres";

const result = await sql`
  SELECT * FROM learning.enrollments
  WHERE learner_id = ${learnerId}
  AND course_id = ${courseId}
`;
```

### NDPR Compliance (Nigeria Data Protection Regulation)

```typescript
// src/compliance/ndprCompliance.ts

export class NDPRCompliance {
    /**
     * Sect. 1. Processing basis - must have lawful basis
     */
    async validateProcessingBasis(
        userId: string,
        processingType: string
    ): Promise<boolean> {
        // Lawful bases: consent, contract, legal obligation, vital interests, public task, legitimate interests
        const consent = await pool.query(
            `SELECT * FROM compliance.user_consents
       WHERE user_id = $1 AND consent_type = $2 AND granted = true
       AND expires_at > NOW()`,
            [userId, processingType]
        );

        return consent.rows.length > 0;
    }

    /**
     * Sect. 4. Rights of data subjects - Right to access
     */
    async exportUserData(userId: string): Promise<object> {
        const result = await pool.query(
            `SELECT 
        u.id, u.email, u.first_name, u.last_name,
        l.learning_path, l.current_skill_level,
        e.enrolled_courses, a.assessments
       FROM auth.users u
       LEFT JOIN learning.learners l ON u.id = l.user_id
       LEFT JOIN (
         SELECT learner_id, ARRAY_AGG(course_id) as enrolled_courses
         FROM learning.enrollments GROUP BY learner_id
       ) e ON l.id = e.learner_id
       LEFT JOIN (
         SELECT learner_id, ARRAY_AGG(score) as assessments
         FROM assessments.submissions GROUP BY learner_id
       ) a ON l.id = a.learner_id
       WHERE u.id = $1`,
            [userId]
        );

        return {
            userData: result.rows[0],
            exportedAt: new Date().toISOString(),
            exportFormat: "JSON",
        };
    }

    /**
     * Sect. 3. Right to erasure - Right to be forgotten
     */
    async deleteUserData(userId: string): Promise<void> {
        const client = await pool.connect();

        try {
            await client.query("BEGIN");

            // Delete personal data
            const encryption = new EncryptionService();
            const anonymousId = `anon_${crypto.randomUUID()}`;

            // Anonymize rather than delete (might be needed for audit trail)
            await client.query(
                `UPDATE auth.users
         SET email = $1, first_name = 'Deleted', last_name = 'User',
             phone_number = NULL, status = 'deleted', updated_at = NOW()
         WHERE id = $2`,
                [anonymousId, userId]
            );

            // Delete session data
            await client.query(`DELETE FROM auth.sessions WHERE user_id = $1`, [
                userId,
            ]);

            // Delete learning session transcripts
            await client.query(
                `DELETE FROM learning.learning_sessions WHERE learner_id IN (
          SELECT id FROM learning.learners WHERE user_id = $1
        )`,
                [userId]
            );

            // Log deletion for compliance
            await client.query(
                `INSERT INTO compliance.data_deletion_log (user_id, deleted_at, reason)
         VALUES ($1, NOW(), 'Right to erasure request')`,
                [userId]
            );

            await client.query("COMMIT");
        } catch (error) {
            await client.query("ROLLBACK");
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Data Processing Agreement (DPA) tracking
     */
    async recordDPA(organizationId: string, dpaContent: string): Promise<void> {
        const hash = crypto
            .createHash("sha256")
            .update(dpaContent)
            .digest("hex");

        await pool.query(
            `UPDATE organizations.orgs
       SET ndpr_dpa_signed = true, dpa_signed_date = NOW(), dpa_content_hash = $1
       WHERE id = $2`,
            [hash, organizationId]
        );

        // Log for audit trail
        await pool.query(
            `INSERT INTO compliance.audit_log (action, org_id, timestamp)
       VALUES ('DPA_SIGNED', $1, NOW())`,
            [organizationId]
        );
    }

    /**
     * Breach notification
     */
    async reportDataBreach(
        learnersAffected: string[],
        breachDetails: string,
        mitigationSteps: string
    ): Promise<void> {
        // Log breach internally
        await pool.query(
            `INSERT INTO compliance.data_breach_log (learners_affected, details, mitigation, timestamp)
       VALUES ($1, $2, $3, NOW())`,
            [JSON.stringify(learnersAffected), breachDetails, mitigationSteps]
        );

        // Notify users
        for (const learnerId of learnersAffected) {
            await notificationService.sendEmail(learnerId, {
                subject: "Important: Data Security Notification",
                template: "data_breach_notification",
                context: {
                    mitigationSteps,
                    supportContact: "security@elitecoach.ai",
                },
            });
        }

        // Alert security team
        logger.error("DATA BREACH REPORTED", {
            affectedCount: learnersAffected.length,
            details: breachDetails,
            timestamp: new Date(),
        });
    }
}
```

---

## Complete OpenAPI Specification

Here's the beginning of a comprehensive OpenAPI 3.0 spec for all services:

```yaml
# openapi.yaml

openapi: 3.0.3
info:
    title: Elite Coach AI API
    description: AI-Powered Professional Skills Training Platform
    version: 1.0.0
    contact:
        name: Elite Coach Support
        email: api-support@elitecoach.ai
    license:
        name: Proprietary
        url: https://elitecoach.ai/license

servers:
    - url: https://api.elitecoach.ai/api/v1
      description: Production
    - url: https://staging-api.elitecoach.ai/api/v1
      description: Staging
    - url: http://localhost:8000/api/v1
      description: Local development

components:
    securitySchemes:
        BearerAuth:
            type: http
            scheme: bearer
            bearerFormat: JWT
        CookieAuth:
            type: apiKey
            in: cookie
            name: refreshToken

    schemas:
        Error:
            type: object
            properties:
                error:
                    type: object
                    properties:
                        code:
                            type: string
                            example: VALIDATION_ERROR
                        message:
                            type: string
                            example: Validation failed
                        details:
                            type: object
                        timestamp:
                            type: string
                            format: date-time
                        requestId:
                            type: string
                            format: uuid

        User:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                email:
                    type: string
                    format: email
                firstName:
                    type: string
                lastName:
                    type: string
                userType:
                    type: string
                    enum: [learner, tutor, org_admin, super_admin]
                organizationId:
                    type: string
                    format: uuid
                    nullable: true
                createdAt:
                    type: string
                    format: date-time
                updatedAt:
                    type: string
                    format: date-time

        Course:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                title:
                    type: string
                description:
                    type: string
                domain:
                    type: string
                difficultyLevel:
                    type: string
                    enum: [beginner, intermediate, advanced]
                durationHours:
                    type: number
                    format: float
                skillsCovered:
                    type: array
                    items:
                        type: string
                status:
                    type: string
                    enum: [draft, published, archived]
                createdAt:
                    type: string
                    format: date-time
                publishedAt:
                    type: string
                    format: date-time
                    nullable: true

        LearningSession:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                learnerId:
                    type: string
                    format: uuid
                courseId:
                    type: string
                    format: uuid
                startedAt:
                    type: string
                    format: date-time
                endedAt:
                    type: string
                    format: date-time
                    nullable: true
                durationMinutes:
                    type: integer
                escalated:
                    type: boolean
                transcript:
                    type: array
                    items:
                        type: object
                        properties:
                            role:
                                type: string
                                enum: [learner, ai, tutor]
                            content:
                                type: string
                            timestamp:
                                type: string
                                format: date-time

        Organization:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                industry:
                    type: string
                country:
                    type: string
                planTier:
                    type: string
                    enum: [starter, growth, enterprise, institutional]
                activeLearnersCount:
                    type: integer
                maxLearners:
                    type: integer
                ndprDpaSigned:
                    type: boolean

    parameters:
        pageParam:
            name: page
            in: query
            schema:
                type: integer
                default: 1
            description: Page number (1-indexed)

        limitParam:
            name: limit
            in: query
            schema:
                type: integer
                default: 20
                maximum: 100
            description: Items per page

        sortParam:
            name: sort
            in: query
            schema:
                type: string
                default: -createdAt
            description: Sort field with optional - prefix for descending

paths:
    /auth/register:
        post:
            tags: [Authentication]
            summary: Register new user
            requestBody:
                required: true
                content:
                    application/json:
                        schema:
                            type: object
                            required:
                                [email, password, firstName, lastName, userType]
                            properties:
                                email:
                                    type: string
                                    format: email
                                password:
                                    type: string
                                    minLength: 12
                                    description: Must contain uppercase, lowercase, number, special char
                                firstName:
                                    type: string
                                    minLength: 2
                                lastName:
                                    type: string
                                    minLength: 2
                                userType:
                                    type: string
                                    enum: [learner, tutor]
            responses:
                "201":
                    description: User registered successfully
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    userId:
                                        type: string
                                        format: uuid
                                    token:
                                        type: string
                                    refreshToken:
                                        type: string
                                    expiresIn:
                                        type: integer
                "400":
                    description: Validation error or user already exists
                    content:
                        application/json:
                            schema:
                                $ref: "#/components/schemas/Error"
                "409":
                    description: Email already registered
                    content:
                        application/json:
                            schema:
                                $ref: "#/components/schemas/Error"

    /auth/login:
        post:
            tags: [Authentication]
            summary: Login user
            requestBody:
                required: true
                content:
                    application/json:
                        schema:
                            type: object
                            required: [email, password]
                            properties:
                                email:
                                    type: string
                                    format: email
                                password:
                                    type: string
            responses:
                "200":
                    description: Login successful
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    userId:
                                        type: string
                                        format: uuid
                                    token:
                                        type: string
                                    refreshToken:
                                        type: string
                                    user:
                                        $ref: "#/components/schemas/User"
                "401":
                    description: Invalid credentials
                "429":
                    description: Too many login attempts

    /auth/refresh:
        post:
            tags: [Authentication]
            summary: Refresh access token
            security:
                - CookieAuth: []
            requestBody:
                required: true
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                refreshToken:
                                    type: string
            responses:
                "200":
                    description: Token refreshed
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    token:
                                        type: string
                                    expiresIn:
                                        type: integer

    /learning/sessions:
        post:
            tags: [Learning]
            summary: Start new learning session
            security:
                - BearerAuth: []
            requestBody:
                required: true
                content:
                    application/json:
                        schema:
                            type: object
                            required: [learnerId, courseId]
                            properties:
                                learnerId:
                                    type: string
                                    format: uuid
                                courseId:
                                    type: string
                                    format: uuid
                                moduleId:
                                    type: string
                                    format: uuid
                                    nullable: true
            responses:
                "201":
                    description: Session started
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    sessionId:
                                        type: string
                                        format: uuid
                                    aiGreeting:
                                        type: string
                                    currentModule:
                                        type: object

    /learning/sessions/{sessionId}/message:
        post:
            tags: [Learning]
            summary: Send message in learning session
            security:
                - BearerAuth: []
            parameters:
                - name: sessionId
                  in: path
                  required: true
                  schema:
                      type: string
                      format: uuid
            requestBody:
                required: true
                content:
                    application/json:
                        schema:
                            type: object
                            required: [message]
                            properties:
                                message:
                                    type: string
                                    minLength: 1
                                    maxLength: 5000
                                messageType:
                                    type: string
                                    enum: [question, answer, feedback]
                                    default: question
            responses:
                "200":
                    description: Response generated
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    sessionId:
                                        type: string
                                    aiResponse:
                                        type: string
                                    escalated:
                                        type: boolean
                                    escalationReason:
                                        type: string
                                        nullable: true

    /courses:
        get:
            tags: [Courses]
            summary: List courses
            parameters:
                - $ref: "#/components/parameters/pageParam"
                - $ref: "#/components/parameters/limitParam"
                - name: domain
                  in: query
                  schema:
                      type: string
                - name: difficulty
                  in: query
                  schema:
                      type: string
                      enum: [beginner, intermediate, advanced]
                - name: search
                  in: query
                  schema:
                      type: string
            responses:
                "200":
                    description: List of courses
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    courses:
                                        type: array
                                        items:
                                            $ref: "#/components/schemas/Course"
                                    total:
                                        type: integer
                                    page:
                                        type: integer
                                    totalPages:
                                        type: integer

        post:
            tags: [Courses]
            summary: Create new course
            security:
                - BearerAuth: []
            requestBody:
                required: true
                content:
                    application/json:
                        schema:
                            type: object
                            required: [title, domain, difficulty]
                            properties:
                                title:
                                    type: string
                                description:
                                    type: string
                                domain:
                                    type: string
                                difficulty:
                                    type: string
                                skillsTaught:
                                    type: array
                                    items:
                                        type: string
            responses:
                "201":
                    description: Course created
                "403":
                    description: Insufficient permissions

    /organizations:
        post:
            tags: [Enterprise]
            summary: Create organization
            security:
                - BearerAuth: []
            requestBody:
                required: true
                content:
                    application/json:
                        schema:
                            type: object
                            required: [name, planTier, adminUserId]
                            properties:
                                name:
                                    type: string
                                industry:
                                    type: string
                                country:
                                    type: string
                                planTier:
                                    type: string
                                    enum:
                                        [
                                            starter,
                                            growth,
                                            enterprise,
                                            institutional,
                                        ]
            responses:
                "201":
                    description: Organization created
                    content:
                        application/json:
                            schema:
                                $ref: "#/components/schemas/Organization"

    /organizations/{organizationId}/dashboard:
        get:
            tags: [Enterprise]
            summary: Get organization dashboard
            security:
                - BearerAuth: []
            parameters:
                - name: organizationId
                  in: path
                  required: true
                  schema:
                      type: string
                      format: uuid
            responses:
                "200":
                    description: Dashboard data
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    activeLearners:
                                        type: integer
                                    completionRate:
                                        type: number
                                    averageScore:
                                        type: number
                                    courseProgress:
                                        type: array
                                        items:
                                            type: object
                "403":
                    description: Access denied

security:
    - BearerAuth: []

tags:
    - name: Authentication
      description: User authentication and authorization
    - name: Learning
      description: Learning sessions and AI tutor
    - name: Courses
      description: Course management
    - name: Assessments
      description: Quizzes and exams
    - name: Enterprise
      description: Organization and team management
    - name: Notifications
      description: User notifications
```

---

## Project Repository Structure

```
elite-coach-ai/
├── services/
│   ├── auth-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   │   └── authController.ts
│   │   │   ├── services/
│   │   │   │   ├── authService.ts
│   │   │   │   ├── mfaService.ts
│   │   │   │   └── samlService.ts
│   │   │   ├── middleware/
│   │   │   │   ├── authentication.ts
│   │   │   │   └── authorization.ts
│   │   │   ├── routes/
│   │   │   │   └── auth.routes.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── index.ts (entry point)
│   │   ├── tests/
│   │   │   ├── auth.test.ts
│   │   │   ├── mfa.test.ts
│   │   │   └── saml.test.ts
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── jest.config.js
│   │   └── .env.example
│   │
│   ├── learning-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   │   └── learningController.ts
│   │   │   ├── services/
│   │   │   │   ├── ragEngine.ts
│   │   │   │   ├── learningPathEngine.ts
│   │   │   │   └── sessionService.ts
│   │   │   ├── middleware/
│   │   │   ├── routes/
│   │   │   │   └── learning.routes.ts
│   │   │   └── index.ts
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── .env.example
│   │
│   ├── course-service/
│   ├── assessment-service/
│   ├── enterprise-service/
│   ├── notification-service/
│   ├── analytics-service/
│   ├── tutor-service/
│   └── career-service/
│
├── api-gateway/
│   ├── kong/
│   │   ├── kong.conf
│   │   ├── config/
│   │   │   ├── routes.yml
│   │   │   ├── services.yml
│   │   │   └── plugins.yml
│   │   └── Dockerfile
│   └── docs/
│       └── gateway-setup.md
│
├── shared/
│   ├── types/
│   │   ├── errors.ts
│   │   ├── models.ts
│   │   └── events.ts
│   ├── utils/
│   │   ├── logger.ts
│   │   ├── encryption.ts
│   │   ├── validation.ts
│   │   └── retry.ts
│   ├── middleware/
│   │   ├── errorHandler.ts
│   │   ├── authentication.ts
│   │   └── logging.ts
│   └── package.json
│
├── database/
│   ├── migrations/
│   │   ├── V1.0__initial_schema.sql
│   │   ├── V1.1__add_learning_paths.sql
│   │   ├── V1.2__add_indexes.sql
│   │   └── ... (flyway versioned)
│   ├── seeds/
│   │   ├── courses.seed.sql
│   │   └── tutors.seed.sql
│   └── flyway.conf
│
├── kubernetes/
│   ├── namespaces.yaml
│   ├── secrets.yaml
│   ├── configmaps.yaml
│   ├── services/
│   │   ├── auth-service-deployment.yaml
│   │   ├── learning-service-deployment.yaml
│   │   └── ... (one per service)
│   ├── ingress.yaml
│   ├── network-policies.yaml
│   └── monitoring/
│       ├── prometheus.yaml
│       ├── grafana.yaml
│       └── alerts.yaml
│
├── docker-compose.yml (local development)
├── .github/workflows/
│   ├── test.yaml
│   ├── build.yaml
│   ├── deploy-staging.yaml
│   └── deploy-production.yaml
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
│
├── .env.example
├── .gitignore
├── README.md
└── package.json (monorepo root)
```

---

## Development Workflow & Setup Guide

### 1. Local Development Setup (First Time)

```bash
# Clone repository
git clone https://github.com/elitecoachglobal/elitecoach-platform.git
cd elitecoach-platform

# Install dependencies for services
npm install
cd services/auth-service && npm install
cd ../learning-service && npm install
# ... repeat for all services

# Set up environment
cp .env.example .env.local
# Edit .env.local with your values

# Start services
docker-compose -f docker-compose.yml up -d

# Run migrations
npm run migrate:dev

# Start development servers
npm run dev
```

### 2. Environment Configuration

```bash
# .env.example

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/delitecoach_dev
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-secret-key-min-32-characters
JWT_REFRESH_SECRET=your-refresh-secret-key-min-32-characters

# OpenAI
OPENAI_API_KEY=sk-...

# Pinecone (Vector DB)
PINECONE_API_KEY=...
PINECONE_ENV=gcp-starter

# Message Queue
AMQP_URL=amqp://guest:guest@localhost:5672

# Email
RESEND_API_KEY=re_...
SENDGRID_API_KEY=SG....

# SMS/WhatsApp
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+...

# SAML SSO
SAML_ENTRY_POINT=https://...
SAML_CERT=...
SAML_ORG_ID=...

# Security
ENCRYPTION_KEY=... (hex format, 64 chars for aes-256)
HASH_SALT=...
CORS_ORIGINS=http://localhost:3000,https://app.elitecoach.ai

# Environment
NODE_ENV=development
LOG_LEVEL=debug
```

### 3. Testing Workflow

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# E2E tests (API)
npm run test:e2e

# Coverage report
npm run test:coverage

# Watch mode for development
npm run test:watch
```

### 4. Code Quality & Git Workflow

```bash
# Pre-commit hooks
npm run husky:install

# Lint code
npm run lint
npm run lint:fix

# Format code
npm run format

# Type check
npm run typecheck

# Git workflow (feature branch)
git checkout -b feature/add-user-export
# ... make changes
git add .
git commit -m "feat: add user data export functionality"
git push origin feature/add-user-export
# Create PR, request review
```

---

## Implementation Checklist

### Phase 0 (PoC) - Weeks 1-8

-   [ ] **Week 1: Foundation Setup**

    -   [ ] Repository structure created & GitHub configured
    -   [ ] Docker development environment working
    -   [ ] PostgreSQL schema initialized
    -   [ ] Auth Service basic scaffolding
    -   [ ] Learning Service basic scaffolding

-   [ ] **Week 2: Auth Service - MVP**

    -   [ ] User registration endpoint
    -   [ ] User login endpoint
    -   [ ] JWT token generation & validation
    -   [ ] Token refresh endpoint
    -   [ ] Unit tests for auth flow

-   [ ] **Week 3: Learning Service - RAG Setup**

    -   [ ] OpenAI API integration
    -   [ ] Pinecone vector DB setup
    -   [ ] RAG pipeline implemented
    -   [ ] Test with one sample course

-   [ ] **Week 4: Course Service - Basic**

    -   [ ] POST /courses endpoint
    -   [ ] Course publish endpoint
    -   [ ] Content chunk storage
    -   [ ] Embedding generation

-   [ ] **Week 5: Learning Sessions**

    -   [ ] Start session endpoint
    -   [ ] Message handling endpoint
    -   [ ] Session transcript storage
    -   [ ] End session & summary

-   [ ] **Week 6: Assessment & Escalation**

    -   [ ] Assessment submission
    -   [ ] Escalation trigger logic
    -   [ ] Tutor queue structure
    -   [ ] Basic escalation tests

-   [ ] **Week 7: Testing & Integration**

    -   [ ] Full PoC integration test
    -   [ ] Stress testing with 20 concurrent users
    -   [ ] Latency benchmarks
    -   [ ] Error scenarios

-   [ ] **Week 8: Deployment & Sign-off**
    -   [ ] PoC environment setup
    -   [ ] Production readiness checklist
    -   [ ] Security audit
    -   [ ] Sign-off meeting with stakeholders

### Phase 1 (MVP) - Weeks 9-24

-   [ ] **Weeks 9-11: Scale Learning & Assessment**

    -   [ ] Session persistence optimization
    -   [ ] Batch assessment processing
    -   [ ] Certificate generation
    -   [ ] Load testing (500 concurrent users)

-   [ ] **Weeks 12-14: Enterprise Service**

    -   [ ] Organization CRUD
    -   [ ] Team management
    -   [ ] Learner import (CSV)
    -   [ ] Course assignment engine
    -   [ ] RBAC implementation

-   [ ] **Weeks 15-17: Enterprise Admin Portal API**

    -   [ ] Dashboard endpoints
    -   [ ] Progress aggregation
    -   [ ] Report generation
    -   [ ] Budget tracking

-   [ ] **Weeks 18-20: Notifications & Communication**

    -   [ ] Email integration (Resend)
    -   [ ] WhatsApp integration (Twilio)
    -   [ ] Notification preferences
    -   [ ] Engagement triggers

-   [ ] **Weeks 21-22: Analytics & Reporting**

    -   [ ] Metrics collection
    -   [ ] Dashboard data aggregation
    -   [ ] Report export (PDF/Excel)
    -   [ ] Real-time metrics

-   [ ] **Weeks 23-24: Production Deployment & Launch**
    -   [ ] Kubernetes setup
    -   [ ] CI/CD pipeline
    -   [ ] SSL/TLS certificates
    -   [ ] NDPR audit
    -   [ ] Enterprise pilot launch

### Phase 2 Prep

-   [ ] Mobile app API routes
-   [ ] ML-based path personalization
-   [ ] Mentorship marketplace
-   [ ] Multi-language support
-   [ ] Offline mode architecture

---

## Success Metrics & Monitoring

**Track these KPIs from Day 1:**

```
API Performance:
├── Avg response time < 500ms (p95 < 2.5s for AI)
├── Error rate < 0.1%
├── Uptime > 99.9%
└── AI escalation rate < 20%

Business Metrics:
├── Course completion rate > 65%
├── Learner NPS > 7.5/10
├── Assessment pass rate > 70%
├── User retention (30-day) > 60%
└── Active learners growth rate > 10% MoM

Infrastructure:
├── Database query time < 100ms (p95)
├── Cache hit rate > 80%
├── CPU utilization < 70%
└── Memory utilization < 75%
```

---

**End of Backend Implementation Documentation**

This comprehensive guide provides everything needed to build Elite Coach AI's microservices backend. Teams should use this as the authoritative source for implementation decisions, architecture patterns, and operational standards.
