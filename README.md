# File Storage API

A single-user file storage web platform that allows uploading files via external URLs or direct browser upload, storing them in Google Cloud Storage (GCS) with JWT-based authentication.

## Features

### Phase 2 - Authentication & Access Control ✅

- **JWT-based Authentication**: Secure login with Bearer token authorization
- **Single-user System**: Predefined username/password authentication
- **Access Control**: Private files require authentication, public files accessible to all
- **Session Management**: 1-hour JWT token expiration with client-side storage

### Core File Operations

- **Upload Methods**:
  - External URL upload: Fetch and store files from web URLs
  - Direct browser upload: Upload files directly from user's device
- **File Management**: List, download, rename, delete, and toggle privacy
- **Storage Organization**:
  - `private/` folder: Authentication required for access
  - `public/` folder: Anonymous access allowed
- **Size Limits**: Configurable max file size (default: 200MB)

## Technology Stack

- **Backend**: FastAPI (Python 3.13)
- **Authentication**: JWT with PyJWT, SHA256 password hashing
- **Storage**: Google Cloud Storage (GCS)
- **Deployment**: Google App Engine (GAE) Standard Environment

## Project Structure

```
project-root/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints
│   │   └── files.py         # File management endpoints
│   ├── services/            # Business logic (future phases)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT and authentication utilities
│   │   └── gcs_client.py    # Google Cloud Storage client
│   └── __init__.py
├── app.yaml                 # GAE configuration
├── requirements.txt         # Python dependencies
├── README.md
└── TEST.md                  # Testing setup guide
```

## Environment Variables

Configure these environment variables for authentication and GCS:

### Required for Production
- `USERNAME`: Admin username (default: "admin")
- `PASSWORD_HASH`: SHA256 hash of password
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `GCP_PROJECT`: Google Cloud Project ID
- `GCS_BUCKET`: Google Cloud Storage bucket name

### Optional/Development
- `JWT_EXPIRATION_DELTA`: Token expiration time (default: 1 hour)

## API Endpoints

### Authentication
- `POST /auth/login` - Authenticate and receive JWT token
- `POST /auth/logout` - Logout (client-side token removal)
- `GET /auth/me` - Get current user information

### File Operations (Authentication Required)
- `POST /api/upload/url` - Upload file from external URL
- `POST /api/upload/direct` - Upload file directly from browser
- `GET /api/files` - List all files (with optional `is_public` filter)
- `POST /api/rename/{file_id}` - Rename file (specify `is_public` query param)
- `POST /api/share/{file_id}` - Toggle between private/public (specify `current_is_public` query param)  
- `DELETE /api/files/{file_id}` - Delete file (specify `is_public` query param)

### File Download (Conditional Authentication)
- `GET /api/download/{file_id}` - Download file
  - Public files: No authentication required
  - Private files: Requires valid JWT token

## Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (optional for development):
   ```bash
   export USERNAME="admin"
   export PASSWORD_HASH="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # SHA256 of "password"
   export JWT_SECRET_KEY="your-secret-key-change-this-in-production"
   export GCP_PROJECT="your-project-id"
   export GCS_BUCKET="your-bucket-name"
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
   ```

3. **Run development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Authentication Flow

### Login Process
1. **Authenticate**:
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "password"}'
   ```
   
   Response:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "expires_in": 3600
   }
   ```

2. **Use Token in Requests**:
   ```bash
   curl -X GET "http://localhost:8000/api/files" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

### Password Hash Generation
For production, generate SHA256 hash of your password:
```python
import hashlib
password = "your-secure-password"
password_hash = hashlib.sha256(password.encode()).hexdigest()
print(password_hash)  # Use this value for PASSWORD_HASH env var
```

## Google Cloud Setup

### 1. Create GCS Bucket
```bash
gsutil mb gs://your-bucket-name
```

### 2. Set up bucket structure
The application expects these folders in your GCS bucket:
- `private/` - Files requiring authentication
- `public/` - Files accessible without authentication

### 3. Configure IAM
Ensure your service account has the following permissions:
- `storage.objects.create`
- `storage.objects.delete`
- `storage.objects.get`
- `storage.objects.list`

## Deployment to Google App Engine

1. **Configure app.yaml**:
   Update the environment variables in `app.yaml`:
   ```yaml
   runtime: python313
   entrypoint: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

   env_variables:
     USERNAME: "admin"
     PASSWORD_HASH: "your-sha256-hash"
     JWT_SECRET_KEY: "your-secret-key"
     GCP_PROJECT: "your-project-id"
     GCS_BUCKET: "your-bucket-name"
   ```

2. **Deploy**:
   ```bash
   gcloud app deploy
   ```

## File Size Limits

- Default maximum file size: 200MB
- Configurable in the GCS client utility functions
- GAE request timeout applies to upload operations

## Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `401` - Authentication required/invalid
- `404` - File not found
- `409` - File already exists (for uploads and renames)
- `413` - File too large
- `500` - Server error (GCS issues, etc.)

## Security Features

- **HTTPS**: Enforced by GAE managed TLS certificates
- **JWT Authentication**: Secure token-based authentication
- **Password Security**: SHA256 hashed passwords stored in environment variables
- **Access Control**: Granular private/public file access control
- **Token Expiration**: 1-hour JWT token expiration for security
- **CORS**: Configured for secure web application integration

## Development Phases

- ✅ **Phase 1**: Core Logic (file operations, GCS integration)
- ✅ **Phase 2**: Authentication & Access Control (current implementation)
- 🔄 **Phase 3**: End-to-End AES Encryption (planned)
- 🔄 **Cloud Phase**: Production deployment optimizations (planned)

## Notes

- Single-user system designed for personal file storage
- JWT tokens are stateless - logout is handled client-side
- File IDs are used as object names in GCS (with folder prefixes)
- Default development credentials: username "admin", password "password"
- For production, always use strong passwords and proper environment variable configuration