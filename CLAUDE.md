# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a single-user file storage web platform with both interactive web interface and REST API support. It allows uploading files via external URLs or direct browser upload and stores them in Google Cloud Storage (GCS). The project uses FastAPI backend with Jinja2 templates for the web interface, JWT authentication, and is designed for deployment on Google App Engine (GAE) Standard Environment.

## Development Phases

The project follows a phased approach:
- **Phase 1**: Core Logic (URL upload, direct browser upload, list, download, rename, delete, private/public folders) ✅
- **Phase 2**: Authentication & Access Control (JWT-based auth) ✅
- **Phase 3**: End-to-End AES Encryption (mandatory user-supplied key encryption for specific endpoints) ✅
- **Cloud Phase**: Deploy to GAE Standard - *Ready for deployment*

## Technology Stack

- **Backend**: FastAPI (Python 3.13)
- **Frontend**: Jinja2 templates with HTML/JavaScript (Bootstrap styling)
- **Deployment**: Google App Engine (GAE) Standard
- **Storage**: Google Cloud Storage (GCS) 
- **Authentication**: JWT with PyJWT, SHA256 password hashing (passlib with bcrypt)
- **HTTP Client**: Requests library for URL downloads
- **Server**: Uvicorn for development, Gunicorn for production
- **Encryption**: AES-GCM (Web Crypto API + Python `cryptography`) ✅

## Project Structure

The application follows this structure (current implementation):
```
project-root/
├── app/
│   ├── main.py              # FastAPI entrypoint with web routes
│   ├── routes/              # API route modules
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints (/auth/*)
│   │   └── files.py         # File management endpoints (/api/*)
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Base template with navigation
│   │   ├── index.html       # Home/upload page
│   │   ├── login.html       # Authentication page
│   │   ├── files.html       # File management interface
│   │   ├── admin.html       # Administrative controls
│   │   ├── download_private.html  # Private download page
│   │   └── download_public.html   # Public download page
│   ├── services/            # Business logic (empty, reserved for future)
│   ├── utils/               # Helper modules
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT and authentication utilities
│   │   ├── gcs_client.py    # Google Cloud Storage client
│   │   ├── crypto.py        # AES encryption/decryption utilities
│   │   ├── encryption_middleware.py  # Encryption request/response handlers
│   │   └── form_parser.py   # Large form data parser for encrypted uploads
│   └── __init__.py
├── app.yaml                 # GAE configuration
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
├── TEST.md                 # Testing instructions
└── CLAUDE.md              # This file - Claude Code guidance
```

**Note**: Core app logic resides in `app/` folder, while project root contains only configuration, dependencies, and documentation.

## Key Endpoints

### Web Interface (HTML Pages)
- `GET /` — Home page with file upload interface
- `GET /login` — Authentication page
- `GET /files` — File management interface
- `GET /admin` — Administrative controls
- `GET /download/private/{file_id}` — Private file download page
- `GET /download/public/{file_id}` — Public file download page

### Authentication API
- `POST /auth/login` — Authenticate, return JWT (Form data: username, password)
- `POST /auth/logout` — Invalidate JWT (client-side)
- `GET /auth/me` — Get current user information

### File Operations API (Require Authentication)

#### Encryption-Required Endpoints 🔒
These endpoints **ONLY** work with end-to-end encryption:
- `POST /api/upload/url` — Upload from external URL (encrypted_payload only)
- `POST /api/upload/direct` — Upload file directly (encrypted_payload only)
- `GET /api/files` — List files (always returns encrypted response)
- `GET|HEAD /api/download/private/{file_id}` — Download private file (always returns encrypted response)

#### Standard Endpoints  
- `POST /api/rename/{file_id}` — Rename file (JSON: new_file_id; Query: is_public)
- `POST /api/share/{file_id}` — Toggle private/public (Query: current_is_public)
- `DELETE /api/files/{file_id}` — Delete file (Query: is_public)

### File Download API
- `GET|HEAD /api/download/public/{file_id}` — Download public file (no auth)

## GCS Structure

Files are stored in two folders:
- `private/` — Requires authentication
- `public/` — Anonymous access allowed

## Authentication

Single-user system with:
- Predefined username and SHA256-hashed password from environment variables
- JWT tokens issued on login, stored in browser localStorage
- Bearer token authentication for protected endpoints

## Environment Variables

For GAE deployment, configure these in app.yaml:
- `USERNAME` — Admin username (default: "admin")
- `PASSWORD_HASH` — SHA256 hash of password (default dev: SHA256 of "password")
- `JWT_SECRET_KEY` — Secret key for JWT token signing
- `GCP_PROJECT` — GCP project ID
- `GCS_BUCKET` — GCS bucket name
- `AES_KEY_HASH` — SHA256 hash of AES encryption key (Phase 3)

## Security Considerations

- HTTPS enforced (GAE provides managed TLS)
- JWT-based authentication with 1-hour token expiration
- File size limit: 200MB (configurable in `app/utils/gcs_client.py`)
- Encrypted uploads support up to 250MB payload size
- Private/public file access control via GCS folder structure
- SHA256 password hashing with environment variable storage
- CORS middleware configured for web interface integration
- **End-to-end AES-GCM encryption** with user-supplied keys for specific endpoints
- **Encryption-only endpoints** with no fallback to unencrypted mode
- **Mandatory encryption** for sensitive file operations
- GCS IAM with least privilege principles

## Development Commands

Current development workflow:
- `pip install -r requirements.txt` — Install dependencies
- `uvicorn app.main:app --reload` — Run development server with auto-reload
- Access web interface at `http://localhost:8000`
- Access API docs at `http://localhost:8000/docs`
- `pytest` — Run tests (*when implemented*)

## Deployment

Deploy to GAE using:
- `gcloud app deploy` — Deploy to GAE Standard
- Entry point: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`