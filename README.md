# ConnexxionEngine

ConnexxionEngine is a secure, professional email hosting service with a clean, modern interface. It provides encrypted email management, custom domain support, and organized folder structure (Inbox, Sent, Drafts, Spam, Archive, Trash).

## Features

- 🔒 **Secure & Private**: Encrypted connections, no ads, no tracking
- 📧 **Custom Domains**: Professional emails with your own domain
- 📱 **Clean Dashboard**: Beautiful, organized interface across web and mobile
- 🔧 **Easy Setup**: Connect existing email accounts (Gmail, Outlook, custom IMAP/SMTP)
- 📁 **Organized Folders**: Inbox, Sent, Drafts, Spam, Archive, Trash
- ⚡ **Fast & Reliable**: Built with FastAPI and React for optimal performance

## Architecture

- **Backend**: FastAPI (Python) with PostgreSQL and Redis
- **Frontend**: React with TypeScript and Tailwind CSS
- **Authentication**: JWT-based with encrypted credential storage
- **Email Protocols**: IMAP/SMTP with SSL/TLS support

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd email_engine
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Copy environment variables
   cp .env.example .env
   # Edit .env with your database and Redis URLs, and generate secret keys
   
   # Run database migrations
   alembic upgrade head
   
   # Start backend
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Deployment

### Deploy to Render (Recommended)

This project is configured for easy deployment on Render with the included `render.yaml` file.

#### Prerequisites
- GitHub account
- Render account (free tier available)

#### Step-by-Step Deployment

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/connexxionengine.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file
   - Click "Apply" to deploy

3. **Environment Variables**
   Render will automatically set most environment variables, but you may need to customize:
   - `CORS_ORIGINS`: Set to your frontend URL
   - Database and Redis are automatically provisioned

4. **Access Your Application**
   - Your app will be available at `https://connexxionengine.onrender.com`
   - Backend API at `https://connexxionengine-api.onrender.com`

### Alternative Deployment Options

#### Docker Deployment
```bash
# Build and run with Docker
docker build -t connexxionengine .
docker run -p 8000:8000 connexxionengine
```

#### Manual VPS Deployment
1. Set up PostgreSQL and Redis
2. Copy files to server
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables
5. Run migrations: `alembic upgrade head`
6. Start with: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_NAME` | Application name | No | ConnexxionEngine |
| `DEBUG` | Debug mode | No | false |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection string | Yes | - |
| `AES_SECRET_KEY` | Base64 32-byte key for encryption | Yes | - |
| `JWT_SECRET_KEY` | JWT signing secret | Yes | - |
| `JWT_EXPIRES_MINUTES` | JWT expiration time | No | 1440 (24h) |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | - |
| `SMTP_USE_SSL` | Use SSL for SMTP | No | true |
| `IMAP_USE_SSL` | Use SSL for IMAP | No | true |

## API Documentation

Once deployed, visit `/docs` on your backend URL for interactive API documentation.

## Security

- All credentials are encrypted using AES-GCM encryption
- JWT tokens for stateless authentication
- HTTPS enforced in production
- CORS properly configured
- SQL injection protection via SQLAlchemy ORM

## Support

For issues and feature requests, please create an issue in the GitHub repository.

## License

Copyright © 2024 ConnexxionEngine. All rights reserved.