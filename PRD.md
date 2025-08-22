# Product Requirements Document (PRD)

**Project: Temporary File Storage with Optional End-to-End Encryption**

---

## 1. Overview

### 1.1 Project Summary

This project provides a **single-user** file storage web platform where files are uploaded via **external URLs** or upload file from browser, then stored in **Google Cloud Storage (GCS)** for future download.

* Files persist in GCS until manually deleted.
* Files reside in `private/` (authentication required) or `public/` (anonymous access).
* **Minimal design**: no extra metadata, only GCS object name.

The system evolves through phases:

* **Local testing (pre-cloud):** core features → auth → encryption.
* **Cloud phase:** deploy to **Google App Engine (GAE) Standard Environment**.

### 1.2 Deployment Target

* **Platform:** Google App Engine (GAE) Standard (Python 3.13 runtime)
* **Backend Framework:** FastAPI
* **Storage:** Google Cloud Storage (GCS)
* **Session:** JWT (stored client-side)
* **Encryption:** Optional AES-GCM, user-supplied key

### 1.3 Authentication

* **Phase 1:** no auth (for dev/testing).
* **Phase 2+:** JWT-based session:

  * Single predefined username and SHA256-hashed password (from environment variables).
  * JWT issued upon login; stored in browser localStorage.
  * All private operations require valid JWT.
* **Public files** remain accessible without authentication.

### 1.4 Application Structure

* Core app logic files reside in **`app/` folder**.
* Project root only contains entry point (`main.py`), config (`app.yaml`), and dependency definitions (`requirements.txt`).

---

## 2. Goals

* Provide a secure, minimal, single-user file storage app.
* Enable uploading from external URLs, or upload file from browser
* list/download/delete/rename file.
* Allow toggling between private/public.
* Provide optional end-to-end AES encryption layer.
* Deploy reliably on GAE Standard.

---

## 3. Non-Goals

* Multi-user support.
* Metadata storage (timestamps, counts, etc.).
* File previews or versioning.
* Advanced key management (KMS, PKI).

---

## 4. Phased Development

### Pre-cloud phase (local testing):

* **Phase 1 — Core Logic**

  * Implement file upload, list, download, rename, delete.
  * Implement private/public folder separation.

* **Phase 2 — Authentication & Access Control**

  * JWT-based login/logout.
  * Private vs. public file access enforcement.

* **Phase 3 — End-to-End AES Encryption**

  * Add optional encryption:

    * Frontend requires user-supplied AES key.
    * Store only SHA256 hash in localStorage.
    * Re-prompt user if:

      * Hash not present, or
      * Decryption error occurs.
    * Backend loads AES key SHA256 hash from env vars.
    * Requests/responses encrypted with AES-GCM.

### Cloud phase:

* Deploy to **GAE Standard**.
* Integrate GCS IAM, environment variable management, scaling, HTTPS enforcement.

---

## 5. System Requirements

### 5.1 Technology Stack

* **Backend:** FastAPI (Python 3.13)
* **Deployment:** GAE Standard
* **Storage:** Google Cloud Storage (GCS)
* **Session:** JWT (PyJWT or equivalent)
* **Encryption:** AES-GCM (Web Crypto API + Python `cryptography`)

### 5.2 Functional Requirements

#### 5.2.1 Authentication (Phase 2+)

* User provides username + password.
* Password checked against SHA256 hash stored in env vars.
* On success → backend issues JWT.
* JWT stored in browser localStorage, used in `Authorization: Bearer` headers.
* Token expiry (e.g., 1h). Refresh by re-login.

#### 5.2.2 File Upload

**Method 1: External URL Upload**
* User provides external file URL.
* Backend fetches file, stores in `private/` or `public/`.
* Configurable max file size (default: 200MB).
* Returns object name + file size.

**Method 2: Direct Browser Upload**
* User selects local file via browser file input.
* File uploaded directly from browser to backend.
* Same size limits and storage logic as URL upload.
* Support multipart/form-data uploads.
* Progress indication for large files.

#### 5.2.3 File Listing

* Authenticated users can list files (`private/`, `public/`).
* Show: object name, file size.
* Allow copying download link.

#### 5.2.4 File Download

* **Private files:** require valid JWT.
* **Public files:** available to anyone with link.
* Files streamed directly from GCS.

#### 5.2.5 File Rename

* Authenticated user may rename files (change GCS object name).

#### 5.2.6 Share Toggle

* Authenticated user moves file between `private/` and `public/`.

#### 5.2.7 File Deletion

* Authenticated user deletes files from GCS.

#### 5.2.8 API Endpoints

* `POST /login` — Authenticate, return JWT.
* `POST /logout` — Invalidate JWT (optional).
* `POST /upload` — Upload from external URL.
* `POST /upload/direct` — Upload file directly from browser (multipart/form-data).
* `GET /files` — List files.
* `GET /download/{file_id}` — Download file.
* `POST /rename/{file_id}` — Rename file.
* `POST /share/{file_id}` — Toggle private/public.
* `DELETE /files/{file_id}` — Delete file.

---

## 6. Security & Encryption

### 6.1 Standard Security

* HTTPS (GAE provides managed TLS).
* JWT for session management.
* Strong password hash in env vars.
* GCS IAM least privilege.

### 6.2 End-to-End AES Encryption (Phase 3+)

#### Frontend

* User prompted to input AES key.
* SHA256 hash stored in localStorage.
* If missing or decryption fails → user must re-enter key.
* Payloads encrypted with AES-GCM before sending.

#### Backend

* AES key SHA256 hash stored in environment variables.
* Backend decrypts client payloads using AES-GCM.
* Responses encrypted before sending back.

#### Risks

* User must remember key (no reset).
* Hard-coded/shared key makes system vulnerable if disclosed.
* Protects against HTTPS interception only, not endpoint compromise.

---

## 7. Performance & Scalability

* GCS ensures durability and scale.
* GAE Standard: auto-scaling, scale-to-zero when idle.
* File listing queries GCS directly (acceptable scale for single-user).
* Encryption overhead tolerable for ≤200MB files.

---
## 8. Deployment

### 8.1 Application Structure

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

* `main.py` is inside `app/`.
* GAE will run using the **module path** `app.main:app`.

---

### 8.2 app.yaml Example

```yaml
runtime: python313
entrypoint: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

env_variables:
  USERNAME: "admin"
  PASSWORD_HASH: "sha256-hash"
  AES_KEY_HASH: "sha256-hash"
  GCP_PROJECT: "project-id"
  GCS_BUCKET: "bucket-name"
```


* **GCS Bucket**

  * Subfolders: `private/`, `public/`
  * No lifecycle rules (manual deletion only).

---

## 9. Success Criteria

* Phase 1: Core upload/list/download/delete/share tested locally.
* Phase 2: JWT auth and access control functional.
* Phase 3: End-to-end AES encryption functional with user-supplied key.
* Cloud phase: Deployment succeeds on GAE Standard, app scales automatically.
* User can reliably upload, manage, and share files.
