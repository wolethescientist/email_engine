# ConnexxionEngine API

ConnexxionEngine is a secure, professional email API service. It provides encrypted email management over a RESTful API, supporting custom domain connections via IMAP/SMTP.

## Features

- 🔒 **Secure & Private**: Encrypted connections and credential storage.
- 📧 **Connect Any Email**: Use the API to manage any existing email account (Gmail, Outlook, custom IMAP/SMTP).
- 📬 **Full Email Functionality**: List mailboxes, read emails, send emails, and manage attachments.
- ⚡ **Fast & Reliable**: Built with FastAPI for optimal performance.
- 📚 **Automatic Documentation**: Interactive API documentation powered by Swagger UI and ReDoc.

## Architecture

- **Backend**: FastAPI (Python)
- **Authentication**: JWT-based with encrypted credential storage
- **Email Protocols**: IMAP/SMTP with SSL/TLS and OAuth2 support

## Local Development

### Prerequisites

- Python 3.11+

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd email_engine_v1
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Copy environment variables
   
   # Start backend
   uvicorn app.main:app --reload
   ```

3. **Access the application**
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## Deployment

### Docker Deployment (Recommended)

A `Dockerfile` is included for easy containerization.

```bash
# Build the Docker image
docker build -t connexxionengine-api .

# Run the container
docker run -p 8000:8000 --env-file .env connexxionengine-api
```

### Manual Deployment

1. Copy files to your server.
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables (see below).
4. Start the server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_NAME` | Application name | No | ConnexxionEngine |
| `DEBUG` | Debug mode | No | false |
| `AES_SECRET_KEY` | Base64 32-byte key for encryption | Yes | - |
| `JWT_SECRET_KEY` | JWT signing secret | Yes | - |
| `JWT_EXPIRES_MINUTES` | JWT expiration time | No | 1440 (24h) |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | `http://localhost:5173` |
| `SMTP_USE_SSL` | Use SSL for SMTP | No | true |
| `IMAP_USE_SSL` | Use SSL for IMAP | No | true |

## API Documentation

Once running, visit `/docs` for interactive API documentation or `/redoc` for alternative documentation.

## Security

- All credentials are encrypted using AES-GCM encryption.
- JWT tokens for stateless authentication.
- HTTPS should be enforced in production (e.g., via a reverse proxy).
- CORS is configurable via environment variables.

## Support

For issues and feature requests, please create an issue in the GitHub repository.

## License

Copyright © 2024 ConnexxionEngine. All rights reserved.
