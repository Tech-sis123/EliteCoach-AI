# Elite Coach AI - Backend Implementation Documentation

## Part 2: Authentication, Error Handling, Monitoring & Deployment

---

## Authentication & Authorization

### JWT Implementation Strategy

**Token Structure:**

```typescript
// Access Token (8-hour expiry)
{
  "sub": "user-uuid",
  "role": "learner|tutor|org_admin|super_admin",
  "organization_id": "org-uuid",
  "email": "user@example.com",
  "iat": 1713000000,
  "exp": 1713028800,
  "iss": "elitecoach.ai",
  "aud": "elitecoach-api"
}

// Refresh Token (30-day expiry, issued separately)
{
  "sub": "user-uuid",
  "type": "refresh",
  "jti": "token-id-uuid", // Unique token ID for blacklisting
  "iat": 1713000000,
  "exp": 1715592000,
  "iss": "elitecoach.ai"
}
```

**Implementation:**

```typescript
// src/services/authService.ts

import jwt from "jsonwebtoken";
import crypto from "crypto";
import { pool } from "../db";

export class AuthService {
    private jwtSecret = process.env.JWT_SECRET!;
    private refreshSecret = process.env.JWT_REFRESH_SECRET!;

    // Generate token pair
    async generateTokenPair(
        userId: string,
        role: string,
        organizationId?: string
    ) {
        const accessToken = this.generateAccessToken(
            userId,
            role,
            organizationId
        );
        const refreshToken = this.generateRefreshToken(userId);

        // Store refresh token in database for revocation management
        const jti = crypto.randomUUID();
        await pool.query(
            `INSERT INTO auth.sessions (user_id, token_id, refresh_token, expires_at)
       VALUES ($1, $2, $3, to_timestamp($4))`,
            [
                userId,
                jti,
                refreshToken,
                Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60,
            ]
        );

        return {
            accessToken,
            refreshToken,
            expiresIn: 8 * 60 * 60, // 8 hours in seconds
            tokenType: "Bearer",
        };
    }

    // Generate access token
    private generateAccessToken(
        userId: string,
        role: string,
        organizationId?: string
    ): string {
        return jwt.sign(
            {
                sub: userId,
                role,
                organization_id: organizationId,
                iat: Math.floor(Date.now() / 1000),
            },
            this.jwtSecret,
            {
                expiresIn: "8h",
                issuer: "elitecoach.ai",
                audience: "elitecoach-api",
                algorithm: "HS256",
            }
        );
    }

    // Generate refresh token
    private generateRefreshToken(userId: string): string {
        return jwt.sign(
            {
                sub: userId,
                type: "refresh",
                iat: Math.floor(Date.now() / 1000),
            },
            this.refreshSecret,
            {
                expiresIn: "30d",
                issuer: "elitecoach.ai",
                algorithm: "HS256",
            }
        );
    }

    // Verify and refresh tokens
    async refreshAccessToken(refreshToken: string): Promise<string> {
        try {
            // Verify refresh token signature
            const decoded = jwt.verify(refreshToken, this.refreshSecret) as any;

            // Check if token is blacklisted
            const tokenRecord = await pool.query(
                "SELECT * FROM auth.sessions WHERE refresh_token = $1 AND expires_at > NOW()",
                [refreshToken]
            );

            if (tokenRecord.rows.length === 0) {
                throw new Error("Refresh token not found or expired");
            }

            // Get user details for new access token
            const userResult = await pool.query(
                "SELECT id, role, organization_id FROM auth.users WHERE id = $1",
                [decoded.sub]
            );

            if (userResult.rows.length === 0) {
                throw new Error("User not found");
            }

            const user = userResult.rows[0];
            return this.generateAccessToken(
                user.id,
                user.role,
                user.organization_id
            );
        } catch (error) {
            throw new Error(`Token refresh failed: ${error.message}`);
        }
    }

    // Verify token
    verifyToken(token: string): any {
        try {
            return jwt.verify(token, this.jwtSecret) as any;
        } catch (error) {
            throw new Error(`Token verification failed: ${error.message}`);
        }
    }

    // Logout (blacklist refresh token)
    async logout(refreshToken: string): Promise<void> {
        await pool.query("DELETE FROM auth.sessions WHERE refresh_token = $1", [
            refreshToken,
        ]);
    }
}
```

### Role-Based Access Control (RBAC)

**Role Hierarchy:**

```
super_admin
  ├─ Full platform access
  ├─ User management
  └─ Platform configuration

org_admin
  ├─ Organization settings
  ├─ Team management
  ├─ Course assignments
  └─ Reports/Dashboard access

tutor
  ├─ View escalations
  ├─ Submit responses
  ├─ Upload content
  └─ View their students' progress

learner
  ├─ Enroll in courses
  ├─ Access learning sessions
  └─ View own progress
```

**Permission Matrix:**

```typescript
const permissionMatrix = {
    super_admin: {
        organizations: ["create", "read", "update", "delete"],
        users: ["create", "read", "update", "delete"],
        courses: ["create", "read", "update", "delete", "publish"],
        analytics: ["read", "export"],
        tutors: ["manage", "approve"],
        platform: ["configure", "monitor"],
    },
    org_admin: {
        organization: ["read", "update"], // Own organization only
        teams: ["create", "read", "update", "delete"],
        learners: ["import", "read", "update"],
        courses: ["assign", "read"],
        analytics: ["read", "export"],
        reports: ["generate", "read"],
    },
    tutor: {
        escalations: ["read", "update"],
        learners: ["read"], // Assigned to them
        sessions: ["read"],
        content: ["submit", "update", "delete"], // Own content
        responses: ["submit"],
    },
    learner: {
        courses: ["read", "enroll"],
        sessions: ["create", "read", "update"],
        assessments: ["read", "submit"],
        profile: ["read", "update"], // Own profile
        certificates: ["read", "download"],
    },
};
```

**Middleware Implementation:**

```typescript
// src/middleware/authorization.ts

export function requireRole(...allowedRoles: string[]) {
    return (req: Request, res: Response, next: NextFunction) => {
        if (!req.user) {
            return res.status(401).json({ error: "Unauthorized" });
        }

        if (!allowedRoles.includes(req.user.role)) {
            return res.status(403).json({
                error: "Forbidden",
                requiredRoles: allowedRoles,
                userRole: req.user.role,
            });
        }

        next();
    };
}

export function requirePermission(resource: string, action: string) {
    return async (req: Request, res: Response, next: NextFunction) => {
        if (!req.user) {
            return res.status(401).json({ error: "Unauthorized" });
        }

        const userPermissions = permissionMatrix[req.user.role];
        const resourcePermissions = userPermissions[resource];

        if (!resourcePermissions || !resourcePermissions.includes(action)) {
            return res.status(403).json({
                error: "Forbidden",
                resource,
                action,
                availableActions: resourcePermissions || [],
            });
        }

        next();
    };
}

// Usage in routes
app.get(
    "/api/v1/organizations/:orgId/dashboard",
    authenticateToken,
    requirePermission("analytics", "read"),
    organizationController.getDashboard
);

app.post(
    "/api/v1/users",
    authenticateToken,
    requireRole("super_admin"),
    userController.createUser
);
```

### Enterprise SSO - SAML 2.0

```typescript
// src/services/samlService.ts

import * as passport from "passport";
import * as SamlStrategy from "passport-saml";

export class SAMLService {
    configureStrategy() {
        passport.use(
            new SamlStrategy.Strategy(
                {
                    path: "/auth/sso/saml/callback",
                    entryPoint: process.env.SAML_ENTRY_POINT,
                    issuer: "elitecoach-ai",
                    cert: process.env.SAML_CERT,
                    identifierFormat:
                        "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                },
                async (profile: any, done: Function) => {
                    try {
                        // Extract email from SAML profile
                        const email = profile.nameID;

                        // Check if user exists
                        let user = await pool.query(
                            "SELECT * FROM auth.users WHERE email = $1",
                            [email]
                        );

                        if (user.rows.length === 0) {
                            // Auto-create user on first SAML login (if enabled)
                            const newUser = await pool.query(
                                `INSERT INTO auth.users (email, first_name, last_name, user_type, organization_id)
                 VALUES ($1, $2, $3, $4, $5)
                 RETURNING *`,
                                [
                                    email,
                                    profile[
                                        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
                                    ],
                                    profile[
                                        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
                                    ],
                                    "learner",
                                    process.env.SAML_ORG_ID,
                                ]
                            );
                            user = newUser;
                        }

                        return done(null, user.rows[0]);
                    } catch (error) {
                        return done(error);
                    }
                }
            )
        );
    }
}

// SAML routes
app.get("/auth/sso/saml", passport.authenticate("saml"));

app.post(
    "/auth/sso/saml/callback",
    passport.authenticate("saml", { failureRedirect: "/login" }),
    async (req: Request, res: Response) => {
        const user = req.user as any;
        const authService = new AuthService();

        const tokens = await authService.generateTokenPair(
            user.id,
            user.user_type,
            user.organization_id
        );

        // Set secure HTTP-only cookie
        res.cookie("refreshToken", tokens.refreshToken, {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            sameSite: "lax",
            maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
        });

        // Redirect to frontend with access token
        res.redirect(
            `${process.env.FRONTEND_URL}/auth/sso-success?token=${tokens.accessToken}`
        );
    }
);
```

### MFA - Time-based One-Time Password (TOTP)

```typescript
// src/services/mfaService.ts

import speakeasy from "speakeasy";
import QRCode from "qrcode";

export class MFAService {
    // Generate MFA secret and QR code
    async generateMFASecret(userId: string, userEmail: string) {
        const secret = speakeasy.generateSecret({
            name: `Elite Coach (${userEmail})`,
            issuer: "Elite Coach AI",
            length: 32,
        });

        const qrCode = await QRCode.toDataURL(secret.otpauth_url!);

        return {
            secret: secret.base32,
            qrCode,
            manual: secret.otpauth_url,
        };
    }

    // Verify TOTP code
    verifyTOTPCode(secret: string, code: string): boolean {
        return speakeasy.totp.verify({
            secret,
            encoding: "base32",
            token: code,
            window: 2, // Allow 2 time windows (±30 seconds)
        });
    }

    // Generate backup codes
    generateBackupCodes(count: number = 10): string[] {
        const codes: string[] = [];
        for (let i = 0; i < count; i++) {
            codes.push(crypto.randomBytes(4).toString("hex").toUpperCase());
        }
        return codes;
    }

    // Hash and store backup codes
    async storeBackupCodes(userId: string, codes: string[]): Promise<void> {
        const hashedCodes = await Promise.all(
            codes.map((code) => bcrypt.hash(code, 10))
        );

        await pool.query(
            `UPDATE auth.users SET backup_codes = $1 WHERE id = $2`,
            [JSON.stringify(hashedCodes), userId]
        );
    }
}

// MFA enrollment route
app.post(
    "/api/v1/auth/mfa/enable",
    authenticateToken,
    async (req: Request, res: Response) => {
        const user = req.user;
        const mfaService = new MFAService();

        const { secret, qrCode } = await mfaService.generateMFASecret(
            user.userId,
            user.email
        );
        const backupCodes = mfaService.generateBackupCodes();

        // Don't save yet - require verification in next step
        res.json({
            secret,
            qrCode,
            backupCodes,
            setupInstructions: "Scan QR code and enter 6-digit code to confirm",
        });
    }
);

// MFA verification
app.post(
    "/api/v1/auth/mfa/verify",
    authenticateToken,
    async (req: Request, res: Response) => {
        const { code, secret } = req.body;
        const mfaService = new MFAService();

        if (!mfaService.verifyTOTPCode(secret, code)) {
            return res.status(400).json({ error: "Invalid code" });
        }

        // Save MFA secret and backup codes
        const backupCodes = mfaService.generateBackupCodes();
        await mfaService.storeBackupCodes(req.user.userId, backupCodes);

        await pool.query(
            `UPDATE auth.users SET mfa_enabled = true, mfa_secret = $1 WHERE id = $2`,
            [secret, req.user.userId]
        );

        res.json({
            success: true,
            backupCodes,
            message:
                "MFA enabled successfully. Keep these backup codes secure!",
        });
    }
);

// MFA verification during login
app.post(
    "/api/v1/auth/mfa/verify-login",
    async (req: Request, res: Response) => {
        const { email, password, mfaCode } = req.body;

        // First, verify email/password
        const user = await verifyCredentials(email, password);
        if (!user) {
            return res.status(401).json({ error: "Invalid credentials" });
        }

        if (!user.mfa_enabled) {
            // MFA not enabled, issue tokens directly
            const authService = new AuthService();
            const tokens = await authService.generateTokenPair(
                user.id,
                user.user_type
            );
            return res.json(tokens);
        }

        // MFA enabled, verify code
        const mfaService = new MFAService();
        const isValidCode = mfaService.verifyTOTPCode(user.mfa_secret, mfaCode);

        if (!isValidCode) {
            // Try backup code
            const backupCodes = JSON.parse(user.backup_codes || "[]");
            const validBackupCode = await Promise.all(
                backupCodes.map((code) => bcrypt.compare(mfaCode, code))
            ).then((results) => results.some((r) => r));

            if (!validBackupCode) {
                return res.status(401).json({ error: "Invalid MFA code" });
            }

            // Remove used backup code
            const updatedBackupCodes = backupCodes.filter(
                (code) => !bcrypt.compareSync(mfaCode, code)
            );
            await pool.query(
                "UPDATE auth.users SET backup_codes = $1 WHERE id = $2",
                [JSON.stringify(updatedBackupCodes), user.id]
            );
        }

        // Issue tokens
        const authService = new AuthService();
        const tokens = await authService.generateTokenPair(
            user.id,
            user.user_type
        );
        res.json(tokens);
    }
);
```

---

## Error Handling & Resilience

### Standardized Error Response Format

```typescript
// src/types/errors.ts

export interface ErrorResponse {
    error: {
        code: string;
        message: string;
        details?: object;
        timestamp: string;
        requestId: string;
        path: string;
    };
}

export enum ErrorCode {
    // Validation errors (4000-4099)
    VALIDATION_ERROR = "VALIDATION_ERROR",
    INVALID_REQUEST = "INVALID_REQUEST",
    MISSING_FIELD = "MISSING_FIELD",

    // Authentication errors (4010-4039)
    UNAUTHORIZED = "UNAUTHORIZED",
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS",
    TOKEN_EXPIRED = "TOKEN_EXPIRED",
    TOKEN_INVALID = "TOKEN_INVALID",
    MFA_REQUIRED = "MFA_REQUIRED",

    // Authorization errors (4030-4049)
    FORBIDDEN = "FORBIDDEN",
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS",

    // Resource errors (4040-4069)
    NOT_FOUND = "NOT_FOUND",
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT",
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS",

    // Business logic errors (4100-4199)
    COURSE_NOT_PUBLISHED = "COURSE_NOT_PUBLISHED",
    ASSESSMENT_ALREADY_SUBMITTED = "ASSESSMENT_ALREADY_SUBMITTED",
    LEARNER_NOT_ENROLLED = "LEARNER_NOT_ENROLLED",
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED",

    // Rate limiting (4290-4299)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED",
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS",

    // Server errors (5000-5999)
    INTERNAL_ERROR = "INTERNAL_ERROR",
    DATABASE_ERROR = "DATABASE_ERROR",
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE",
    TIMEOUT = "TIMEOUT",
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR",
}

export class AppError extends Error {
    constructor(
        public code: ErrorCode,
        public statusCode: number,
        message: string,
        public details?: object
    ) {
        super(message);
        this.name = "AppError";
    }
}
```

**Error Handling Middleware:**

```typescript
// src/middleware/errorHandler.ts

import { Request, Response } from "express";
import { AppError, ErrorCode } from "../types/errors";

export function errorHandler(err: any, req: Request, res: Response) {
    const requestId = req.id || crypto.randomUUID();
    const timestamp = new Date().toISOString();

    let appError: AppError;

    if (err instanceof AppError) {
        appError = err;
    } else if (err.code === "EBADCSRFTOKEN") {
        appError = new AppError(
            ErrorCode.INVALID_REQUEST,
            400,
            "Invalid CSRF token"
        );
    } else if (err instanceof SyntaxError && "body" in err) {
        appError = new AppError(
            ErrorCode.INVALID_REQUEST,
            400,
            "Invalid JSON in request body"
        );
    } else if (err.name === "ValidationError") {
        appError = new AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "Validation failed",
            err.details
        );
    } else {
        // Unknown error
        console.error("Unhandled error:", err);
        appError = new AppError(
            ErrorCode.INTERNAL_ERROR,
            500,
            "An unexpected error occurred"
        );
    }

    const response = {
        error: {
            code: appError.code,
            message: appError.message,
            details: appError.details,
            timestamp,
            requestId,
            path: req.path,
        },
    };

    // Log the error
    logger.error({
        requestId,
        error: appError,
        statusCode: appError.statusCode,
        method: req.method,
        path: req.path,
        userId: req.user?.userId,
    });

    res.status(appError.statusCode).json(response);
}
```

### Resilience Patterns

**Retry with Exponential Backoff:**

```typescript
// src/utils/retry.ts

export async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    options = {
        maxRetries: 3,
        initialDelayMs: 100,
        multiplier: 2,
        maxDelayMs: 10000,
        shouldRetry: (error: any) => true,
    }
): Promise<T> {
    let lastError: any;

    for (let i = 0; i < options.maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;

            if (!options.shouldRetry(error)) {
                throw error;
            }

            if (i < options.maxRetries - 1) {
                const delayMs = Math.min(
                    options.initialDelayMs * Math.pow(options.multiplier, i),
                    options.maxDelayMs
                );
                await new Promise((resolve) => setTimeout(resolve, delayMs));
            }
        }
    }

    throw lastError;
}

// Usage
async function fetchCourseWithRetry(courseId: string) {
    return retryWithBackoff(() => courseService.getCourse(courseId), {
        maxRetries: 3,
        shouldRetry: (error) => error.statusCode >= 500, // Retry on server errors
    });
}
```

**Timeout Pattern:**

```typescript
// src/utils/timeout.ts

export function withTimeout<T>(
    promise: Promise<T>,
    timeoutMs: number,
    timeoutMessage: string = "Operation timed out"
): Promise<T> {
    return Promise.race([
        promise,
        new Promise<T>((_, reject) =>
            setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs)
        ),
    ]);
}

// Usage
async function processLearnerSession(sessionId: string) {
    try {
        const result = await withTimeout(
            this.generateAIResponse(sessionId),
            2500, // 2.5 second limit for AI response
            "AI response generation timed out"
        );
        return result;
    } catch (error) {
        if (error.message.includes("timed out")) {
            throw new AppError(
                ErrorCode.TIMEOUT,
                504,
                "Response generation took too long. Please try again."
            );
        }
        throw error;
    }
}
```

**Bulkhead Pattern (Resource Isolation):**

```typescript
// src/utils/bulkhead.ts

export class Bulkhead {
    private activeRequests = 0;
    private waitingQueue: Array<() => void> = [];

    constructor(private maxConcurrent: number) {}

    async execute<T>(fn: () => Promise<T>): Promise<T> {
        while (this.activeRequests >= this.maxConcurrent) {
            await new Promise((resolve) => this.waitingQueue.push(resolve));
        }

        this.activeRequests++;

        try {
            return await fn();
        } finally {
            this.activeRequests--;
            const next = this.waitingQueue.shift();
            if (next) next();
        }
    }
}

// Usage - limit AI inference concurrency
const aiBulkhead = new Bulkhead(10); // Max 10 concurrent AI requests

async function generateAIResponse(message: string) {
    return aiBulkhead.execute(() =>
        openaiClient.createChatCompletion({
            messages: [{ role: "user", content: message }],
        })
    );
}
```

---

## Monitoring & Observability

### Logging Strategy

```typescript
// src/utils/logger.ts

import winston from "winston";
import ElasticsearchTransport from "winston-elasticsearch";

const logger = winston.createLogger({
    defaultMeta: { service: "elitecoach-learning-service" },
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    transports: [
        // Console in development
        ...(process.env.NODE_ENV === "development"
            ? [
                  new winston.transports.Console({
                      format: winston.format.combine(
                          winston.format.colorize(),
                          winston.format.simple()
                      ),
                  }),
              ]
            : []),

        // File transport
        new winston.transports.File({
            filename: "logs/error.log",
            level: "error",
        }),
        new winston.transports.File({
            filename: "logs/combined.log",
        }),

        // Elasticsearch transport (centralized logging)
        ...(process.env.ELASTICSEARCH_URL
            ? [
                  new ElasticsearchTransport({
                      level: "info",
                      clientOpts: { node: process.env.ELASTICSEARCH_URL },
                      index: "elitecoach-logs",
                  }),
              ]
            : []),
    ],
});

export default logger;
```

**Structured Logging:**

```typescript
// Examples of structured logging

// API request
logger.info("API request received", {
    requestId: req.id,
    method: req.method,
    path: req.path,
    userId: req.user?.userId,
    queryParams: req.query,
    timestamp: new Date(),
});

// AI inference
logger.info("AI response generated", {
    sessionId,
    learnerId,
    model: "gpt-4o",
    inputTokens: 245,
    outputTokens: 189,
    latencyMs: 1240,
    escalated: false,
    timestamp: new Date(),
});

// Database query
logger.debug("Database query executed", {
    query: "SELECT * FROM learning.enrollments WHERE learner_id = $1",
    duration: 42,
    rowsAffected: 5,
    timestamp: new Date(),
});

// Error
logger.error("Assessment submission failed", {
    error: err.message,
    stack: err.stack,
    submissionId,
    learnerId,
    statusCode: 500,
    timestamp: new Date(),
});
```

### Metrics & Monitoring

```typescript
// src/utils/metrics.ts

import client from "prom-client";

// Application metrics
export const httpRequestDuration = new client.Histogram({
    name: "http_request_duration_seconds",
    help: "Duration of HTTP requests in seconds",
    labelNames: ["method", "route", "status_code"],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
});

export const aiResponseLatency = new client.Histogram({
    name: "ai_response_latency_ms",
    help: "AI response generation latency in milliseconds",
    labelNames: ["model", "status"],
    buckets: [100, 500, 1000, 1500, 2000, 2500],
});

export const learnerSessions = new client.Counter({
    name: "learner_sessions_total",
    help: "Total learner sessions",
    labelNames: ["course", "completion_status"],
});

export const assessmentSubmissions = new client.Counter({
    name: "assessment_submissions_total",
    help: "Total assessment submissions",
    labelNames: ["assessment_type", "status"],
});

export const enrollments = new client.Gauge({
    name: "active_enrollments",
    help: "Number of active enrollments",
    labelNames: ["course", "organization"],
});

export const escalations = new client.Counter({
    name: "ai_escalations_total",
    help: "Total AI escalations to human tutors",
    labelNames: ["reason"],
});

// Middleware to track HTTP requests
export function metricsMiddleware(
    req: Request,
    res: Response,
    next: NextFunction
) {
    const startTime = Date.now();

    res.on("finish", () => {
        const duration = (Date.now() - startTime) / 1000;
        httpRequestDuration
            .labels(req.method, req.route?.path || req.path, res.statusCode)
            .observe(duration);
    });

    next();
}

// Metrics endpoint (for Prometheus scraping)
app.get("/metrics", async (req, res) => {
    try {
        res.set("Content-Type", client.register.contentType);
        const metrics = await client.register.metrics();
        res.end(metrics);
    } catch (error) {
        res.status(500).end(error);
    }
});
```

### Distributed Tracing

```typescript
// src/middleware/tracing.ts

import { trace, context } from "@opentelemetry/api";
import { NodeTracerProvider } from "@opentelemetry/node";
import { registerInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { JaegerExporter } from "@opentelemetry/exporter-jaeger";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";

// Set up Jaeger exporter
const jaegerExporter = new JaegerExporter({
    serviceName: "elitecoach-learning-service",
    host: process.env.JAEGER_HOST || "localhost",
    port: parseInt(process.env.JAEGER_PORT || "6831"),
});

const nodeTracerProvider = new NodeTracerProvider();
nodeTracerProvider.addSpanProcessor(new BatchSpanProcessor(jaegerExporter));
nodeTracerProvider.register();

registerInstrumentations();

const tracer = trace.getTracer("elitecoach-learning-service");

// Middleware to add tracing
export function tracingMiddleware(
    req: Request,
    res: Response,
    next: NextFunction
) {
    const span = tracer.startSpan(`${req.method} ${req.path}`);

    context.with(trace.setSpan(context.active(), span), () => {
        span.setAttributes({
            "http.method": req.method,
            "http.target": req.path,
            "http.client_ip": req.ip,
        });

        res.on("finish", () => {
            span.setAttribute("http.status_code", res.statusCode);
            span.end();
        });

        next();
    });
}

// Tracing for service calls
export async function traceServiceCall<T>(
    serviceName: string,
    operationName: string,
    fn: () => Promise<T>
): Promise<T> {
    const span = tracer.startSpan(`${serviceName}.${operationName}`);

    return context.with(trace.setSpan(context.active(), span), async () => {
        try {
            const result = await fn();
            span.setStatus({ code: SpanStatusCode.OK });
            return result;
        } catch (error) {
            span.recordException(error as Error);
            span.setStatus({ code: SpanStatusCode.ERROR });
            throw error;
        } finally {
            span.end();
        }
    });
}
```

### Alerting

```yaml
# prometheus/alerts.yml

groups:
    - name: elitecoach-alerts
      interval: 1m
      rules:
          # AI response latency
          - alert: HighAILatency
            expr: histogram_quantile(0.95, ai_response_latency_ms) > 2500
            for: 5m
            annotations:
                summary: "AI response latency exceeds 2.5 seconds"
                severity: "warning"

          # Service errors
          - alert: HighErrorRate
            expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
            for: 5m
            annotations:
                summary: "Error rate exceeds 5%"
                severity: "critical"

          # Escalation rate
          - alert: HighEscalationRate
            expr: rate(ai_escalations_total[5m]) > 0.20
            for: 10m
            annotations:
                summary: "AI escalation rate exceeds 20%"
                severity: "warning"

          # Database connection pool
          - alert: DatabaseConnectionPoolExhausted
            expr: postgres_connections_used / postgres_connections_max > 0.9
            for: 2m
            annotations:
                summary: "Database connection pool 90% utilized"
                severity: "critical"
```

---

## Deployment Strategy

### Docker Configuration

**Dockerfile for Microservice:**

```dockerfile
# Multi-stage build

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies and build
RUN npm ci && npm run build

#Stage 2: Runtime
FROM node:20-alpine

WORKDIR /app

# Install dumb-init (for PID 1 and signal handling)
RUN apk add --no-cache dumb-init

# Copy built application
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Use dumb-init to handle signals
ENTRYPOINT ["dumb-init", "--"]

# Start application
CMD ["node", "dist/index.js"]

EXPOSE 3000
```

**Docker Compose for Local Development:**

```yaml
version: "3.8"

services:
    postgres:
        image: postgres:15-alpine
        environment:
            POSTGRES_DB: ${DB_NAME}
            POSTGRES_USER: ${DB_USER}
            POSTGRES_PASSWORD: ${DB_PASSWORD}
        ports:
            - "5432:5432"
        volumes:
            - postgres_data:/var/lib/postgresql/data
            - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
        healthcheck:
            test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
            interval: 10s
            timeout: 5s
            retries: 5

    redis:
        image: redis:7-alpine
        ports:
            - "6379:6379"
        healthcheck:
            test: ["CMD", "redis-cli", "ping"]
            interval: 10s
            timeout: 5s
            retries: 5

    auth-service:
        build:
            context: ./services/auth
            dockerfile: Dockerfile
        environment:
            NODE_ENV: development
            DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
            REDIS_URL: redis://redis:6379
            JWT_SECRET: ${JWT_SECRET}
            JWT_REFRESH_SECRET: ${JWT_REFRESH_SECRET}
        ports:
            - "3001:3000"
        depends_on:
            postgres:
                condition: service_healthy
            redis:
                condition: service_healthy
        volumes:
            - ./services/auth/src:/app/src

    learning-service:
        build:
            context: ./services/learning
            dockerfile: Dockerfile
        environment:
            NODE_ENV: development
            DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
            REDIS_URL: redis://redis:6379
            OPENAI_API_KEY: ${OPENAI_API_KEY}
            PINECONE_API_KEY: ${PINECONE_API_KEY}
            AMQP_URL: amqp://rabbitmq:5672
        ports:
            - "3002:3000"
        depends_on:
            - postgres
            - redis
        volumes:
            - ./services/learning/src:/app/src

    rabbitmq:
        image: rabbitmq:3.12-management-alpine
        ports:
            - "5672:5672"
            - "15672:15672"
        environment:
            RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
            RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
        healthcheck:
            test: ["CMD", "rabbitmq-diagnostics", "ping"]
            interval: 10s
            timeout: 5s
            retries: 5

    kong:
        image: kong:3.3-alpine
        environment:
            KONG_DATABASE: postgres
            KONG_PG_HOST: postgres
            KONG_PG_USER: ${DB_USER}
            KONG_PG_PASSWORD: ${DB_PASSWORD}
            KONG_PROXY_ACCESS_LOG: /dev/stdout
            KONG_ADMIN_ACCESS_LOG: /dev/stdout
            KONG_PROXY_ERROR_LOG: /dev/stderr
            KONG_ADMIN_ERROR_LOG: /dev/stderr
        ports:
            - "8000:8000" # Proxy
            - "8001:8001" # Admin API
        depends_on:
            - postgres

volumes:
    postgres_data:
```

### Kubernetes Deployment

**Service Deployment Manifest:**

```yaml
# kubernetes/learning-service-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
    name: learning-service
    namespace: elitecoach

spec:
    replicas: 3

    selector:
        matchLabels:
            app: learning-service

    template:
        metadata:
            labels:
                app: learning-service
                version: v1

        spec:
            serviceAccountName: learning-service

            containers:
                - name: learning-service
                  image: ${REGISTRY}/elitecoach/learning-service:${VERSION}
                  imagePullPolicy: IfNotPresent

                  ports:
                      - containerPort: 3000
                        name: http
                      - containerPort: 9090
                        name: metrics

                  env:
                      - name: NODE_ENV
                        value: "production"
                      - name: DATABASE_URL
                        valueFrom:
                            secretKeyRef:
                                name: db-credentials
                                key: url
                      - name: REDIS_URL
                        value: "redis://redis-service:6379"
                      - name: OPENAI_API_KEY
                        valueFrom:
                            secretKeyRef:
                                name: ai-credentials
                                key: openai-key
                      - name: PINECONE_API_KEY
                        valueFrom:
                            secretKeyRef:
                                name: vector-db-credentials
                                key: pinecone-key
                      - name: AMQP_URL
                        value: "amqp://rabbitmq-service:5672"

                  resources:
                      requests:
                          memory: "256Mi"
                          cpu: "250m"
                      limits:
                          memory: "512Mi"
                          cpu: "500m"

                  livenessProbe:
                      httpGet:
                          path: /health
                          port: 3000
                      initialDelaySeconds: 15
                      periodSeconds: 20

                  readinessProbe:
                      httpGet:
                          path: /ready
                          port: 3000
                      initialDelaySeconds: 10
                      periodSeconds: 10

                  securityContext:
                      runAsNonRoot: true
                      runAsUser: 1001
                      readOnlyRootFilesystem: true
                      allowPrivilegeEscalation: false

            securityContext:
                fsGroup: 1001

            affinity:
                podAntiAffinity:
                    preferredDuringSchedulingIgnoredDuringExecution:
                        - weight: 100
                          podAffinityTerm:
                              labelSelector:
                                  matchExpressions:
                                      - key: app
                                        operator: In
                                        values:
                                            - learning-service
                              topologyKey: kubernetes.io/hostname

---
apiVersion: v1
kind: Service
metadata:
    name: learning-service
    namespace: elitecoach

spec:
    selector:
        app: learning-service

    type: ClusterIP

    ports:
        - name: http
          port: 80
          targetPort: 3000
        - name: metrics
          port: 9090
          targetPort: 9090

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
    name: learning-service-hpa
    namespace: elitecoach

spec:
    scaleTargetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: learning-service

    minReplicas: 3
    maxReplicas: 10

    metrics:
        - type: Resource
          resource:
              name: cpu
              target:
                  type: Utilization
                  averageUtilization: 70
        - type: Resource
          resource:
              name: memory
              target:
                  type: Utilization
                  averageUtilization: 80

    behavior:
        scaleDown:
            stabilizationWindowSeconds: 300
            policies:
                - type: Percent
                  value: 50
                  periodSeconds: 60
        scaleUp:
            stabilizationWindowSeconds: 0
            policies:
                - type: Percent
                  value: 100
                  periodSeconds: 30
```

**Database Migration (Flyway):**

```yaml
# Database migrations automated via Flyway

db/migration/
├── V1.0__initial_schema.sql
├── V1.1__add_learning_paths.sql
├── V1.2__add_indexes.sql
├── V1.3__add_notifications.sql
└── V2.0__add_vector_support.sql
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/service-deployment.yaml

name: Deploy Microservice

on:
    push:
        branches: [main, develop]
        paths:
            - "services/learning-service/**"
            - ".github/workflows/service-deployment.yaml"

env:
    REGISTRY: ghcr.io
    SERVICE_NAME: learning-service

jobs:
    build:
        runs-on: ubuntu-latest

        permissions:
            contents: read
            packages: write

        steps:
            - uses: actions/checkout@v3

            - name: Set up Docker Buildx
              uses: docker/setup-buildx-action@v2

            - name: Log in to Container Registry
              uses: docker/login-action@v2
              with:
                  registry: ${{ env.REGISTRY }}
                  username: ${{ github.actor }}
                  password: ${{ secrets.GITHUB_TOKEN }}

            - name: Extract metadata
              id: meta
              uses: docker/metadata-action@v4
              with:
                  images: ${{ env.REGISTRY }}/${{ github.repository_owner }}/${{ env.SERVICE_NAME }}
                  tags: |
                      type=ref,event=branch
                      type=semver,pattern={{version}}
                      type=sha,prefix={{branch}}-

            - name: Build and push
              uses: docker/build-push-action@v4
              with:
                  context: ./services/${{ env.SERVICE_NAME }}
                  push: true
                  tags: ${{ steps.meta.outputs.tags }}
                  labels: ${{ steps.meta.outputs.labels }}
                  cache-from: type=registry,ref=${{ steps.meta.outputs.tags[0] }}
                  cache-to: type=inline

    test:
        runs-on: ubuntu-latest

        services:
            postgres:
                image: postgres:15-alpine
                env:
                    POSTGRES_PASSWORD: postgres
                options: >-
                    --health-cmd pg_isready
                    --health-interval 10s
                    --health-timeout 5s
                    --health-retries 5
                ports:
                    - 5432:5432

        steps:
            - uses: actions/checkout@v3

            - name: Set up Node.js
              uses: actions/setup-node@v3
              with:
                  node-version: "20"
                  cache: "npm"
                  cache-dependency-path: "services/${{ env.SERVICE_NAME }}/package-lock.json"

            - name: Install dependencies
              working-directory: services/${{ env.SERVICE_NAME }}
              run: npm ci

            - name: Run tests
              working-directory: services/${{ env.SERVICE_NAME }}
              env:
                  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
              run: npm test

            - name: Run linting
              working-directory: services/${{ env.SERVICE_NAME }}
              run: npm run lint

            - name: Upload coverage
              uses: codecov/codecov-action@v3
              with:
                  files: ./services/${{ env.SERVICE_NAME }}/coverage/lcov.info
```

---

This backend implementation guide provides a complete foundation for building the Elite Coach AI microservices. Continue to the next section for final API specifications and deployment checklist.
