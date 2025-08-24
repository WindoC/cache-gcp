# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a single-user file storage web platform that allows uploading files via external URLs or direct browser upload and stores them in Google Cloud Storage (GCS). The project uses FastAPI backend with optional end-to-end AES encryption and is designed for deployment on Google App Engine (GAE) Standard Environment.

## Development Phases

The project follows a phased approach:
- **Phase 1**: Core Logic (URL upload, direct browser upload, list, download, rename, delete, private/public folders)
- **Phase 2**: Authentication & Access Control (JWT-based auth)
- **Phase 3**: End-to-End AES Encryption (optional user-supplied key encryption)
- **Cloud Phase**: Deploy to GAE Standard

## Technology Stack

- **Backend**: FastAPI (Python 3.13)
- **Deployment**: Google App Engine (GAE) Standard
- **Storage**: Google Cloud Storage (GCS)
- **Authentication**: JWT (stored client-side in localStorage)
- **Encryption**: AES-GCM (Web Crypto API + Python `cryptography`)

## Project Structure

The application structure should follow this layout per PRD requirements:
```
project-root/
├── app/
│   ├── main.py        # FastAPI entrypoint
│   ├── routes/        # API routes
│   ├── services/      # business logic
│   ├── utils/         # helpers (crypto, GCS client, etc.)
│   └── __init__.py
├── app.yaml           # GAE config
├── requirements.txt
└── README.md
```

**Note**: Core app logic resides in `app/` folder, while project root contains only entry point, config, and dependencies.

## Key API Endpoints

- `POST /login` — Authenticate, return JWT
- `POST /logout` — Invalidate JWT
- `POST /upload/url` — Upload from external URL
- `POST /upload/direct` — Upload file directly from browser (multipart/form-data)
- `GET /files` — List files
- `GET /download/{file_id}` — Download file
- `POST /rename/{file_id}` — Rename file
- `POST /share/{file_id}` — Toggle private/public
- `DELETE /files/{file_id}` — Delete file

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
- `USERNAME` — Admin username
- `PASSWORD_HASH` — SHA256 hash of password
- `AES_KEY_HASH` — SHA256 hash of AES encryption key (Phase 3)
- `GCP_PROJECT` — GCP project ID
- `GCS_BUCKET` — GCS bucket name

## Security Considerations

- HTTPS enforced (GAE provides managed TLS)
- File size limit: 200MB (configurable)
- Optional end-to-end encryption with user-supplied AES key
- GCS IAM with least privilege principles

## Development Commands

Since this is a new project, typical development commands would be:
- `pip install -r requirements.txt` — Install dependencies
- `uvicorn app.main:app --reload` — Run development server
- `pytest` — Run tests (when implemented)

## Deployment

Deploy to GAE using:
- `gcloud app deploy` — Deploy to GAE Standard
- Entry point: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`