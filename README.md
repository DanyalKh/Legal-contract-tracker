# Contract Clause Analysis System

A modern web application for analyzing legal contracts using AI-powered clause detection and manual labeling workflows. Built with FastAPI backend and Angular frontend.

## Project Overview

This application enables legal professionals to:
- Upload contract documents (text/markdown files)
- Automatically parse contracts into sentences
- Manually label sentences with clause types (confidentiality, termination, liability, etc.)
- View contract analysis dashboards with filtering and grouping
- Track labeling progress and statistics

Key Features:
- Document Upload & Parsing: Automatic sentence segmentation using spaCy
- Clause Labeling: Manual labeling with predefined clause types
- Dashboard Analytics: Contract progress tracking and statistics
- Advanced Filtering: Search, filter by clause type, and group by clause categories
- Responsive UI: Modern Angular Material design

## Implemented Features

### Core Functionality
- ✅ Contract upload with automatic text parsing
- ✅ Sentence-level clause type labeling
- ✅ Contract dashboard with progress tracking
- ✅ Search and filter contracts
- ✅ Clause type filtering (fixed and tested)
- ✅ Dashboard grouping by clause type (new feature)
- ✅ Contract deletion and download
- ✅ Responsive grid/list view toggles

### Technical Features
- ✅ SQLite database (file-based, no external dependencies)
- ✅ RESTful API with FastAPI
- ✅ Angular frontend with Material Design
- ✅ Docker containerization
- ✅ Comprehensive test suite
- ✅ Hot reload development setup

## Tech Stack

### Backend
- Framework: FastAPI (Python async web framework)
- Database: SQLite (file-based, no external DB required)
- ORM: SQLAlchemy with async support
- Text Processing: spaCy (en_core_web_lg model)
- Validation: Pydantic schemas
- Testing: pytest

### Frontend
- Framework: Angular 17+
- UI Library: Angular Material
- Styling: SCSS with custom enterprise theme
- State Management: Angular reactive forms
- Routing: Angular Router with lazy loading

### DevOps
- Containerization: Docker & Docker Compose
- Development: Hot reload for both frontend and backend
- API Docs: Automatic Swagger/OpenAPI documentation

## Architecture & Data Model

### Database Schema
```
contracts (SQLite table)
├── id: INTEGER (Primary Key)
├── filename: TEXT
├── content: TEXT (full contract text)
├── uploaded_at: DATETIME
└── sentences: One-to-many relationship

sentences (SQLite table)
├── id: INTEGER (Primary Key)
├── contract_id: INTEGER (Foreign Key)
├── text: TEXT
├── position: INTEGER
└── label: One-to-one relationship

clause_labels (SQLite table)
├── id: INTEGER (Primary Key)
├── sentence_id: INTEGER (Foreign Key)
├── clause_type_id: INTEGER (Foreign Key)
├── source: TEXT ('manual' or 'ai')
└── created_at: DATETIME

clause_types (SQLite table)
├── id: INTEGER (Primary Key)
├── name: TEXT (e.g., 'Confidentiality', 'Termination')
└── color: TEXT (hex color for UI)
```

### Key Design Decisions

1. SQLite Over PostgreSQL: Contracts are stored as text in database fields rather than separate files. This is intentional - normal contract text fits well within database TEXT fields and eliminates file system complexity.

2. Sentence-Level Granularity: Contracts are parsed into individual sentences for precise clause labeling, enabling detailed analysis.

3. Manual Labeling Workflow: Human expertise ensures accuracy over automated labeling, with AI assistance available for suggestions.

4. File-Based Storage: SQLite database file is mounted in Docker for persistence, keeping the architecture simple.

## Local Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (optional)

### Important: Startup Order
⚠️ Always start the backend first, then the frontend. The frontend makes immediate API calls on load, so the backend must be running before starting the frontend.

### Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_lg

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server (with API proxy to backend)
# NOTE: Only start this AFTER the backend is running
ng serve --proxy-config proxy.conf.json --host 0.0.0.0 --port 4200
```

Note: The `--proxy-config proxy.conf.json` flag is required to proxy API requests from the frontend (`/api/*`) to the backend server running on port 8000. Without this proxy, the frontend cannot communicate with the backend API.

### Access Application
- Frontend: http://localhost:4200
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Docker Run Steps

### Quick Start (Recommended)
```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Note: Docker Compose automatically starts the backend before the frontend due to the `depends_on` configuration, ensuring proper startup order. The frontend uses `proxy.conf.docker.json` for Docker networking.

### Development Workflow
```bash
# Rebuild after dependency changes
docker-compose up -d --build

# Access backend container
docker exec -it clausetracker_app bash

# Run tests
docker exec -it clausetracker_app pytest

# View SQLite database (copy to host)
docker cp clausetracker_app:/app/clausetracker.db ./backend/
```

## Test Instructions

### Backend Tests
```bash
cd backend

# Run all tests
pytest tests/test_api.py -v

# Run with coverage
pytest tests/test_api.py --cov=app --cov-report=html

# Run specific test
pytest tests/test_api.py::test_upload_contract_success -v
```

### Test Coverage
- ✅ Contract upload and parsing
- ✅ Clause type CRUD operations
- ✅ Sentence labeling and unlabeling
- ✅ Contract filtering by clause type
- ✅ Contract grouping by clause type
- ✅ Error handling and validation
- ✅ Full workflow integration tests

## API Overview

### Core Endpoints

#### Contracts
- `GET /api/contracts` - List contracts (with search, filtering, grouping)
- `POST /api/contracts` - Upload new contract
- `GET /api/contracts/{id}` - Get contract details
- `DELETE /api/contracts/{id}` - Delete contract

#### Clause Types
- `GET /api/clause-types` - List available clause types
- `POST /api/clause-types` - Create new clause type

#### Labeling
- `POST /api/sentences/{id}/label` - Label a sentence
- `DELETE /api/sentences/{id}/label` - Remove sentence label

### Query Parameters
- `search`: Filter contracts by filename
- `clause_type_id`: Filter contracts containing specific clause type
- `group_by_clause`: Group results by clause type (returns `ContractsByClauseType[]`)

## Design Decisions

### UI/UX Choices
- Enterprise Theme: Professional color scheme with subtle gradients and shadows
- Minimal Motion: Focus on readability over animations
- Contextual Labeling: Inline clause type badges instead of separate legends
- Responsive Design: Works on desktop and tablet devices

### Technical Choices
- SQLite: Simple, file-based database eliminates external dependencies
- spaCy: Industry-standard NLP library for sentence segmentation
- FastAPI: High-performance async framework with auto-generated docs
- Angular: Enterprise-grade frontend framework with strong typing

### Data Storage Decision
Important: Contracts are intentionally stored in the database as text fields, not as separate files on disk. This design choice is based on:

- Normal contract documents fit comfortably within database TEXT fields
- Eliminates file system complexity and permissions issues
- Enables full-text search capabilities
- Simplifies backup and migration processes
- Reduces infrastructure requirements

## Known Limitations

### Current Scope
- File Types: Only supports .txt and .md files
- Languages: English text only (spaCy en_core_web_lg model)
- AI Features: Manual labeling only (AI suggestions not implemented)
- Authentication: No user management or authentication
- Export: Basic contract download, no advanced reporting

### Performance Considerations
- Database: SQLite suitable for moderate contract volumes
- Text Processing: spaCy model loads on startup (~500MB RAM)
- Concurrent Users: Single-user application design

## Next Steps

### Potential Enhancements
- AI-Powered Labeling: Integrate ML models for clause type suggestions
- Multi-Language Support: Add support for additional languages
- User Management: Authentication and multi-user support
- Document Comparison: Side-by-side contract analysis
- Export Formats: PDF reports and Excel exports
- Audit Trail: Labeling history and user attribution

## Backend Scaling Techniques

To scale beyond single-user usage, consider these key extensions:

### Database Scaling
- Migrate from SQLite to PostgreSQL for concurrent access and better performance
- Implement connection pooling and read replicas for high-traffic scenarios
- Add database indexing on frequently queried fields (contract_id, clause_type_id, timestamps)

### Application Scaling
- Deploy multiple backend instances behind a load balancer
- Implement async processing for resource-intensive operations (contract parsing, bulk operations)
- Add Redis caching for frequently accessed data (clause types, contract metadata)

### Performance Optimizations
- Rate limiting and request throttling for API protection
- Pagination for large result sets
- Background job processing for long-running tasks
- Database query optimization and result caching

### Infrastructure Scaling
- Container orchestration (Kubernetes) for auto-scaling
- Object storage (S3/MinIO) for contract files at scale
- CDN integration for global file distribution
- Monitoring and logging for performance tracking

These extensions would support hundreds of concurrent users while maintaining response times.