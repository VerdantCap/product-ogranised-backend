# Backend Setup Guide

This document provides detailed instructions for setting up and running the Organised-AI backend service.

## Table of Contents

1. [Major Components](#major-components)
2. [Development Environment Setup](#development-environment-setup)
3. [Production Environment Setup](#production-environment-setup)
4. [Docker Setup](#docker-setup)
5. [Database Migrations](#database-migrations)
6. [API Documentation](#api-documentation)
7. [Project Structure](#project-structure)

## Major Components

The Organised-AI backend uses the following major components:

- **PostgreSQL**: Relational database for storing application data
- **Redis**: In-memory data store used for caching and session management
- **MinIO**: S3-compatible object storage for file storage
- **FastAPI**: Python web framework for building the API
- **SQLAlchemy**: ORM for database interactions
- **Alembic**: Database migration tool
- **JWT**: Authentication mechanism
- **Stripe**: Payment processing (configured but may not be fully implemented)
- **OpenAI**: AI capabilities integration

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL
- Redis
- MinIO (for file storage)
- Poetry (for dependency management)

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Organised-ai/product-organised-backend.git
   cd product-organised-backend
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables (adjust as needed):
   ```
   # PostgreSQL configuration
   SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/organise
   
   # Redis configuration
   REDIS_HOST=localhost
   REDIS_PORT=6380
   REDIS_PASSWORD=
   
   # MinIO/S3 configuration
   AWS_ACCESS_KEY_ID=minio_key
   AWS_SECRET_KEY=minio_password
   S3_ENDPOINT_URL=http://localhost:9000
   S3_PUBLIC_BUCKET=public
   S3_FILES_BUCKET_NAME=files
   USE_S3_STORAGE=True
   
   # Frontend URL for OAuth callbacks
   FRONTEND_URL=http://localhost:3000
   
   # JWT configuration
   JWT_SECRET=your-secret-key
   JWT_EXPIRY_DAYS=30
   
   # Email configuration (for verification emails)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   VERIFICATION_SMTP_FROM_EMAIL=support-mail
   VERIFICATION_SMTP_USERNAME=your-email
   VERIFICATION_SMTP_PASSWORD=your-app-password
   ```

5. **Set up PostgreSQL**:
   ```bash
   # Create the database
   createdb organise
   ```

6. **Set up Redis**:
   Ensure Redis is running on port 6380. If you're using a different port, update the `.env` file accordingly.

7. **Set up MinIO**:
   Ensure MinIO is running on port 9000. If you're using a different port, update the `.env` file accordingly.

8. **Run database migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

9. **Start the backend server**:
   ```bash
   poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

10. **Verify the setup**:
    Open your browser and navigate to `http://localhost:8000/docs` to access the Swagger UI documentation.

## Production Environment Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL
- Redis
- MinIO or S3-compatible storage
- Poetry (for dependency management)
- Nginx or similar for reverse proxy (recommended)

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Organised-ai/product-organised-backend.git
   cd product-organised-backend
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies** (excluding development dependencies):
   ```bash
   poetry install --no-dev
   ```

4. **Set up environment variables**:
   Create a `.env` file with production values:
   ```
   # PostgreSQL configuration
   SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://postgres:secure-password@your-postgres-host:5432/organise
   
   # Redis configuration
   REDIS_HOST=your-redis-host
   REDIS_PORT=6379
   REDIS_PASSWORD=secure-redis-password
   
   # MinIO/S3 configuration
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_KEY=your-secret-key
   S3_ENDPOINT_URL=https://your-minio-or-s3-endpoint
   S3_PUBLIC_BUCKET=public
   S3_FILES_BUCKET_NAME=files
   USE_S3_STORAGE=True
   
   # Frontend URL for OAuth callbacks
   FRONTEND_URL=https://your-frontend-domain
   
   # JWT configuration
   JWT_SECRET=secure-random-string
   JWT_EXPIRY_DAYS=30
   
   # Email configuration
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   VERIFICATION_SMTP_FROM_EMAIL=support@getorganised.ai
   VERIFICATION_SMTP_USERNAME=your-email@gmail.com
   VERIFICATION_SMTP_PASSWORD=your-app-password
   ```

5. **Run database migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

6. **Start the production server**:
   ```bash
   poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

7. **Set up a reverse proxy** (Nginx or similar) to handle HTTPS and forward requests to the application.

   Example Nginx configuration:
   ```nginx
   server {
       listen 80;
       server_name your-api-domain.com;
       
       # Redirect HTTP to HTTPS
       return 301 https://$host$request_uri;
   }
   
   server {
       listen 443 ssl;
       server_name your-api-domain.com;
       
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

8. **Set up a process manager** (e.g., Supervisor, systemd) to ensure the application runs continuously.

   Example systemd service file (`/etc/systemd/system/organised-backend.service`):
   ```
   [Unit]
   Description=Organised-AI Backend
   After=network.target
   
   [Service]
   User=your-user
   WorkingDirectory=/path/to/product-organised-backend
   ExecStart=/path/to/.local/bin/poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start the service:
   ```bash
   sudo systemctl enable organised-backend
   sudo systemctl start organised-backend
   ```

## Docker Setup

The backend can be run using Docker Compose, which simplifies the setup process by containerizing all required services.

### Prerequisites

- Docker
- Docker Compose

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Organised-ai/product-organised-backend.git
   cd product-organised-backend
   ```

2. **Create a `.env` file** with appropriate values (see the Development or Production setup sections).

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```
   This will start PostgreSQL, Redis, and MinIO services.

4. **Run database migrations**:
   ```bash
   # If you're running the application outside Docker
   poetry run alembic upgrade head
   
   # If you're running the application inside Docker
   docker-compose exec app poetry run alembic upgrade head
   ```

5. **Start the application** (if not already started by Docker Compose):
   ```bash
   # If you're running the application outside Docker
   poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   
   # If you're running the application inside Docker
   docker-compose exec app poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Verify the setup**:
   Open your browser and navigate to `http://localhost:8000/docs` to access the Swagger UI documentation.

## Database Migrations

The project uses Alembic for database migrations.

### Creating a New Migration

When you make changes to the database models, you need to create a new migration:

```bash
poetry run alembic revision --autogenerate -m "description of changes"
```

### Applying Migrations

To apply all pending migrations:

```bash
poetry run alembic upgrade head
```

### Reverting Migrations

To revert the most recent migration:

```bash
poetry run alembic downgrade -1
```

To revert to a specific migration:

```bash
poetry run alembic downgrade <migration_id>
```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
product-organised-backend/
├── alembic/                  # Database migration scripts
├── src/
│   ├── controllers/          # API route handlers
│   ├── daos/                 # Data Access Objects
│   ├── db/                   # Database configuration
│   ├── middleware/           # FastAPI middleware
│   ├── models/               # SQLAlchemy models
│   ├── services/             # Business logic
│   ├── utils/                # Utility functions
│   ├── __init__.py
│   ├── base.py
│   ├── config.py             # Application configuration
│   ├── database.py           # Database connection setup
│   ├── enums.py              # Enumeration types
│   ├── main.py               # Application entry point
│   └── schemas.py            # Pydantic schemas
├── docker-compose.yml        # Docker Compose configuration
├── poetry.lock               # Poetry lock file
├── poetry.toml               # Poetry configuration
├── pyproject.toml            # Project dependencies
├── config/                   # Configuration templates
│   ├── nginx/                # Nginx configuration templates
│   │   └── backend.conf      # Sample Nginx configuration for backend
│   └── minio/                # MinIO configuration templates
│       └── permissions.json  # Sample MinIO permissions
└── README.md                 # Project README
```

You can check your current environment with the following commands:

```bash
# Show current directory
pwd
# Expected output: /path/to/product-organised-backend

# List files in the current directory
ls -la
# Expected output: List of files and directories including alembic/, src/, docker-compose.yml, etc.

# Show directory structure
find . -type d -not -path "*/\.*" | sort
# Expected output: Directory structure of the project
```

## Database Schema and Commands

### Database Schema

The main database tables and their relationships are as follows:

```
users
  ├── id (PK)
  ├── email
  ├── hashed_password
  ├── full_name
  ├── is_active
  └── created_at

workspaces
  ├── id (PK)
  ├── name
  ├── description
  ├── created_at
  └── owner_id (FK -> users.id)

workspace_members
  ├── id (PK)
  ├── workspace_id (FK -> workspaces.id)
  ├── user_id (FK -> users.id)
  ├── role
  └── joined_at

folders
  ├── id (PK)
  ├── name
  ├── workspace_id (FK -> workspaces.id)
  ├── parent_id (FK -> folders.id)
  ├── created_at
  └── created_by (FK -> users.id)

files
  ├── id (PK)
  ├── name
  ├── size
  ├── mime_type
  ├── storage_path
  ├── workspace_id (FK -> workspaces.id)
  ├── folder_id (FK -> folders.id)
  ├── created_at
  ├── updated_at
  ├── created_by (FK -> users.id)
  └── updated_by (FK -> users.id)

tasks
  ├── id (PK)
  ├── title
  ├── description
  ├── status
  ├── priority
  ├── due_date
  ├── workspace_id (FK -> workspaces.id)
  ├── assignee_id (FK -> users.id)
  ├── created_at
  ├── updated_at
  ├── created_by (FK -> users.id)
  └── updated_by (FK -> users.id)

events
  ├── id (PK)
  ├── title
  ├── description
  ├── start_time
  ├── end_time
  ├── location
  ├── workspace_id (FK -> workspaces.id)
  ├── created_at
  ├── updated_at
  ├── created_by (FK -> users.id)
  └── updated_by (FK -> users.id)
```

### Common Database Commands

#### PostgreSQL Commands

```bash
# Connect to PostgreSQL database
psql -U postgres -h localhost -p 5432 -d organise

# List all tables
\dt

# Describe a specific table
\d users

# Execute a query
SELECT id, email, full_name FROM users LIMIT 10;

# Create a backup of the database
pg_dump -U postgres -h localhost -p 5432 -d organise > backup.sql

# Restore a database from backup
psql -U postgres -h localhost -p 5432 -d organise < backup.sql

# Check database size
SELECT pg_size_pretty(pg_database_size('organise'));

# Check table sizes
SELECT 
  table_name, 
  pg_size_pretty(pg_total_relation_size(table_name)) as total_size
FROM 
  information_schema.tables
WHERE 
  table_schema = 'public'
ORDER BY 
  pg_total_relation_size(table_name) DESC;
```

#### Alembic Commands

```bash
# Generate a new migration
poetry run alembic revision --autogenerate -m "Add new field to users table"

# Apply all pending migrations
poetry run alembic upgrade head

# Revert the most recent migration
poetry run alembic downgrade -1

# Get current migration version
poetry run alembic current

# Show migration history
poetry run alembic history --verbose
```

## MinIO Configuration and Permissions

### MinIO Setup

MinIO is used for file storage with S3-compatible API. Here's how to configure it:

#### MinIO Configuration

Create a file `config/minio/permissions.json` with the following content:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::files/*",
        "arn:aws:s3:::public/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::files",
        "arn:aws:s3:::public"
      ]
    }
  ]
}
```

#### MinIO Commands

```bash
# Create buckets
mc mb minio/files
mc mb minio/public

# Set bucket policy
mc policy set download minio/public
mc policy set private minio/files

# List buckets
mc ls minio

# List files in a bucket
mc ls minio/files

# Upload a file
mc cp example.pdf minio/files/

# Download a file
mc cp minio/files/example.pdf ./downloaded-example.pdf

# Remove a file
mc rm minio/files/example.pdf

# Set up a user policy
mc admin policy add minio organise-policy config/minio/permissions.json

# Create a user and apply the policy
mc admin user add minio organise-user organise-password
mc admin policy set minio organise-policy user=organise-user
```

### Expected Setup Time

Setting up MinIO typically takes about 5-10 minutes, including:
- Installation: 2-3 minutes
- Configuration: 2-3 minutes
- Creating buckets and policies: 1-2 minutes
- Testing access: 1-2 minutes

## Redis Commands and Monitoring

Redis is used for caching and session management. Here are some useful commands:

```bash
# Connect to Redis CLI
redis-cli -h localhost -p 6380

# List all keys
KEYS *

# Get information about a specific key
GET session:12345

# Get TTL (time to live) for a key
TTL session:12345

# Delete a key
DEL session:12345

# Monitor Redis commands in real-time
MONITOR

# Get Redis statistics
INFO

# Get memory usage statistics
INFO memory

# Clear all keys (use with caution)
FLUSHALL

# Check Redis connection
redis-cli -h localhost -p 6380 PING
# Expected output: PONG
```

### Redis Objects Structure

The application uses Redis for the following purposes:

1. **Session Storage**:
   ```
   Key pattern: session:{session_id}
   Value: JSON string containing session data
   TTL: 30 days (configurable in .env)
   ```

2. **Rate Limiting**:
   ```
   Key pattern: ratelimit:{ip_address}
   Value: Counter of requests
   TTL: 1 hour
   ```

3. **Cache**:
   ```
   Key pattern: cache:{entity_type}:{entity_id}
   Value: JSON string of cached entity data
   TTL: 1 hour (configurable in .env)
   ```

4. **Email Verification Codes**:
   ```
   Key pattern: email_verification:{email}
   Value: Verification code
   TTL: 10 minutes
   ```

### Expected Redis Setup Time

Setting up Redis typically takes about 3-5 minutes, including:
- Installation: 1-2 minutes
- Configuration: 1-2 minutes
- Testing connection: 1 minute

### Code References

- [Alembic Migrations](https://github.com/Organised-ai/product-organised-backend/tree/main/alembic)
- [API Controllers](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers)
- [Data Access Objects](https://github.com/Organised-ai/product-organised-backend/tree/main/src/daos)
- [Database Configuration](https://github.com/Organised-ai/product-organised-backend/tree/main/src/db)
- [Middleware](https://github.com/Organised-ai/product-organised-backend/tree/main/src/middleware)
- [Database Models](https://github.com/Organised-ai/product-organised-backend/tree/main/src/models)
- [Business Logic Services](https://github.com/Organised-ai/product-organised-backend/tree/main/src/services)
- [Utility Functions](https://github.com/Organised-ai/product-organised-backend/tree/main/src/utils)
- [Application Configuration](https://github.com/Organised-ai/product-organised-backend/blob/main/src/config.py)
- [Database Connection Setup](https://github.com/Organised-ai/product-organised-backend/blob/main/src/database.py)
- [Enumeration Types](https://github.com/Organised-ai/product-organised-backend/blob/main/src/enums.py)
- [Application Entry Point](https://github.com/Organised-ai/product-organised-backend/blob/main/src/main.py)
- [Pydantic Schemas](https://github.com/Organised-ai/product-organised-backend/blob/main/src/schemas.py)
- [Docker Compose Configuration](https://github.com/Organised-ai/product-organised-backend/blob/main/docker-compose.yml)
- [Project Dependencies](https://github.com/Organised-ai/product-organised-backend/blob/main/pyproject.toml)

The backend provides APIs for:

- [User authentication and authorization](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers/auth)
- [Workspace management](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers/workspace)
- [File and folder operations](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers/file)
- [Task management](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers/task)
- [Event planning](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers/event)
- [Activity tracking](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers/activity)
- [Travel planning](https://github.com/Organised-ai/product-organised-backend/tree/main/src/controllers/travel) (accommodations, excursions, transport)
- And more

Each feature has its own controller, model, and data access layer for clean separation of concerns.
