# Mental Health Monitoring System (mHealth)

A comprehensive automated mental health monitoring system that conducts periodic phone calls to students, analyzes emotional states through voice sentiment analysis, and provides a dashboard for counselors to monitor student well-being.

## 🎯 Project Overview

This thesis project implements an end-to-end mental health monitoring solution for educational institutions. The system:

- **Automatically schedules and initiates phone calls** to students at configured intervals
- **Records conversations** using Exotel telephony integration
- **Analyzes emotional sentiment** from voice recordings using machine learning models
- **Provides a web dashboard** for counselors to monitor student mental health status
- **Flags at-risk students** based on sentiment analysis results
- **Manages call attempts and retry logic** for unsuccessful connections

## 🏗️ Architecture

### System Components (Microservices Architecture)

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Frontend      │◄────────┤   Backend API    │────────►│   PostgreSQL    │
│  (React +TS)    │  HTTP   │   (FastAPI)      │         │   Database      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                    │ │ │
                    ┌───────────────┘ │ └──────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌───────────────┐  ┌────────────┐  ┌──────────────┐
            │   Celery      │  │   Exotel   │  │    MinIO     │
            │   Workers     │  │  Telephony │  │   Storage    │
            └───────────────┘  └────────────┘  └──────────────┘
                    │                 │
                    │                 │
            ┌───────────────┐         │
            │   RabbitMQ    │         │
            │ Message Queue │         │
            └───────────────┘         │
                    │                 │
                    │                 │
                    ▼                 ▼
            ┌──────────────────────────────────┐
            │      ML Service (Separate)       │
            │  - Sentiment Analysis (PyTorch)  │
            │  - Emotion Classification        │
            │  - Audio Feature Processing      │
            └──────────────────────────────────┘
```

**Key Architectural Decision: Separate ML Service**

The machine learning inference is deployed as a **separate microservice** to enable:
- **Independent scaling**: Scale ML service based on inference load
- **Resource isolation**: GPU/CPU resources dedicated to ML workloads
- **Technology independence**: Different deployment strategies for ML models
- **Development agility**: Update models without redeploying main backend
- **Cost optimization**: Scale down ML service during low-demand periods

### Technology Stack

#### Backend
- **FastAPI** - Modern Python web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM for database operations
- **PostgreSQL** - Primary relational database
- **Alembic** - Database migration management
- **Celery** - Distributed task queue for asynchronous call processing
- **RabbitMQ** - Message broker for Celery tasks
- **MinIO** - S3-compatible object storage for audio recordings
- **httpx** - Async HTTP client for ML service communication
- **Exotel API** - Telephony integration for call management

#### ML Service (Microservice)
- **FastAPI** - REST API for ML inference endpoints
- **PyTorch + Transformers** - Deep learning frameworks for sentiment analysis
- **Wav2Vec2** - Pre-trained speech model for emotion detection
- **scikit-learn** - Legacy emotion classification model
- **Librosa** - Audio processing and feature extraction
- **Docker** - Containerized deployment for scalability

#### Frontend
- **React 19** - UI library with React Compiler
- **TypeScript** - Type-safe JavaScript
- **Material-UI (MUI)** - Component library and design system
- **Vite** - Fast build tool and dev server
- **TanStack Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Axios** - HTTP client for API communication

#### DevOps & Tools
- **Docker Compose** - Container orchestration
- **Python virtual environments** - Dependency isolation
- **ESLint** - Code linting
- **Uvicorn** - ASGI server

## 📁 Project Structure

```
mhealth/
├── docker-compose.yml         # Root Docker services definition
├── backend/                    # Backend application directory
│   ├── app/                    # Main application package
│   │   ├── api/               # API route modules
│   │   │   ├── auth_routes.py              # Authentication & authorization
│   │   │   ├── call_monitoring_routes.py   # Call status monitoring
│   │   │   ├── counsellor_routes.py        # Counselor-specific endpoints
│   │   │   ├── database_routes.py          # Database management
│   │   │   ├── frontend_routes.py          # Frontend configuration
│   │   │   ├── ml_routes.py               # ML service proxy endpoints
│   │   │   └── target_monitoring_routes.py # Target student tracking
│   │   │
│   │   ├── middleware/         # Custom middleware components
│   │   ├── services/          # Business logic services
│   │   │
│   │   ├── __init__.py
│   │   ├── auth_utilities.py   # JWT, password hashing utilities
│   │   ├── celery_config_exotel.py  # Celery task definitions
│   │   ├── config.py           # Environment configuration
│   │   ├── email_utils.py      # Email notification utilities
│   │   ├── main_exotel.py      # FastAPI application entry point
│   │   ├── ml_client.py        # HTTP client for ML microservice
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── schemas.py          # Pydantic validation schemas
│   │   ├── sql_db.py           # Database connection setup
│   │   └── targets_sample.csv  # Sample target data
│   │
│   ├── alembic/               # Database migrations
│   │   ├── versions/          # Migration scripts
│   │   ├── env.py             # Alembic environment config
│   │   └── script.py.mako     # Migration template
│   │
│   ├── alembic.ini            # Alembic configuration
│   ├── create_admin.py        # Admin user creation script
│   ├── get_recordings.py      # Utility to fetch recordings
│   ├── insert_targets.py      # Bulk target insertion script
│   ├── requirements.txt       # Python dependencies
│   └── reset_calls.py         # Database reset utility
│
├── ml-service/                # ML Microservice (Separate Deployment)
│   ├── app/                   # ML service application
│   │   ├── services/         # ML inference services
│   │   │   ├── vad_sentiment.py    # VAD-based sentiment analysis
│   │   │   ├── emotion_model.py    # Legacy sklearn emotion model
│   │   │   └── audio_utils.py      # Audio feature extraction
│   │   │
│   │   ├── __init__.py
│   │   ├── config.py          # ML service configuration
│   │   └── main.py            # FastAPI ML service entry point
│   │
│   ├── model_store/           # Trained ML model files
│   │   ├── best_model.pt      # Current production model
│   │   └── emotion_model.joblib  # Legacy sklearn model
│   │
│   ├── Dockerfile             # ML service container definition
│   ├── requirements.txt       # ML-specific Python dependencies
│   ├── .env.example           # Example environment variables
│   └── README.md              # ML service documentation
│
├── frontend2/                 # Frontend application directory
│   ├── src/                   # Source code
│   │   ├── api/              # API client functions
│   │   ├── assets/           # Static assets (images, icons)
│   │   ├── components/       # Reusable React components
│   │   ├── constants/        # Application constants
│   │   ├── contexts/         # React context providers
│   │   ├── layouts/          # Page layout components
│   │   ├── lib/              # Utility libraries
│   │   ├── pages/            # Page components
│   │   │   ├── AboutPage.tsx
│   │   │   ├── CallManagementPage.tsx
│   │   │   ├── CallStatusDashboard.tsx
│   │   │   ├── DatabaseManagementPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── ForgotPasswordPage.tsx
│   │   │   ├── ResetPasswordPage.tsx
│   │   │   └── SystemHealthPage.tsx
│   │   ├── utils/            # Helper functions
│   │   ├── App.tsx           # Root application component
│   │   ├── main.tsx          # Application entry point
│   │   └── theme.ts          # MUI theme configuration
│   │
│   ├── public/               # Public static files
│   ├── eslint.config.js      # ESLint configuration
│   ├── index.html            # HTML entry point
│   ├── package.json          # NPM dependencies
│   ├── tsconfig.json         # TypeScript configuration
│   └── vite.config.ts        # Vite build configuration
│
└── paper-replica.ipynb       # Jupyter notebook for research/analysis

```

## 🗃️ Database Schema

### Core Tables

#### **Targets**
Stores information about students being monitored.

| Column          | Type   | Description                    |
|-----------------|--------|--------------------------------|
| Target_Id       | UUID   | Primary key                    |
| Name            | String | Student name                   |
| Roll_No         | String | Unique student roll number     |
| Phone_No        | String | Contact phone number           |
| Department_Name | String | Academic department            |
| Program         | String | Study program (BTech, MTech)   |

#### **Calls**
Records all call attempts and their outcomes.

| Column         | Type     | Description                          |
|----------------|----------|--------------------------------------|
| Call_Id        | UUID     | Primary key                          |
| Call_Sid       | String   | Exotel call session ID               |
| Target_Id      | UUID     | Foreign key to Targets               |
| Model_Id       | String   | Foreign key to Models                |
| Scheduled_Time | DateTime | When Celery scheduled the call       |
| Started_Time   | DateTime | When call execution began            |
| Emotion_Id     | String   | Foreign key to Emotions (nullable)   |
| Status         | Enum     | Call status (see below)              |
| Duration       | Integer  | Call duration in seconds             |
| Recording_Url  | String   | MinIO URL to audio recording         |

**Call Status Enum:**
1. `Call Scheduled` - Initial status
2. `failed` - Call failed
3. `busy` - Target was busy
4. `no-answer` - No answer from target
5. `Message Not Conveyed` - Call completed but no recording
6. `Message Conveyed But Not Processed` - Recording exists, awaiting ML analysis
7. `Message Conveyed And Processed` - Sentiment analysis completed

#### **Emotions**
Emotion classification labels.

| Column     | Type   | Description              |
|------------|--------|--------------------------|
| Emotion_Id | String | Primary key (E1, E2...)  |
| Emotion    | String | Emotion label            |

#### **Models**
ML model version tracking.

| Column        | Type   | Description              |
|---------------|--------|--------------------------|
| Model_Id      | String | Primary key (M1, M2...)  |
| Model_Name    | String | Model name               |
| Model_Version | String | Version identifier       |
| Model_Details | Text   | Additional metadata      |

#### **Admins**
System administrators/counselors.

| Column     | Type   | Description         |
|------------|--------|---------------------|
| Admin_Id   | UUID   | Primary key         |
| Email      | String | Unique email        |
| Password   | String | Hashed password     |

## 🔌 API Routes

### Authentication
- `POST /api/auth/login` - Admin login
- `POST /api/auth/signup` - Create admin account
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token

### Call Management
- `GET /api/calls/status` - Get all call statuses
- `GET /api/calls/target/{target_id}` - Get calls for specific target
- `POST /api/calls/initiate` - Manually trigger calls
- `GET /api/calls/monitoring` - Real-time call monitoring

### Student Targets
- `GET /api/targets` - List all targets
- `POST /api/targets` - Add new target
- `PUT /api/targets/{id}` - Update target
- `DELETE /api/targets/{id}` - Remove target
- `POST /api/targets/bulk-upload` - CSV bulk upload

### ML/Sentiment Analysis
- `POST /api/ml/sentiment` - Analyze audio sentiment
- `GET /api/ml/models` - List available models

### Database Management
- `POST /api/database/reset` - Reset database
- `GET /api/database/backup` - Export database backup
- `POST /api/database/restore` - Restore from backup

### Counselor Dashboard
- `GET /api/counselor/dashboard` - Overview statistics
- `GET /api/counselor/flagged-targets` - At-risk students
- `GET /api/counselor/reports` - Generate reports

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- RabbitMQ
- MinIO
- Exotel account (for production calls)
- Docker & Docker Compose (recommended for deployment)

### Quick Start with Docker Compose (Recommended)

The easiest way to run the entire system:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mhealth
   ```

2. **Set up environment variables:**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   
   # ML Service
   cp ml-service/.env.example ml-service/.env
   ```

3. **Copy ML model files:**
   ```bash
   # Ensure best_model.pt is in ml-service/model_store/
   mkdir -p ml-service/model_store
   # Copy your trained model file here
   ```

4. **Start all services:**
   ```bash
   docker compose up -d
   ```

   This starts:
   - PostgreSQL database
   - RabbitMQ message broker
   - MinIO object storage
   - ML Service (on port 8001)
   - pgAdmin (optional, on port 5050)

5. **Run database migrations:**
   ```bash
   docker compose exec backend-api alembic upgrade head
   ```

6. **Start backend services:**
   ```bash
   # Start FastAPI server
   uvicorn app.main_exotel:app --reload --host 0.0.0.0 --port 8000
   
   # In separate terminals:
   # Start Celery worker
   celery -A app.celery_config_exotel worker --loglevel=info
   
   # Start Celery beat
   celery -A app.celery_config_exotel beat --loglevel=info
   ```

7. **Start frontend:**
   ```bash
   cd frontend2
   npm install
   npm run dev
   ```

Access the application at `http://localhost:5173`

### ML Service Setup (Separate Deployment)

The ML service can be deployed independently:

**Option 1: Docker (Recommended)**
```bash
cd ml-service
docker build -t mhealth-ml-service .
docker run -p 8001:8001 \
  -v $(pwd)/model_store:/app/model_store \
  -e ML_SERVICE_HOST=0.0.0.0 \
  -e ML_SERVICE_PORT=8001 \
  mhealth-ml-service
```

**Option 2: Local Development**
```bash
cd ml-service
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Test ML Service:**
```bash
curl -X POST "http://localhost:8001/api/ml/sentiment" \
  -F "file=@sample_audio.mp3"
```

### Manual Setup (Development)

For development without Docker:

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create `.env` file with:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/mhealth
   EXOTEL_SID=your_sid
   EXOTEL_API_KEY=your_key
   EXOTEL_API_TOKEN=your_token
   EXOTEL_PHONE_NUMBER=your_number
   JWT_SECRET_KEY=your_secret
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   ML_SERVICE_URL=http://localhost:8001
   ```

5. **Start infrastructure services:**
   ```bash
   docker compose -f ../docker-compose.yml up -d postgres rabbitmq minio
   ```

6. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Create admin user:**
   ```bash
   python create_admin.py
   ```

8. **Start Celery worker:**
   ```bash
   celery -A app.celery_config_exotel worker --loglevel=info
   ```

9. **Start Celery beat (scheduler):**
   ```bash
   celery -A app.celery_config_exotel beat --loglevel=info
   ```

10. **Start FastAPI server:**
    ```bash
    uvicorn app.main_exotel:app --reload --host 0.0.0.0 --port 8000
    ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend2
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure API endpoint:**
   Update `src/api/config.ts` with backend URL

4. **Start development server:**
   ```bash
   npm run dev
   ```

5. **Access application:**
   Open browser to `http://localhost:5173`

## 🔄 How It Works

### Call Workflow

1. **Scheduling**: Celery Beat triggers `initiate_calls_for_all_targets` periodic task
2. **Call Creation**: System creates call records with `Call Scheduled` status
3. **Exotel Integration**: Celery worker initiates calls via Exotel API
4. **Call Monitoring**: Exotel webhooks update call status in real-time
5. **Recording Capture**: Completed calls trigger recording download from Exotel
6. **Storage**: Audio files stored in MinIO with metadata in PostgreSQL
7. **ML Service Call**: Backend sends audio to ML microservice via HTTP
8. **Sentiment Analysis**: ML service analyzes audio using PyTorch model
9. **Emotion Classification**: Results returned to backend with VAD coordinates
10. **Database Update**: Emotion and sentiment stored in call record
11. **Dashboard Refresh**: Counselor dashboard reflects latest emotional states
12. **Flagging**: Students with concerning patterns flagged for intervention

### Sentiment Analysis Pipeline (ML Service)

1. **Audio Preprocessing**: Conversion to 16kHz mono, noise reduction
2. **Feature Extraction**: Wav2Vec2 feature extractor processes audio
3. **Model Inference**: LSTM-based model predicts VAD coordinates
4. **Emotion Mapping**: VAD mapped to emotion labels using distance metrics
5. **Sentiment Classification**: Emotion mapped to Positive/Negative/Neutral
6. **Response**: JSON with emotion, sentiment, VAD, and timing metrics

## 🔐 Security Features

- **JWT Authentication**: Secure token-based auth for API access
- **Password Hashing**: Bcrypt for admin password storage
- **CORS Protection**: Configured allowed origins
- **Environment Variables**: Sensitive config externalized
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **Rate Limiting**: Protection against API abuse (via middleware)

## 📊 Key Features

### For Counselors
- **Real-time Dashboard**: Monitor all active calls and student status
- **Historical Data**: View call history and emotional trends
- **Flagged Alerts**: Automatic identification of at-risk students
- **Bulk Management**: Upload/manage student lists via CSV
- **Report Generation**: Export data for analysis

### For System Administrators
- **Database Management**: Backup, restore, and reset capabilities
- **User Management**: Create/manage counselor accounts
- **System Health**: Monitor service status and performance
- **Call Configuration**: Adjust frequency, times, and retry logic
- **Model Management**: Update ML models and track versions

## 🧪 Testing

Run backend tests:
```bash
cd backend
pytest
```

Run frontend tests:
```bash
cd frontend2
npm test
```

## 📝 Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## � Deployment Strategies

### Microservices Deployment

#### Production Deployment with Docker Compose

```bash
# Production docker-compose.yml setup
cd mhealth
docker compose up -d --build
```

#### Separate ML Service Deployment

**Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-service
spec:
  replicas: 3  # Scale based on inference load
  selector:
    matchLabels:
      app: ml-service
  template:
    metadata:
      labels:
        app: ml-service
    spec:
      containers:
      - name: ml-service
        image: mhealth-ml-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: ML_SERVICE_HOST
          value: "0.0.0.0"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

**Cloud Deployment Options:**
- **AWS**: ECS/Fargate for ML service, RDS for PostgreSQL, S3 for recordings
- **Azure**: Container Instances, Azure Database for PostgreSQL, Blob Storage
- **GCP**: Cloud Run for ML service, Cloud SQL, Cloud Storage

#### Scalability Considerations

**ML Service Scaling:**
- Horizontal: Deploy multiple ML service instances behind load balancer
- Vertical: Increase CPU/memory for GPU-accelerated inference
- Auto-scaling: Scale based on request queue depth

**Backend Scaling:**
- Stateless design allows horizontal scaling
- Celery workers can scale independently
- Use Redis for session management if needed

**Database Optimization:**
- Read replicas for reporting queries
- Connection pooling (PgBouncer)
- Partitioning for large call tables

### Environment Configuration

**Development:**
- ML Service: Local Python process
- Database: Local PostgreSQL or Docker
- Message Queue: Local RabbitMQ

**Staging:**
- ML Service: Docker container
- Managed database service
- Managed message broker

**Production:**
- ML Service: Kubernetes deployment with auto-scaling
- High-availability database with backups
- Managed RabbitMQ cluster
- CDN for frontend assets
- SSL/TLS everywhere

## 🐛 Troubleshooting

### Common Issues

**ML Service Connection Errors:**
- Check ML service is running: `curl http://localhost:8001/health`
- Verify ML_SERVICE_URL in backend `.env`
- Check network connectivity between services
- Review ML service logs: `docker logs mhealth-ml-service`

**ML Model Loading Failures:**
- Ensure `best_model.pt` exists in `ml-service/model_store/`
- Check file permissions on model directory
- Verify PyTorch version compatibility
- Check available memory (model requires ~2GB)

**Celery workers not starting:**
- Ensure RabbitMQ is running: `docker ps`
- Check broker URL in config
- Verify Celery dependencies installed

**Calls not going through:**
- Verify Exotel credentials in `.env`
- Check Exotel account balance
- Validate phone number format (+91XXXXXXXXXX)

**MinIO connection errors:**
- Confirm MinIO is running on correct port
- Verify access credentials match `.env`
- Check bucket exists: `mc ls myminio/recordings`

**Sentiment Analysis Timeout:**
- Increase ML_SERVICE_TIMEOUT in backend config
- Check ML service resource allocation
- Consider using faster CPU or GPU
- Reduce MAX_AUDIO_DURATION if files are too large

**Docker Container Issues:**
- Check logs: `docker compose logs -f ml-service`
- Verify volume mounts: `docker inspect mhealth-ml-service`
- Rebuild image: `docker compose build --no-cache ml-service`
- Check port conflicts: `netstat -an | findstr 8001`

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Exotel API Reference](https://developer.exotel.com/)
- [SQLAlchemy ORM Guide](https://docs.sqlalchemy.org/)

## 👥 Contributors

This project is part of a thesis at IIT Gandhinagar.

## 📄 License

This project is developed for academic purposes.

---

**Note**: This is a research project. Ensure compliance with privacy regulations and institutional ethics guidelines when deploying in production environments. Always obtain informed consent from participants.
