# Vaultly API Reference

**API Version:** v1  
**Base URL:** https://api.vaultly.io/v1  
**Last Updated:** March 12, 2025

---

## Authentication

All API requests must include a valid Bearer token in the Authorization header:

```
Authorization: Bearer <your_api_token>
```

API tokens are generated from the Vaultly dashboard under Settings > API Tokens. Tokens do not expire automatically but can be revoked at any time. Each token is scoped to a single workspace.

---

## Rate Limiting

The Vaultly API enforces a rate limit of 120 requests per minute per API token. Requests that exceed this limit receive an HTTP 429 response with a `Retry-After` header indicating how many seconds to wait before retrying.

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

---

## Endpoints

### Upload a Document

```
POST /documents
```

Uploads a new document to the authenticated workspace.

**Request headers:**
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form fields:**
- `file` (required): The document file to upload. Maximum file size is 50 MB.
- `folder_id` (optional): UUID of the target folder. Defaults to root.
- `tags` (optional): Comma-separated list of tags, e.g. `finance,2024`.

**Response 201:**

```json
{
  "id": "doc_8f3a12",
  "filename": "report.pdf",
  "size_bytes": 204800,
  "uploaded_at": "2025-03-12T10:45:00Z"
}
```

**Response 413:** Returned when the uploaded file exceeds 50 MB.

---

### Search Documents

```
GET /search?q=<query>
```

Full-text search across all documents in the authenticated workspace.

**Query parameters:**
- `q` (required): Search query string.
- `folder_id` (optional): Restrict search to a specific folder UUID.
- `page` (optional, default 1): Page number for paginated results.
- `per_page` (optional, default 20, max 100): Results per page.

**Response 200:**

```json
{
  "total": 42,
  "page": 1,
  "results": [
    { "id": "doc_8f3a12", "filename": "report.pdf", "score": 0.94 }
  ]
}
```

---

### Delete a Document

```
DELETE /documents/{document_id}
```

Permanently deletes a document. This action cannot be undone.

**Response 200:**

```json
{ "deleted": true, "id": "doc_8f3a12" }
```

**Response 404:** Returned when the document ID does not exist.

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200  | Success |
| 201  | Resource created |
| 400  | Bad request — malformed body or missing required field |
| 401  | Unauthorized — missing or invalid token |
| 403  | Forbidden — token lacks required permission |
| 413  | Payload too large — file exceeds 50 MB limit |
| 429  | Rate limit exceeded |
| 500  | Internal server error |

---

## SDK Support

Official SDKs are available for Python, JavaScript (Node.js), and Go. Install the Python SDK with:

```bash
pip install vaultly-sdk
```

Full SDK documentation is available at https://docs.vaultly.io/sdk.
