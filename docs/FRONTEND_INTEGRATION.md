# Frontend Integration Documentation - Elite Coach AI

This guide provides frontend developers with the necessary information to integrate with the Elite Coach AI Backend API.

## 1. General Information

- **Base URL**: `http://localhost:8000/api/v1` (Development)
- **Complete API Spec**: A list of all 100+ endpoints can be found in the [Full API Specification](./FULL_API_SPECIFICATION.md).
- **Interactive JSON Examples**: Detailed request/response examples for core learner workflows are in the [Frontend API Reference](./FRONTEND_API_REFERENCE.md).
- **Swagger Documentation**: The auto-generated docs are available at `/docs` (Swagger UI).
- **Content Type**: `application/json`
- **Authentication**: Bearer Token (JWT)

---

## 2. Authentication Flow

### User Registration
- **Endpoint**: `POST /auth/register`
- **Full Specification**: [Auth Details](./FULL_API_SPECIFICATION.md#1-authentication--identity-apiv1auth)
- **Restriction**: Creating a `platform_admin` via this endpoint is **blocked**.

### Login & Session Management
- **Login**: `POST /auth/login` (Standard OAuth2 password grant). 
- **Refresh**: `POST /auth/refresh`
- **Me**: `GET /auth/me` to get current profile and roles.

---

## 3. Role-Based Access Control (RBAC)

The system uses specific roles to control access. Always check the `roles` array in the JWT payload (via decode) or in the user profile before rendering protected UI components.

| Role | Frontend Access/View | Reference |
| :--- | :--- | :--- |
| `solo_learner` | Standard student dashboard, course catalog, AI tutor. | [Onboarding](./FULL_API_SPECIFICATION.md#2-onboarding--adaptive-paths-apiv1onboarding) |
| `org_learner` | Learner dashboard with organization-specific branding. | [Enterprise](./FULL_API_SPECIFICATION.md#10-enterprise-dashboard-apiv1enterprise) |
| `tutor_author` | Content Management System (CMS) to create lessons. | [Tutor CMS](./FULL_API_SPECIFICATION.md#9-tutor-cms-content-management-apiv1cms) |
| `tutor_responder` | Message Inbox for handling student escalations. | [Tutor Inbox](./FULL_API_SPECIFICATION.md#8-tutor-expert-inbox-apiv1inbox) |
| `enterprise_admin` | Team management and organization analytics. | [Enterprise Dashboard](./FULL_API_SPECIFICATION.md#10-enterprise-dashboard-apiv1enterprise) |
| `platform_admin` | Global settings and user moderation. | [Platform Admin](./FULL_API_SPECIFICATION.md#11-platform-administration-apiv1admin) |

---

## 4. Feature Workflows

### AI Tutor Integration
1. **Initialize Session**: `POST /learning/lesson/{id}/start`
2. **Chat**: `POST /ai/chat`
3. **Handle Response**:
    - `reply`: The markdown content for the chat bubble.
    - `is_escalated`: If `true`, the UI should switch to "Escalation" mode (show wait times).
- **Reference**: [AI Tutor Spec](./FULL_API_SPECIFICATION.md#4-ai-tutor-experience-apiv1ai)

### Adaptive Onboarding
1. Send user preferences to `/onboarding/start`.
2. Present the returned questions.
3. Submit answers to `/onboarding/submit`.
4. Render the returned `items` (Learning Path) as the user's course list.
- **Reference**: [Onboarding Spec](./FRONTEND_API_REFERENCE.md#2-onboarding--diagnostics-onboarding)

### Payments & Subscription
1. User chooses a plan -> `POST /payments/subscribe`.
2. Frontend redirects to the returned `authorization_url`.
3. After payment, Paystack redirects back to the frontend.
4. Call `GET /payments/status` to unlock learning content.
- **Reference**: [Payment Spec](./FRONTEND_API_REFERENCE.md#7-payments-payments)

---

## 5. Common Patterns & Best Practices

### Error Handling
- **401 Unauthorized**: Redirect to login, clear local storage.
- **403 Forbidden**: Show "Access Denied" overlay.
- **422 Unprocessable Entity**: Validation error (typically for forms). Use the `detail` array to show field-specific errors.

### Media Uploads
For avatars or CMS content, use the `Cloudinary` integrated endpoints:
- `POST /users/avatar`
- `POST /tutor-cms/upload`

### Pagination
List endpoints use `limit` and `offset` query parameters.
Example: `GET /courses?limit=10&offset=20`

---
*For backend-specific logic, refer to the [Technical Documentation](../TECHNICAL_DOCUMENTATION.md).*
