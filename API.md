# File Storage API Documentation

This document provides comprehensive API documentation for the File Storage Web Platform. The API supports both web interface routes (HTML pages) and REST API endpoints for programmatic access.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-app-id.appspot.com` (when deployed to Google App Engine)

## Authentication

The API uses JWT (JSON Web Token) authentication with Bearer token authorization. All file operations require authentication except for public file downloads.

### Authentication Flow

1. Obtain JWT token via `/auth/login`
2. Include token in `Authorization: Bearer <token>` header for protected endpoints
3. Tokens expire after 1 hour (3600 seconds)

---

## Web Interface Routes

These endpoints return HTML pages for the interactive web interface.

### `GET /`
**Home Page**

Returns the main page with file upload interface.

**Response**: HTML page with upload forms

---

### `GET /login`
**Login Page**

Returns the authentication page.

**Response**: HTML login form

---

### `GET /files`
**File Management Interface**

Returns the file management interface (requires authentication via browser session).

**Response**: HTML page with file listing and management controls

---

### `GET /admin`
**Administrative Controls**

Returns the administrative interface (requires authentication via browser session).

**Response**: HTML page with admin controls

---

### `GET /download/private/{file_id}`
**Private File Download Page**

Returns a download page for private files (requires authentication via browser session).

**Parameters:**
- `file_id` (path) - The ID of the file to download

**Response**: HTML download page

---

### `GET /download/public/{file_id}`
**Public File Download Page**

Returns a download page for public files (no authentication required).

**Parameters:**
- `file_id` (path) - The ID of the file to download

**Response**: HTML download page

---

## Authentication API

### `POST /auth/login`
**User Login**

Authenticate user and receive JWT access token.

**Content-Type**: `application/x-www-form-urlencoded`

**Request Body** (Form Data):
```
username=admin&password=your-password
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials

**Example:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password"
```

---

### `POST /auth/logout`
**User Logout**

Logout user (token invalidation is handled client-side).

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

### `GET /auth/me`
**Get Current User**

Get information about the currently authenticated user.

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "username": "admin"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

## File Operations API

All file operations require authentication via JWT token in the Authorization header.

### `POST /api/upload/url`
**Upload File from URL**

Upload a file by providing an external URL.

**Headers**: 
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body**:
```json
{
  "url": "https://example.com/file.pdf",
  "file_id": "my-document",
  "is_public": false
}
```

**Parameters:**
- `url` (required) - External URL to fetch file from
- `file_id` (optional) - Custom file ID. If not provided, extracted from URL or generates UUID
- `is_public` (optional, default: false) - Whether file should be publicly accessible

**Response** (200 OK):
```json
{
  "file_id": "my-document",
  "object_path": "private/my-document",
  "size": 1024576,
  "is_public": false
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `409 Conflict` - File with same ID already exists
- `413 Request Entity Too Large` - File exceeds size limit (200MB)
- `500 Internal Server Error` - Upload failed

**Example:**
```bash
curl -X POST "http://localhost:8000/api/upload/url" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://httpbin.org/json",
       "file_id": "test-file",
       "is_public": false
     }'
```

---

### `POST /api/upload/direct`
**Direct File Upload**

Upload a file directly from client device.

**Headers**: `Authorization: Bearer <token>`
**Content-Type**: `multipart/form-data`

**Request Body** (Form Data):
- `file` (required) - File to upload
- `file_id` (optional) - Custom file ID. If not provided, uses original filename or generates UUID
- `is_public` (optional, default: false) - Whether file should be publicly accessible

**Response** (200 OK):
```json
{
  "file_id": "document.pdf",
  "object_path": "private/document.pdf",
  "size": 1024576,
  "is_public": false,
  "original_filename": "document.pdf"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `409 Conflict` - File with same ID already exists
- `413 Request Entity Too Large` - File exceeds size limit (200MB)
- `500 Internal Server Error` - Upload failed

**Example:**
```bash
curl -X POST "http://localhost:8000/api/upload/direct" \
     -H "Authorization: Bearer <token>" \
     -F "file=@document.pdf" \
     -F "file_id=my-document" \
     -F "is_public=false"
```

---

### `GET /api/files`
**List Files**

Get a list of all files with optional filtering by public/private status.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters:**
- `is_public` (optional) - Filter by public (true) or private (false) files. Omit to show all files.

**Response** (200 OK):
```json
[
  {
    "file_id": "document.pdf",
    "object_path": "private/document.pdf",
    "size": 1024576,
    "is_public": false
  },
  {
    "file_id": "image.jpg",
    "object_path": "public/image.jpg",
    "size": 512000,
    "is_public": true
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `500 Internal Server Error` - Failed to list files

**Example:**
```bash
# List all files
curl -X GET "http://localhost:8000/api/files" \
     -H "Authorization: Bearer <token>"

# List only private files
curl -X GET "http://localhost:8000/api/files?is_public=false" \
     -H "Authorization: Bearer <token>"

# List only public files
curl -X GET "http://localhost:8000/api/files?is_public=true" \
     -H "Authorization: Bearer <token>"
```

---

## File Download API

### `GET /api/download/private/{file_id}`
### `HEAD /api/download/private/{file_id}`
**Download Private File**

Download or get information about a private file. Requires authentication.

**Headers**: `Authorization: Bearer <token>`

**Parameters:**
- `file_id` (path) - The ID of the file to download

**Response** (200 OK):
- **GET**: File content as binary stream
- **HEAD**: Headers only with file metadata

**Headers in Response:**
- `Content-Length` - File size in bytes
- `Content-Type` - File MIME type (or application/octet-stream)
- `Content-Disposition` - attachment; filename={file_id}

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - File not found
- `500 Internal Server Error` - Download failed

**Example:**
```bash
# Download file
curl -X GET "http://localhost:8000/api/download/private/document.pdf" \
     -H "Authorization: Bearer <token>" \
     --output document.pdf

# Get file info only (HEAD request)
curl -I "http://localhost:8000/api/download/private/document.pdf" \
     -H "Authorization: Bearer <token>"
```

---

### `GET /api/download/public/{file_id}`
### `HEAD /api/download/public/{file_id}`
**Download Public File**

Download or get information about a public file. No authentication required.

**Parameters:**
- `file_id` (path) - The ID of the file to download

**Response** (200 OK):
- **GET**: File content as binary stream
- **HEAD**: Headers only with file metadata

**Headers in Response:**
- `Content-Length` - File size in bytes
- `Content-Type` - File MIME type (or application/octet-stream)
- `Content-Disposition` - attachment; filename={file_id}

**Error Responses:**
- `404 Not Found` - File not found
- `500 Internal Server Error` - Download failed

**Example:**
```bash
# Download public file (no authentication needed)
curl -X GET "http://localhost:8000/api/download/public/image.jpg" \
     --output image.jpg

# Get public file info only
curl -I "http://localhost:8000/api/download/public/image.jpg"
```

---

### `GET /api/download/{file_id}` (Legacy)
### `HEAD /api/download/{file_id}` (Legacy)
**Download File (Legacy Endpoint)**

Download file using the legacy endpoint with conditional authentication.

**Query Parameters:**
- `is_public` (required) - Whether the file is public (true) or private (false)

**Headers** (conditional):
- `Authorization: Bearer <token>` - Required if is_public=false

**Response**: Same as dedicated endpoints above

**Note**: This endpoint is maintained for backward compatibility. Use the dedicated `/api/download/private/` and `/api/download/public/` endpoints for new integrations.

**Example:**
```bash
# Download private file (requires auth)
curl -X GET "http://localhost:8000/api/download/document.pdf?is_public=false" \
     -H "Authorization: Bearer <token>" \
     --output document.pdf

# Download public file (no auth)
curl -X GET "http://localhost:8000/api/download/image.jpg?is_public=true" \
     --output image.jpg
```

---

### `POST /api/rename/{file_id}`
**Rename File**

Rename an existing file.

**Headers**: 
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Parameters:**
- `file_id` (path) - Current ID of the file to rename

**Query Parameters:**
- `is_public` (required) - Whether the file is public (true) or private (false)

**Request Body**:
```json
{
  "new_file_id": "new-filename.pdf"
}
```

**Response** (200 OK):
```json
{
  "old_file_id": "document.pdf",
  "new_file_id": "new-filename.pdf",
  "object_path": "private/new-filename.pdf",
  "is_public": false
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - Source file not found
- `409 Conflict` - Target filename already exists
- `500 Internal Server Error` - Rename failed

**Example:**
```bash
curl -X POST "http://localhost:8000/api/rename/document.pdf?is_public=false" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"new_file_id": "renamed-document.pdf"}'
```

---

### `POST /api/share/{file_id}`
**Toggle File Privacy**

Toggle a file between private and public access.

**Headers**: `Authorization: Bearer <token>`

**Parameters:**
- `file_id` (path) - ID of the file to toggle

**Query Parameters:**
- `current_is_public` (required) - Current privacy status of the file (true/false)

**Response** (200 OK):
```json
{
  "file_id": "document.pdf",
  "object_path": "public/document.pdf",
  "was_public": false,
  "is_public": true
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - File not found
- `500 Internal Server Error` - Share toggle failed

**Example:**
```bash
# Make private file public
curl -X POST "http://localhost:8000/api/share/document.pdf?current_is_public=false" \
     -H "Authorization: Bearer <token>"

# Make public file private
curl -X POST "http://localhost:8000/api/share/document.pdf?current_is_public=true" \
     -H "Authorization: Bearer <token>"
```

---

### `DELETE /api/files/{file_id}`
**Delete File**

Delete an existing file.

**Headers**: `Authorization: Bearer <token>`

**Parameters:**
- `file_id` (path) - ID of the file to delete

**Query Parameters:**
- `is_public` (required) - Whether the file is public (true) or private (false)

**Response** (200 OK):
```json
{
  "message": "File document.pdf deleted successfully"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - File not found
- `500 Internal Server Error` - Delete failed

**Example:**
```bash
# Delete private file
curl -X DELETE "http://localhost:8000/api/files/document.pdf?is_public=false" \
     -H "Authorization: Bearer <token>"

# Delete public file
curl -X DELETE "http://localhost:8000/api/files/image.jpg?is_public=true" \
     -H "Authorization: Bearer <token>"
```

---

## Error Handling

The API uses standard HTTP status codes:

- **200 OK** - Request successful
- **401 Unauthorized** - Authentication required or invalid
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource already exists (file ID conflicts)
- **413 Request Entity Too Large** - File exceeds size limit (200MB default)
- **500 Internal Server Error** - Server error (GCS issues, etc.)

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Rate Limits

No rate limits are currently implemented, but consider implementing them for production use.

---

## File Size Limits

- **Maximum file size**: 200MB (configurable in `app/utils/gcs_client.py`)
- **Timeout**: GAE request timeout applies to upload operations

---

## CORS Support

The API includes CORS middleware configured to:
- Allow all origins (`*`)
- Allow all methods
- Allow all headers
- Allow credentials

---

## Interactive Documentation

When running the server, interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to test API endpoints directly in your browser with built-in authentication support.

---

## Authentication Examples

### Getting Started

1. **Login to get token**:
```bash
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password" | jq -r '.access_token')
```

2. **Upload a file from URL**:
```bash
curl -X POST "http://localhost:8000/api/upload/url" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://httpbin.org/json",
       "file_id": "test-data",
       "is_public": true
     }'
```

3. **List files**:
```bash
curl -X GET "http://localhost:8000/api/files" \
     -H "Authorization: Bearer $TOKEN"
```

4. **Download the file** (now public):
```bash
curl -X GET "http://localhost:8000/api/download/public/test-data" \
     --output test-data.json
```

### Python Example

```python
import requests

# Login
response = requests.post('http://localhost:8000/auth/login', data={
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Upload file
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'file_id': 'my-doc', 'is_public': 'false'}
    response = requests.post('http://localhost:8000/api/upload/direct', 
                           files=files, data=data, headers=headers)
    print(response.json())

# List files
response = requests.get('http://localhost:8000/api/files', headers=headers)
files = response.json()
print(f"Found {len(files)} files")

# Download file
response = requests.get('http://localhost:8000/api/download/private/my-doc', 
                       headers=headers)
with open('downloaded-doc.pdf', 'wb') as f:
    f.write(response.content)
```

---

## Security Notes

- JWT tokens expire after 1 hour for security
- Private files require authentication for all access
- Public files can be accessed without authentication
- SHA256 password hashing is used for credential storage
- HTTPS is enforced in production (GAE managed TLS)
- File IDs should not contain sensitive information as they appear in URLs

---

## Storage Structure

Files are stored in Google Cloud Storage with the following structure:

```
your-gcs-bucket/
├── private/           # Files requiring authentication
│   ├── document.pdf
│   └── private-data.json
└── public/            # Files accessible without authentication
    ├── image.jpg
    └── public-data.json
```