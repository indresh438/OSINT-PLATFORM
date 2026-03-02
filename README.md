# 🔍 OSINT Intelligence Platform

A private, scalable, and modular OSINT (Open Source Intelligence) platform that runs entirely offline on your Linux system. Designed for ingesting, normalizing, indexing, and correlating large datasets from various sources.

## 🎯 Features

### Core Capabilities
- **Massive Data Ingestion**: Import MySQL dumps with hundreds of tables and lakhs of rows
- **Smart Normalization**: Automatically normalize data into standard fields (email, IP, domain, username, phone)
- **Lightning-Fast Search**: Full-text search powered by Elasticsearch
- **Flexible Storage**: Semi-structured data storage in MongoDB
- **Relationship Mapping**: Graph-based entity correlation with Neo4j
- **Async Processing**: Background import jobs with Celery + Redis
- **Interactive Dashboard**: Real-time search and visualization with Streamlit

### Offline-First Design
- Runs entirely on your local machine
- No internet connection required for core operations
- Privacy-focused: your data never leaves your system

### Future-Ready Architecture
- Modular design for easy extension
- Ready for online data collectors (Twitter, Shodan, WHOIS)
- Threat intelligence enrichment ready
- User authentication framework prepared
- Export capabilities (PDF/CSV)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                      │
│                    (Frontend - Port 8501)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                    (API - Port 8000)                         │
└──┬────────┬────────┬────────┬────────┬──────────────────────┘
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
┌──────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌────────┐
│MySQL │ │MongoDB │ │ ES   │ │Neo4j │ │ Redis  │
│:3306 │ │:27017  │ │:9200 │ │:7687 │ │ :6379  │
└──────┘ └────────┘ └──────┘ └──────┘ └────────┘
   │                                      │
   └──────────────────┬───────────────────┘
                      ▼
              ┌──────────────┐
              │ Celery Worker│
              │  (Async Jobs)│
              └──────────────┘
```

### Component Breakdown

1. **MySQL** - Source database for existing dumps
2. **MongoDB** - Semi-structured data and audit trails
3. **Elasticsearch** - Full-text search and indexing
4. **Neo4j** - Graph database for relationship mapping
5. **Redis** - Message broker for Celery
6. **FastAPI** - REST API backend
7. **Celery** - Async task processing
8. **Streamlit** - Interactive web dashboard

## 🚀 Quick Start

### Prerequisites

- Linux system (tested on Ubuntu 22.04+)
- Docker and Docker Compose installed
- At least 2 TB SSD storage
- 8 GB RAM minimum (16 GB recommended)
- Python 3.11+ (if running without Docker)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /home/sansat/Desktop/local_osint
   ```

2. **Create necessary directories:**
   ```bash
   mkdir -p data/{mysql,mongodb,elasticsearch,neo4j,redis,mysql_dumps} logs
   ```

3. **Set proper permissions:**
   ```bash
   chmod -R 777 data logs
   ```

4. **Start all services:**
   ```bash
   docker-compose up -d
   ```

5. **Wait for services to initialize (2-3 minutes):**
   ```bash
   docker-compose logs -f
   ```

6. **Initialize database indices:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/import/initialize
   ```

7. **Access the dashboard:**
   - Frontend: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - Neo4j Browser: http://localhost:7474

## 📊 Usage Guide

### 1. Import MySQL Data

#### Place your MySQL dump file:
```bash
cp your_database.sql data/mysql_dumps/
```

#### Start import via API:
```bash
curl -X POST "http://localhost:8000/api/v1/import/mysql" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "leaked_db_2023",
    "dump_file": "/dumps/your_database.sql",
    "field_mapping": {
      "users": {
        "email_addr": "email",
        "user_name": "username",
        "ip_address": "ip"
      }
    }
  }'
```

#### Or use the Streamlit dashboard:
1. Go to http://localhost:8501
2. Navigate to "Import Data" tab
3. Fill in the form and submit

### 2. Search Entities

#### Via API:
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "example@domain.com",
    "limit": 100
  }'
```

#### Via Dashboard:
1. Go to "Search" tab
2. Enter your query
3. Filter by entity type if needed
4. View results with full metadata

### 3. Explore Relationships

```bash
curl "http://localhost:8000/api/v1/entities/email:user@example.com/relationships?depth=2"
```

Or use the "Relationships" tab in the dashboard.

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

- **MySQL**: Root password, database name
- **MongoDB**: Admin credentials
- **Elasticsearch**: Memory settings (adjust based on your system)
- **Neo4j**: Authentication credentials
- **Batch Size**: Adjust in backend config for performance

### Field Mapping

The system auto-detects common field names, but you can provide custom mappings:

```json
{
  "table_name": {
    "source_field": "standard_field",
    "email_column": "email",
    "ip_col": "ip",
    "domain_field": "domain",
    "user_name": "username",
    "phone_num": "phone"
  }
}
```

Standard fields: `email`, `ip`, `domain`, `username`, `phone`

## 📁 Project Structure

```
local_osint/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application
│   │   ├── config.py                # Configuration
│   │   ├── database.py              # Database connections
│   │   ├── models.py                # Pydantic models
│   │   ├── normalizer.py            # Data normalization
│   │   ├── elasticsearch_manager.py # ES operations
│   │   ├── mongodb_manager.py       # MongoDB operations
│   │   ├── neo4j_manager.py         # Neo4j operations
│   │   ├── celery_app.py            # Celery configuration
│   │   ├── tasks.py                 # Async tasks
│   │   └── routers/
│   │       ├── health.py            # Health check endpoints
│   │       ├── search.py            # Search endpoints
│   │       ├── entities.py          # Entity endpoints
│   │       └── import_router.py     # Import endpoints
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py                       # Streamlit dashboard
│   └── Dockerfile
├── docker-compose.yml
├── data/                            # Persistent data
│   ├── mysql/
│   ├── mongodb/
│   ├── elasticsearch/
│   ├── neo4j/
│   ├── redis/
│   └── mysql_dumps/                 # Place your dumps here
├── logs/                            # Application logs
└── README.md
```

## 🔍 API Endpoints

### Health & Status
- `GET /api/v1/health` - System health check
- `GET /api/v1/stats` - System statistics

### Search
- `POST /api/v1/search` - Advanced search
- `GET /api/v1/search/quick?q=query` - Quick search
- `GET /api/v1/search/by-value/{value}` - Exact match

### Entities
- `GET /api/v1/entities/{entity_id}/relationships` - Get relationships
- `GET /api/v1/entities/{entity_id}/connections/{target_id}` - Find connections
- `GET /api/v1/entities/value/{value}` - Get by value

### Import
- `POST /api/v1/import/mysql` - Start import job
- `GET /api/v1/import/status/{job_id}` - Get job status
- `GET /api/v1/import/jobs` - List all jobs
- `POST /api/v1/import/initialize` - Initialize indices

Full API documentation: http://localhost:8000/docs

## 🎯 Data Flow

1. **Ingestion**: MySQL dump → Import task
2. **Normalization**: Raw records → Standard entity format
3. **Storage**: 
   - MongoDB: Full records + audit trail
   - Elasticsearch: Indexed entities for search
   - Neo4j: Graph nodes + relationships
4. **Query**: Search/API → Results from Elasticsearch
5. **Enrichment**: Entity → Related entities via Neo4j

## 🚀 Performance Tuning

### For Large Datasets (> 1M records)

1. **Increase Elasticsearch memory:**
   ```yaml
   # In docker-compose.yml
   ES_JAVA_OPTS: "-Xms4g -Xmx4g"
   ```

2. **Adjust batch size:**
   ```python
   # In backend/app/config.py
   BATCH_SIZE = 5000  # Default: 1000
   ```

3. **Increase Celery workers:**
   ```yaml
   # In docker-compose.yml
   command: celery -A app.celery_app worker --concurrency=8
   ```

4. **Optimize Neo4j:**
   ```yaml
   NEO4J_server_memory_heap_max__size: 4G
   ```

## 🔮 Future Extensions

### Online Data Collectors (Planned)
- Twitter/X API integration
- Shodan scanner
- WHOIS lookup
- DNS enumeration
- Subdomain discovery
- Certificate transparency logs
- Breach data APIs

### Enrichment Modules (Planned)
- IP geolocation
- Domain reputation scoring
- Email breach checking
- Hash identification
- Phone number validation
- Username OSINT

### Advanced Features (Planned)
- User authentication & RBAC
- Multi-tenancy support
- PDF/CSV report generation
- Scheduled scans
- Alert system
- Data retention policies
- Encryption at rest

## 🛠️ Troubleshooting

### Services not starting
```bash
docker-compose down
docker-compose up -d --force-recreate
```

### Elasticsearch fails to start
- Check available disk space
- Increase `vm.max_map_count`:
  ```bash
  sudo sysctl -w vm.max_map_count=262144
  echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
  ```

### Import job stuck
- Check Celery worker logs:
  ```bash
  docker-compose logs celery_worker
  ```
- Check Redis connection
- Verify MySQL dump file format

### Search not working
- Verify Elasticsearch is running
- Check if index exists:
  ```bash
  curl http://localhost:9200/_cat/indices
  ```
- Reinitialize indices:
  ```bash
  curl -X POST http://localhost:8000/api/v1/import/initialize
  ```

## 📊 Monitoring

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Application logs
tail -f logs/osint_platform.log
```

### Check service health:
```bash
curl http://localhost:8000/api/v1/health
```

### Monitor import jobs:
- Via API: `GET /api/v1/import/jobs`
- Via Dashboard: "Import Data" → "Monitor Jobs" tab

## 🔒 Security Considerations

1. **Change default passwords** in `docker-compose.yml`
2. **Restrict network access** using firewall rules
3. **Use VPN** if accessing remotely
4. **Encrypt volumes** for sensitive data
5. **Regular backups** of data directories
6. **Monitor logs** for suspicious activity

## 📝 License

This project is for educational and personal use. Ensure compliance with data protection laws and regulations in your jurisdiction.

## 🤝 Contributing

This is a personal project. Future contributions guidelines will be added.

## 📧 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review Docker container logs
3. Check API documentation at `/docs`

## 🎓 Learning Resources

- **Elasticsearch**: https://www.elastic.co/guide
- **Neo4j**: https://neo4j.com/docs/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Celery**: https://docs.celeryq.dev/

---

**Version**: 0.1.0  
**Last Updated**: October 2025  
**Status**: Production-Ready Beta
