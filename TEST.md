# Testing Setup Guide - Phase 2

This guide explains how to set up and test the File Storage API (Phase 2 - Authentication & Access Control) locally and with Google Cloud Storage.

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
set USERNAME=admin
set PASSWORD_HASH=5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
set JWT_SECRET_KEY=your-secret-key-change-this-in-production
set GCP_PROJECT=your-project-id
set GCS_BUCKET=your-unique-bucket-name

# On Windows (PowerShell):
$env:USERNAME="admin"
$env:PASSWORD_HASH="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
$env:JWT_SECRET_KEY="your-secret-key-change-this-in-production"
$env:GCP_PROJECT="your-project-id"
$env:GCS_BUCKET="your-unique-bucket-name"

# On macOS/Linux:
export USERNAME="admin"
export PASSWORD_HASH="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # SHA256 of "password"
export JWT_SECRET_KEY="your-secret-key-change-this-in-production"
export GCP_PROJECT="your-project-id"
export GCS_BUCKET="your-unique-bucket-name"
```

**Authentication Notes**:
- `PASSWORD_HASH` above is SHA256 hash of "password" for development
- For production, generate your own hash: `echo -n "your-password" | sha256sum`
- `JWT_SECRET_KEY` should be a secure random string in production
- **Note**: No `GOOGLE_APPLICATION_CREDENTIALS` needed if you used `gcloud auth application-default login` for local development. For GAE deployment, authentication is automatic.

### 4. Start the Development Server

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## Testing the Application

### Web Interface Testing

**Phase 2 includes a complete web interface for easier testing and usage!**

#### Step 1: Access the Web Interface
1. Navigate to http://localhost:8000 in your browser
2. You should see the home page with file upload options

#### Step 2: Login via Web Interface  
1. Click "Login" or navigate to http://localhost:8000/login
2. Enter username: `admin` and password: `password` (default dev credentials)
3. You'll be redirected to the file management page

#### Step 3: Test File Operations via Web Interface
1. **Upload Files**: Use the upload form on the home page
2. **File Management**: Visit http://localhost:8000/files to see all uploaded files
3. **Admin Controls**: Visit http://localhost:8000/admin for administrative functions
4. **Download Pages**: Access files via http://localhost:8000/download/private/{file_id} or http://localhost:8000/download/public/{file_id}

### API Testing via curl

### Authentication Flow

**Phase 2 requires authentication for all file operations!** You must first obtain a JWT token.

#### Step 1: Login and Get JWT Token
```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password"
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Step 2: Save the Token
Save the `access_token` value from the response. You'll need it for all subsequent requests.

```bash
# Store token in a variable (Linux/macOS/Windows Git Bash)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# For Windows Command Prompt:
set TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# For Windows PowerShell:
$TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Using the FastAPI Documentation

1. Open http://localhost:8000/docs in your browser
2. Click the **"Authorize"** button at the top right
3. Enter your JWT token in the format: `Bearer YOUR_JWT_TOKEN`
4. Now you can test all authenticated endpoints directly

### Manual Testing with curl

#### 1. Test Authentication Endpoints
```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password"

# Get current user info (requires token)
curl -X GET "http://localhost:8000/auth/me" \
     -H "Authorization: Bearer $TOKEN"

# Logout (requires token)
curl -X POST "http://localhost:8000/auth/logout" \
     -H "Authorization: Bearer $TOKEN"
```

#### 2. Test File Upload from URL (Requires Authentication)
```bash
curl -X POST "http://localhost:8000/api/upload/url" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{
       "url": "https://httpbin.org/json",
       "file_id": "test-file-1",
       "is_public": false
     }'
```

#### 3. Test Direct File Upload (Requires Authentication)
```bash
# Create a test file
echo "Hello, World!" > test.txt

# Upload it
curl -X POST "http://localhost:8000/api/upload/direct" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@test.txt" \
     -F "file_id=direct-upload-test" \
     -F "is_public=false"
```

#### 4. List Files (Requires Authentication)
```bash
# List all files
curl "http://localhost:8000/api/files" \
     -H "Authorization: Bearer $TOKEN"

# List only public files
curl "http://localhost:8000/api/files?is_public=true" \
     -H "Authorization: Bearer $TOKEN"

# List only private files  
curl "http://localhost:8000/api/files?is_public=false" \
     -H "Authorization: Bearer $TOKEN"
```

#### 5. Download File (Dedicated Endpoints)
```bash
# Private file download (requires authentication) - NEW dedicated endpoint
curl "http://localhost:8000/api/download/private/test-file-1" \
     -H "Authorization: Bearer $TOKEN" \
     --output downloaded-file.json

# Public file download (no authentication required) - NEW dedicated endpoint
curl "http://localhost:8000/api/download/public/public-file" \
     --output downloaded-public-file.json

# Legacy endpoint still works (requires is_public query parameter)
curl "http://localhost:8000/api/download/test-file-1?is_public=false" \
     -H "Authorization: Bearer $TOKEN" \
     --output downloaded-legacy.json

# HEAD request to get file info without downloading
curl -I "http://localhost:8000/api/download/private/test-file-1" \
     -H "Authorization: Bearer $TOKEN"
```

#### 6. Rename File (Requires Authentication)
```bash
curl -X POST "http://localhost:8000/api/rename/test-file-1?is_public=false" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"new_file_id": "renamed-test-file"}'
```

#### 7. Toggle Share (Private/Public) (Requires Authentication)
```bash
curl -X POST "http://localhost:8000/api/share/renamed-test-file?current_is_public=false" \
     -H "Authorization: Bearer $TOKEN"
```

#### 8. Delete File (Requires Authentication)
```bash
curl -X DELETE "http://localhost:8000/api/files/renamed-test-file?is_public=true" \
     -H "Authorization: Bearer $TOKEN"
```

#### 9. Test Access Control
```bash
# This should fail with 401 Unauthorized
curl "http://localhost:8000/api/files"

# This should fail with 401 Unauthorized (private endpoint)
curl "http://localhost:8000/api/download/private/private-file"

# This should work (public endpoint, no auth required)
curl "http://localhost:8000/api/download/public/public-file"

# Legacy endpoint tests
curl "http://localhost:8000/api/download/private-file?is_public=false"  # Should fail
curl "http://localhost:8000/api/download/public-file?is_public=true"   # Should work
```

### Using Python Requests

Create a test script `test_api_phase2.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"
AUTH_URL = f"{BASE_URL}/auth"

class FileStorageAPITester:
    def __init__(self, username="admin", password="password"):
        self.username = username
        self.password = password
        self.token = None
        self.headers = {}
    
    def login(self):
        """Login and get JWT token"""
        response = requests.post(f"{AUTH_URL}/login", data={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== Testing Authentication Endpoints ===")
        
        # Test /auth/me
        response = requests.get(f"{AUTH_URL}/me", headers=self.headers)
        if response.status_code == 200:
            print(f"✅ GET /auth/me: {response.json()}")
        else:
            print(f"❌ GET /auth/me failed: {response.status_code}")
        
        # Test /auth/logout
        response = requests.post(f"{AUTH_URL}/logout", headers=self.headers)
        if response.status_code == 200:
            print(f"✅ POST /auth/logout: {response.json()}")
        else:
            print(f"❌ POST /auth/logout failed: {response.status_code}")
    
    def test_upload_from_url(self):
        """Test file upload from URL"""
        response = requests.post(f"{API_URL}/upload/url", 
                               headers=self.headers,
                               json={
                                   "url": "https://httpbin.org/json",
                                   "file_id": "python-test",
                                   "is_public": False
                               })
        print(f"Upload from URL: {response.status_code} - {response.json() if response.status_code == 200 else response.text}")
        return response.json() if response.status_code == 200 else None
    
    def test_list_files(self):
        """Test file listing"""
        response = requests.get(f"{API_URL}/files", headers=self.headers)
        if response.status_code == 200:
            print(f"List files: {response.json()}")
        else:
            print(f"❌ List files failed: {response.status_code} - {response.text}")
        return response.json() if response.status_code == 200 else []
    
    def test_download_file(self, file_id, is_public=False):
        """Test file download using new dedicated endpoints"""
        if not is_public:
            # Use dedicated private endpoint
            response = requests.get(f"{API_URL}/download/private/{file_id}", 
                                  headers=self.headers)
        else:
            # Use dedicated public endpoint (no auth needed)
            response = requests.get(f"{API_URL}/download/public/{file_id}")
        
        print(f"Download {file_id} (public={is_public}): {response.status_code}")
        if response.status_code == 200:
            print(f"  Content-Length: {response.headers.get('Content-Length', 'N/A')}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        return response.content if response.status_code == 200 else None
    
    def test_rename_file(self, file_id, new_name, is_public=False):
        """Test file rename"""
        response = requests.post(f"{API_URL}/rename/{file_id}", 
                               headers=self.headers,
                               params={"is_public": is_public},
                               json={"new_file_id": new_name})
        print(f"Rename {file_id} to {new_name}: {response.status_code} - {response.json() if response.status_code == 200 else response.text}")
        return response.json() if response.status_code == 200 else None
    
    def test_toggle_share(self, file_id, current_is_public=False):
        """Test privacy toggle"""
        response = requests.post(f"{API_URL}/share/{file_id}",
                               headers=self.headers,
                               params={"current_is_public": current_is_public})
        print(f"Toggle share {file_id}: {response.status_code} - {response.json() if response.status_code == 200 else response.text}")
        return response.json() if response.status_code == 200 else None
    
    def test_delete_file(self, file_id, is_public=False):
        """Test file deletion"""
        response = requests.delete(f"{API_URL}/files/{file_id}",
                                 headers=self.headers,
                                 params={"is_public": is_public})
        print(f"Delete {file_id}: {response.status_code} - {response.json() if response.status_code == 200 else response.text}")
        return response.json() if response.status_code == 200 else None
    
    def test_access_control(self):
        """Test access control (unauthorized requests)"""
        print("\n=== Testing Access Control ===")
        
        # Test without auth token - should fail
        response = requests.get(f"{API_URL}/files")
        if response.status_code == 401:
            print("✅ Unauthorized file listing blocked correctly")
        else:
            print(f"❌ Unauthorized file listing not blocked: {response.status_code}")
        
        # Test private file download without auth - should fail (new endpoint)
        response = requests.get(f"{API_URL}/download/private/test-file")
        if response.status_code == 401:
            print("✅ Private file access blocked correctly (dedicated endpoint)")
        else:
            print(f"❌ Private file access not blocked: {response.status_code}")
        
        # Test legacy endpoint without auth - should fail  
        response = requests.get(f"{API_URL}/download/test-file?is_public=false")
        if response.status_code == 401:
            print("✅ Private file access blocked correctly (legacy endpoint)")
        else:
            print(f"❌ Private file access not blocked (legacy): {response.status_code}")
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 Starting File Storage API Phase 2 Test Suite")
        
        # Step 1: Login
        if not self.login():
            return
        
        # Step 2: Test auth endpoints
        self.test_auth_endpoints()
        
        # Step 3: Test access control
        self.test_access_control()
        
        print("\n=== Testing File Operations ===")
        
        # Step 4: Upload file
        upload_result = self.test_upload_from_url()
        
        # Step 5: List files
        files = self.test_list_files()
        
        # Step 6: Download file
        self.test_download_file("python-test", is_public=False)
        
        # Step 7: Rename file
        self.test_rename_file("python-test", "python-renamed", is_public=False)
        
        # Step 8: Toggle privacy
        self.test_toggle_share("python-renamed", current_is_public=False)
        
        # Step 9: Download as public file
        self.test_download_file("python-renamed", is_public=True)
        
        # Step 10: Delete file
        self.test_delete_file("python-renamed", is_public=True)
        
        print("\n✅ Test suite completed!")

if __name__ == "__main__":
    tester = FileStorageAPITester()
    tester.run_full_test_suite()
```

Run the test:
```bash
python test_api_phase2.py
```

Expected output:
```
🚀 Starting File Storage API Phase 2 Test Suite
✅ Login successful

=== Testing Authentication Endpoints ===
✅ GET /auth/me: {'username': 'admin'}
✅ POST /auth/logout: {'message': 'Successfully logged out'}

=== Testing Access Control ===
✅ Unauthorized access blocked correctly
✅ Private file access blocked correctly

=== Testing File Operations ===
Upload from URL: 200 - {'file_id': 'python-test', 'object_path': 'private/python-test', 'size': 429, 'is_public': False}
List files: [{'file_id': 'python-test', 'object_path': 'private/python-test', 'size': 429, 'is_public': False}]
Download python-test (public=False): 200
Rename python-test to python-renamed: 200 - {'old_file_id': 'python-test', 'new_file_id': 'python-renamed', 'object_path': 'private/python-renamed', 'is_public': False}
Toggle share python-renamed: 200 - {'file_id': 'python-renamed', 'object_path': 'public/python-renamed', 'was_public': False, 'is_public': True}
Download python-renamed (public=True): 200
Delete python-renamed: 200 - {'message': 'File python-renamed deleted successfully'}

✅ Test suite completed!
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - **401 Unauthorized**: Check that you're sending the JWT token in the Authorization header
   - **Invalid credentials**: Verify username/password match environment variables
   - **Token expired**: JWT tokens expire after 1 hour - get a new token by logging in again

2. **Environment Variable Issues**  
   - **Login fails with correct credentials**: Check `PASSWORD_HASH` environment variable matches SHA256 hash of password
   - **JWT errors**: Ensure `JWT_SECRET_KEY` is set (uses default for development)
   - Generate password hash: `python -c "import hashlib; print(hashlib.sha256('your-password'.encode()).hexdigest())"`

3. **GCS Authentication Error**
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account key
   - Verify the service account has the necessary permissions
   - For local development, use: `gcloud auth application-default login`

4. **Bucket Not Found**
   - Confirm the bucket name is correct in environment variables
   - Ensure the bucket exists in your GCP project

5. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're in the correct directory and virtual environment
   - Check that PyJWT and passlib are installed

6. **Port Already in Use**
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

### Web Interface
- ✅ Home page loads with upload interface at http://localhost:8000
- ✅ Login page works with default credentials (admin/password)
- ✅ JWT token stored in browser localStorage after login
- ✅ File management interface shows uploaded files
- ✅ Admin controls accessible after authentication
- ✅ Download pages work for both private and public files

### Authentication API
- ✅ Successful login with valid credentials (form-based authentication)
- ✅ 401 errors for requests without valid JWT tokens
- ✅ Proper JWT token format in login response
- ✅ User info accessible via /auth/me endpoint

### File Operations API
- ✅ Successful file uploads (both URL and direct) with authentication
- ✅ Files appearing in your GCS bucket under `private/` or `public/` folders
- ✅ Correct file listing with size information (authenticated)
- ✅ Dedicated download endpoints: `/api/download/private/` and `/api/download/public/`
- ✅ HEAD requests return file metadata without downloading content
- ✅ Private file downloads require authentication
- ✅ Public file downloads work without authentication  
- ✅ Successful renames, share toggles, and deletions (all authenticated)

### Access Control
- ✅ 401 errors for all file operations without authentication
- ✅ Private files properly protected via dedicated `/api/download/private/` endpoint
- ✅ Public files accessible without authentication via `/api/download/public/` endpoint
- ✅ Legacy `/api/download/{file_id}` endpoint with conditional authentication
- ✅ Appropriate error responses for invalid operations

## Phase Status

- ✅ **Phase 1**: Core Logic (file operations, GCS integration) - **COMPLETED**
- ✅ **Phase 2**: Authentication & Access Control - **COMPLETED** 
- 🔄 **Phase 3**: End-to-End AES Encryption - **PLANNED**
- 🔄 **Cloud Phase**: Deploy to Google App Engine - **READY**

## Next Steps

After successful Phase 2 testing:
1. **Deploy to GAE**: Use the updated app.yaml with authentication environment variables
2. **Phase 3**: Add optional end-to-end AES encryption
3. **Production Hardening**: Implement additional security measures