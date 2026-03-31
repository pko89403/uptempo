# REST API Design Patterns Reference

## Resource Naming Conventions

| Pattern | Example | Notes |
|---------|---------|-------|
| Plural nouns | `/users`, `/orders` | Always plural for collections |
| Nested resources | `/users/{id}/orders` | Max 2 levels deep |
| Action sub-resources | `/orders/{id}/cancel` | POST for non-CRUD actions |
| Kebab-case paths | `/user-profiles` | Never camelCase in URLs |
| Singular for singletons | `/users/{id}/profile` | One-to-one child resource |

## HTTP Method Semantics

| Method | Idempotent | Safe | Request Body | Typical Status |
|--------|-----------|------|-------------|----------------|
| GET | ✅ | ✅ | No | 200 |
| POST | ❌ | ❌ | Yes | 201 / 202 |
| PUT | ✅ | ❌ | Yes (full) | 200 / 204 |
| PATCH | ❌* | ❌ | Yes (partial) | 200 / 204 |
| DELETE | ✅ | ❌ | No | 204 |

*PATCH can be idempotent with JSON Merge Patch (RFC 7396).

## Pagination Patterns

### Cursor-Based (preferred for large/real-time datasets)
```
GET /items?cursor=eyJpZCI6MTAwfQ&limit=25
→ { "data": [...], "next_cursor": "eyJpZCI6MTI1fQ", "has_more": true }
```

### Offset-Based (simpler, acceptable for small datasets)
```
GET /items?offset=50&limit=25
→ { "data": [...], "total": 200, "offset": 50, "limit": 25 }
```

## Error Response Format (RFC 7807)

```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "Field 'email' must be a valid email address.",
  "instance": "/users/signup",
  "errors": [
    { "field": "email", "message": "Invalid format", "code": "INVALID_EMAIL" }
  ]
}
```

Content-Type: `application/problem+json`

## Content Negotiation & Versioning

| Strategy | Example | Trade-off |
|----------|---------|-----------|
| URL path | `/v1/users` | Simple but breaks URIs |
| Accept header | `Accept: application/vnd.api+json;version=2` | Clean but harder to test |
| Query param | `/users?version=2` | Easy but unconventional |
| Custom header | `API-Version: 2024-01-15` | Date-based, flexible |

Prefer **date-based header versioning** for new APIs (Stripe pattern).

## Rate Limiting Headers

```
X-RateLimit-Limit: 1000         # Max requests per window
X-RateLimit-Remaining: 742      # Remaining in current window
X-RateLimit-Reset: 1620000000   # Unix epoch when window resets
Retry-After: 30                 # Seconds to wait (on 429 response)
```

Return `429 Too Many Requests` with `Retry-After` header when limit exceeded.

### Sliding Window Algorithm
- More fair than fixed windows
- Use Redis `ZRANGEBYSCORE` for distributed rate limiting
- Return `X-RateLimit-Policy: 1000;w=3600` to describe policy

## Quick Checklist

- [ ] Use plural nouns for collection resources
- [ ] Return `Location` header on `201 Created`
- [ ] Support `ETag` / `If-None-Match` for caching
- [ ] Use `406 Not Acceptable` for unsupported media types
- [ ] Document with OpenAPI 3.1 (JSON Schema alignment)
- [ ] Always return consistent envelope or use RFC 7807 for errors
