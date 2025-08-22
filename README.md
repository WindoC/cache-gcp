# File Storage API

A single-user file storage web platform that allows uploading files via external URLs or direct browser upload and stores them in Google Cloud Storage (GCS).

## Features

- Upload files from external URLs
- Direct file upload from browser (multipart/form-data)
- List all files with size information
- Download files with streaming support
- Rename files
- Toggle files between private and public folders
- Delete files
- 200MB file size limit (configurable)

## Technology Stack

- **Backend**: FastAPI (Python 3.13)
- **Storage**: Google Cloud Storage (GCS)
- **Deployment**: Google App Engine (GAE) Standard Environment

## Project Structure

```
project-root/
├── app/
│   ├── main.py        # FastAPI entrypoint
│   ├── routes/        # API routes
│   │   └── files.py   # File management endpoints
│   ├── services/      # Business logic (future phases)
│   ├── utils/         # Helper utilities
│   │   └── gcs_client.py  # GCS operations
│   └── __init__.py
├── main.py            # Entry point
├── app.yaml           # GAE configuration
├── requirements.txt   # Python dependencies
└── README.md
```

## API Endpoints

### File Upload
- `POST /api/upload` - Upload file from external URL
- `POST /api/upload/direct` - Upload file directly from browser

### File Management
- `GET /api/files` - List all files (with optional `is_public` filter)
- `GET /api/download/{file_id}` - Download file (specify `is_public` query param)
- `POST /api/rename/{file_id}` - Rename file (specify `is_public` query param)
- `POST /api/share/{file_id}` - Toggle between private/public (specify `current_is_public` query param)
- `DELETE /api/files/{file_id}` - Delete file (specify `is_public` query param)

## Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (for local testing with GCS):
   ```bash
   export GCP_PROJECT="your-project-id"
   export GCS_BUCKET="your-bucket-name"
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
   ```

3. **Run development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

   Or using the entry point:
   ```bash
   python main.py
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

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
   env_variables:
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
- `404` - File not found
- `409` - File already exists (for uploads and renames)
- `413` - File too large
- `500` - Server error (GCS issues, etc.)

## Development Phases

This is **Phase 1** implementation with core file management features. Future phases will add:
- **Phase 2**: JWT authentication and access control
- **Phase 3**: Optional end-to-end AES encryption
- **Cloud Phase**: Full GAE deployment with production configurations

## Notes

- This implementation assumes GCS is properly configured and accessible
- For local development without GCS, the application will return errors for GCS operations
- All file operations are currently unauthenticated (Phase 1)
- File IDs are used as object names in GCS (with folder prefixes)