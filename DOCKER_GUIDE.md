# Docker Setup Guide

## Quick Start

### 1. Start All Services (Backend + Frontend)
```bash
docker-compose up -d
```

This will:
- Start FastAPI backend on port 8000 (with SQLite database)
- Start Angular frontend on port 4200
- Auto-create SQLite database and tables on startup
- Seed default clause types

### 2. View Logs
```bash
# All services
docker-compose logs -f

# Only backend
docker-compose logs -f app

# Only frontend
docker-compose logs -f frontend
```

### 3. Stop Services
```bash
docker-compose down
```

### 4. Stop and Remove Volumes (⚠️ Deletes all data)
```bash
docker-compose down -v
```

---

## Development Workflow

### Hot Reload
Code changes are automatically detected (volume mount + `--reload` flag).

### Rebuild After Dependency Changes
```bash
docker-compose up -d --build
```

### Run Commands Inside Container
```bash
# Open shell in backend container
docker exec -it clausetracker_app bash

# Run tests
docker exec -it clausetracker_app pytest

# Access SQLite database (the database file is mounted to ./backend/clausetracker.db)
# You can access it from your host machine or copy it out for inspection
docker cp clausetracker_app:/app/clausetracker.db ./backend/
```

---

## Environment Variables

Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL`: Database connection string
- `ENVIRONMENT`: development/production
- `CORS_ORIGINS`: Allowed frontend origins

---

## API Access

- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Direct API**: http://localhost:8000/api/

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac/Linux

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 on host
```

### Database Connection Issues
```bash
# Check db is healthy
docker-compose ps

# Restart database
docker-compose restart db

# View database logs
docker-compose logs db
```

### Reset Everything
```bash
docker-compose down -v
docker-compose up -d --build
```

---

## Production Deployment

For production, update:
1. Change `POSTGRES_PASSWORD` in docker-compose.yml
2. Set `ENVIRONMENT=production`
3. Remove `--reload` from command
4. Configure proper CORS origins
5. Use secrets management for sensitive data
