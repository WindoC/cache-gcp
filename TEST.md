# Testing Setup Guide

This guide explains how to set up and test the File Storage API locally and with Google Cloud Storage.

## Prerequisites

- Python 3.13+
- Google Cloud SDK (gcloud CLI)
- A Google Cloud Project with billing enabled
- Google Cloud Storage API enabled

## Local Development Setup

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Cloud Setup

#### Create a GCP Project (if you don't have one)
```bash
gcloud projects create your-project-id
gcloud config set project your-project-id
```

#### Enable required APIs
```bash
gcloud services enable storage.googleapis.com
```

#### Create a GCS Bucket
```bash
gsutil mb gs://your-unique-bucket-name
```

#### Local Development Credentials (Optional)
For local development only, you can use Application Default Credentials:

```bash
# Authenticate with your user account for local testing
gcloud auth application-default login
```

**Note**: When deployed to GAE, the app automatically uses the default App Engine service account with built-in GCS permissions. No additional service account setup is required for production deployment.

### 3. Environment Configuration

Set the following environment variables for local development:

```bash
# On Windows (Command Prompt):
set GCP_PROJECT=your-project-id
set GCS_BUCKET=your-unique-bucket-name

# On Windows (PowerShell):
$env:GCP_PROJECT="your-project-id"
$env:GCS_BUCKET="your-unique-bucket-name"  

# On macOS/Linux:
export GCP_PROJECT="your-project-id"
export GCS_BUCKET="your-unique-bucket-name"
```

**Note**: No `GOOGLE_APPLICATION_CREDENTIALS` needed if you used `gcloud auth application-default login` for local development. For GAE deployment, authentication is automatic.

### 4. Start the Development Server

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## Testing the API

### Using the FastAPI Documentation

1. Open http://localhost:8000/docs in your browser
2. You'll see all available endpoints with interactive testing capabilities
3. Click on any endpoint to expand it and try it out

### Manual Testing with curl

#### 1. Test File Upload from URL
```bash
curl -X POST "http://localhost:8000/api/upload" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://httpbin.org/json",
       "file_id": "test-file-1",
       "is_public": false
     }'
```

#### 2. Test Direct File Upload
```bash
# Create a test file
echo "Hello, World!" > test.txt

# Upload it
curl -X POST "http://localhost:8000/api/upload/direct" \
     -F "file=@test.txt" \
     -F "file_id=direct-upload-test" \
     -F "is_public=false"
```

#### 3. List Files
```bash
# List all files
curl "http://localhost:8000/api/files"

# List only public files
curl "http://localhost:8000/api/files?is_public=true"

# List only private files  
curl "http://localhost:8000/api/files?is_public=false"
```

#### 4. Download File
```bash
curl "http://localhost:8000/api/download/test-file-1?is_public=false" \
     --output downloaded-file.json
```

#### 5. Rename File
```bash
curl -X POST "http://localhost:8000/api/rename/test-file-1?is_public=false" \
     -H "Content-Type: application/json" \
     -d '{"new_file_id": "renamed-test-file"}'
```

#### 6. Toggle Share (Private/Public)
```bash
curl -X POST "http://localhost:8000/api/share/renamed-test-file?current_is_public=false"
```

#### 7. Delete File
```bash
curl -X DELETE "http://localhost:8000/api/files/renamed-test-file?is_public=true"
```

### Using Python Requests

Create a test script `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_upload_from_url():
    response = requests.post(f"{BASE_URL}/upload", json={
        "url": "https://httpbin.org/json",
        "file_id": "python-test",
        "is_public": False
    })
    print("Upload from URL:", response.json())
    return response.json()

def test_list_files():
    response = requests.get(f"{BASE_URL}/files")
    print("List files:", response.json())
    return response.json()

def test_download_file(file_id, is_public=False):
    response = requests.get(f"{BASE_URL}/download/{file_id}", 
                          params={"is_public": is_public})
    print(f"Download status: {response.status_code}")
    return response.content

def test_rename_file(file_id, new_name, is_public=False):
    response = requests.post(f"{BASE_URL}/rename/{file_id}", 
                           params={"is_public": is_public},
                           json={"new_file_id": new_name})
    print("Rename:", response.json())
    return response.json()

def test_toggle_share(file_id, current_is_public=False):
    response = requests.post(f"{BASE_URL}/share/{file_id}",
                           params={"current_is_public": current_is_public})
    print("Toggle share:", response.json())
    return response.json()

def test_delete_file(file_id, is_public=False):
    response = requests.delete(f"{BASE_URL}/files/{file_id}",
                             params={"is_public": is_public})
    print("Delete:", response.json())
    return response.json()

if __name__ == "__main__":
    # Run tests
    upload_result = test_upload_from_url()
    test_list_files()
    test_download_file("python-test")
    test_rename_file("python-test", "python-renamed")
    test_toggle_share("python-renamed", False)
    test_delete_file("python-renamed", True)
```

Run the test:
```bash
python test_api.py
```

## Troubleshooting

### Common Issues

1. **GCS Authentication Error**
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account key
   - Verify the service account has the necessary permissions

2. **Bucket Not Found**
   - Confirm the bucket name is correct in environment variables
   - Ensure the bucket exists in your GCP project

3. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're in the correct directory and virtual environment

4. **Port Already in Use**
   - Change the port: `uvicorn app.main:app --reload --port 8001`
   - Or kill the process using port 8000

### Checking Logs

View application logs:
```bash
# The uvicorn server will show logs in the terminal
# Look for error messages related to GCS operations
```

Check GCS bucket contents:
```bash
gsutil ls gs://your-bucket-name/
gsutil ls gs://your-bucket-name/private/
gsutil ls gs://your-bucket-name/public/
```

### Testing Without GCS

For basic API structure testing without GCS setup, the endpoints will return errors but you can verify:
- FastAPI is running correctly
- Routes are properly configured
- Request/response formats are correct

## Expected Test Results

When properly configured, you should see:
- Successful file uploads (both URL and direct)
- Files appearing in your GCS bucket under `private/` or `public/` folders
- Correct file listing with size information
- Successful downloads, renames, share toggles, and deletions
- Appropriate error responses for invalid operations

## Next Steps

After successful Phase 1 testing:
1. **Phase 2**: Implement JWT authentication
2. **Phase 3**: Add optional AES encryption
3. **Cloud Phase**: Deploy to Google App Engine