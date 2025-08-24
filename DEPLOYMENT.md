# Deployment Guide - Google App Engine

This guide provides step-by-step instructions for deploying the File Storage application to Google App Engine (GAE) Standard Environment.

## Cloud Phase Readiness Status ✅

**The application is READY for Cloud phase deployment.** All requirements have been implemented:

- ✅ **Phase 1**: Core Logic (upload, list, download, rename, delete, private/public folders)
- ✅ **Phase 2**: Authentication & Access Control (JWT-based auth)
- ✅ **Phase 3**: End-to-End AES Encryption (mandatory encryption for specific endpoints)
- ✅ **GAE Configuration**: Proper app.yaml, requirements.txt, and project structure

## Prerequisites

1. **Google Cloud Platform Account**
   - Active GCP project with billing enabled
   - App Engine API enabled
   - Cloud Storage API enabled

2. **Local Environment**
   - Python 3.13+
   - Google Cloud SDK (`gcloud` CLI) installed and authenticated
   - Project dependencies installed locally for testing

3. **Required Services**
   - Google Cloud Storage bucket created
   - App Engine application initialized in your GCP project

## Pre-Deployment Setup

### 1. Install Google Cloud SDK

```bash
# Download and install from: https://cloud.google.com/sdk/docs/install
# Or use package managers:

# macOS
brew install google-cloud-sdk

# Ubuntu/Debian
curl https://sdk.cloud.google.com | bash
```

### 2. Authenticate and Configure gcloud

```bash
# Authenticate with your Google account
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Verify configuration
gcloud config list
```

### 3. Enable Required APIs

```bash
# Enable App Engine Admin API
gcloud services enable appengine.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage.googleapis.com
```

### 4. Initialize App Engine (if not done already)

```bash
# Initialize App Engine in your project
gcloud app create --region=us-central1
```

**Note**: Choose a region close to your users. This cannot be changed later.

### 5. Create Cloud Storage Bucket

```bash
# Create bucket (must be globally unique)
gsutil mb gs://your-unique-bucket-name

# Set uniform bucket-level access (recommended)
gsutil uniformbucketlevelaccess set on gs://your-unique-bucket-name

# Create required folder structure
echo "" | gsutil cp - gs://your-unique-bucket-name/private/.gitkeep
echo "" | gsutil cp - gs://your-unique-bucket-name/public/.gitkeep
```

## Configuration

### 1. Update app.yaml Environment Variables

Edit `app.yaml` and replace placeholder values:

```yaml
runtime: python313
entrypoint: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

env_variables:
  USERNAME: "your_admin_username"                    # Change this
  PASSWORD_HASH: "your_sha256_password_hash"         # Generate new hash
  JWT_SECRET_KEY: "your_secure_random_jwt_secret"    # Generate secure key
  AES_KEY_HASH: "your_sha256_aes_key_hash"          # Generate new hash
  GCP_PROJECT: "your-actual-project-id"             # Your GCP project ID
  GCS_BUCKET: "your-unique-bucket-name"             # Your GCS bucket name

automatic_scaling:
  min_instances: 0
  max_instances: 1
```

### 2. Generate Secure Hashes and Keys

#### Option A: Using Python Commands

```python
import hashlib
import secrets

# Generate password hash (replace "your_password" with actual password)
password = "your_secure_password"
password_hash = hashlib.sha256(password.encode()).hexdigest()
print(f"PASSWORD_HASH: {password_hash}")

# Generate JWT secret key
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET_KEY: {jwt_secret}")

# Generate AES key hash (replace "your_aes_key" with actual encryption key)
aes_key = "your_encryption_key"
aes_key_hash = hashlib.sha256(aes_key.encode()).hexdigest()
print(f"AES_KEY_HASH: {aes_key_hash}")
```

#### Option B: Using Bash Commands

```bash
# Generate password hash (replace "your_password" with actual password)
echo -n "your_secure_password" | sha256sum

# Generate AES key hash (replace "your_aes_key" with actual encryption key)
echo -n "your_encryption_key" | sha256sum

# Generate JWT secret key (using openssl)
openssl rand -base64 32
```

### 3. Set IAM Permissions

Ensure your App Engine service account has Storage Object Admin permissions:

```bash
# Get your project's App Engine service account
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

# Grant Storage Object Admin role to your bucket
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectAdmin gs://your-unique-bucket-name
```

## Deployment Process

### 1. Local Testing (Recommended)

Test locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables for local testing
export USERNAME="your_admin_username"
export PASSWORD_HASH="your_sha256_password_hash"
export JWT_SECRET_KEY="your_secure_random_jwt_secret"
export AES_KEY_HASH="your_sha256_aes_key_hash"
export GCP_PROJECT="your-actual-project-id"
export GCS_BUCKET="your-unique-bucket-name"

# Run locally
uvicorn app.main:app --reload

# Test at http://localhost:8000
```

### 2. Deploy to GAE

```bash
# Navigate to project root
cd /path/to/your/project

# Deploy to App Engine
gcloud app deploy

# Follow the prompts:
# - Confirm target project
# - Confirm region
# - Type 'Y' to continue

# Deployment typically takes 2-5 minutes
```

### 3. Post-Deployment Verification

```bash
# Get your app URL
gcloud app browse

# Or get the URL directly
echo "https://$(gcloud config get-value project).appspot.com"

# Check deployment status
gcloud app versions list

# View logs
gcloud app logs tail -s default
```

## Post-Deployment Configuration

### 1. Test Core Functionality

1. **Web Interface**: Visit your app URL
2. **Authentication**: Test login with your configured credentials
3. **File Upload**: Test both URL and direct upload methods
4. **Encryption**: Verify AES encryption prompts and functionality
5. **File Management**: Test list, download, rename, share, delete operations

### 2. Security Checklist

- [ ] Changed default username and password
- [ ] Generated secure JWT secret key
- [ ] Set up unique AES encryption key
- [ ] Verified HTTPS is enforced (automatic with GAE)
- [ ] Confirmed private files require authentication
- [ ] Tested encryption/decryption workflow

### 3. Configure Custom Domain (Optional)

```bash
# Map custom domain to your app
gcloud app domain-mappings create your-domain.com

# Follow DNS configuration instructions provided by the command
```

## Monitoring and Maintenance

### 1. View Application Logs

```bash
# Real-time logs
gcloud app logs tail -s default

# Filter logs by severity
gcloud app logs read --severity=ERROR

# View logs in Cloud Console
# https://console.cloud.google.com/logs
```

### 2. Monitor Performance

- **Cloud Console**: https://console.cloud.google.com/appengine
- **Metrics**: CPU usage, memory, requests, errors
- **Scaling**: Monitor auto-scaling behavior

### 3. Update Deployment

```bash
# Make changes to code
# Update version in app.yaml if needed
# Deploy new version
gcloud app deploy

# Manage versions
gcloud app versions list
gcloud app versions migrate VERSION_ID
gcloud app versions delete OLD_VERSION_ID
```

### 4. Backup and Recovery

- **Automatic**: GCS provides built-in durability and availability
- **Manual Backup**: Use `gsutil` to copy bucket contents
```bash
gsutil -m cp -r gs://your-bucket gs://your-backup-bucket
```

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Verify `app.yaml` syntax
   - Check all environment variables are set
   - Ensure requirements.txt includes all dependencies

2. **Cannot Connect to GCS**
   - Verify bucket name in `app.yaml`
   - Check IAM permissions for App Engine service account
   - Confirm GCS API is enabled

3. **Authentication Issues**
   - Verify JWT_SECRET_KEY is set and consistent
   - Check PASSWORD_HASH is correctly generated
   - Ensure USERNAME matches login attempts

4. **Encryption Failures**
   - Verify AES_KEY_HASH matches user's encryption key
   - Check browser localStorage for key persistence
   - Confirm crypto.py module is working correctly

### Getting Help

- **GAE Documentation**: https://cloud.google.com/appengine/docs
- **Cloud Storage**: https://cloud.google.com/storage/docs
- **Application Logs**: Check GAE logs for specific error messages
- **Local Testing**: Always test locally before deploying

## Cost Considerations

- **App Engine**: Pay per instance hour and requests
- **Cloud Storage**: Pay per GB stored and operations
- **Free Tier**: GAE Standard includes free quotas for small applications

Monitor usage in the GCP Console to avoid unexpected charges.

---

## Summary

Your File Storage application is **ready for production deployment** on Google App Engine. The application includes:

- Complete file management functionality
- JWT-based authentication
- End-to-end AES encryption
- Proper security practices
- Auto-scaling infrastructure

Follow this guide to deploy safely and securely to GAE Standard Environment.