# 🎯 OSINT Platform — Theory & Concepts Guide

> A code-free, theory-based explanation of every component in the platform.  
> Written for understanding **what** each piece does and **why** it exists.

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Module 1: Infrastructure & Containerization](#module-1-infrastructure--containerization)
3. [Module 2: Backend API Layer](#module-2-backend-api-layer)
4. [Module 3: Data Processing Pipeline](#module-3-data-processing-pipeline)
5. [Module 4: Multi-Database Storage](#module-4-multi-database-storage)
6. [Module 5: Frontend Dashboard](#module-5-frontend-dashboard)
7. [Module 6: Operations & Monitoring](#module-6-operations--monitoring)
8. [How Everything Connects](#how-everything-connects)

---

## Platform Overview

### What Is This Platform?

This is an **OSINT (Open-Source Intelligence) Platform** — a system designed to ingest large datasets (typically leaked or publicly available databases), extract meaningful entities like emails, IP addresses, usernames, phone numbers, and domains, and make them searchable and interconnected.

### The Core Problem It Solves

Imagine you have 25 different database dumps, each with different table structures, different column names, and millions of rows. You want to:

- **Search** across all of them instantly for a specific email or IP
- **Discover connections** — for example, which usernames are tied to which emails, and which IPs those emails logged in from
- **Visualize relationships** between entities in a graph format
- **Import new databases** without writing custom code for each one

This platform automates all of that.

### The 30-Second Summary

Raw SQL dumps go in → The system auto-detects what each column contains → Entities are extracted, normalized, and stored in 4 specialized databases → Users search and explore through a web dashboard.

---

## Module 1: Infrastructure & Containerization

### What Is Containerization and Why Use It?

The platform uses **Docker containers** — lightweight, isolated environments that package an application with all its dependencies. Think of each container as a sealed box containing one service and everything it needs to run.

**Why not just install everything directly on the machine?**

- **Isolation**: MySQL, MongoDB, Elasticsearch, Neo4j, and Redis all run independently. If one crashes, others keep running.
- **Reproducibility**: Anyone can start the entire platform with a single command, regardless of their operating system or what's already installed.
- **Port conflicts**: Your machine might already have MySQL on port 3306. Containers let us remap to custom ports (3307, 27018, etc.) without affecting existing services.
- **Cleanup**: Want to start fresh? Destroy all containers and recreate them. No leftover files or configurations polluting your system.

### The 9 Containers

The platform runs 9 containers, divided into two categories:

**Data Services (5 containers):**

| Container | What It Is | Why We Need It |
|-----------|------------|----------------|
| **MySQL** | Relational database | Holds the original imported data (SQL dumps are loaded here first) |
| **MongoDB** | Document database | Stores normalized entities and raw records with flexible schema |
| **Elasticsearch** | Search engine | Provides millisecond full-text search across millions of records |
| **Neo4j** | Graph database | Maps and traverses relationships between entities |
| **Redis** | In-memory cache | Acts as message broker for background jobs and caches frequent queries |

**Application Services (4 containers):**

| Container | What It Is | Why We Need It |
|-----------|------------|----------------|
| **Backend** | FastAPI web server | Provides the REST API that all other components talk to |
| **Celery Worker** | Background task processor | Handles long-running imports without blocking the API |
| **Celery Beat** | Task scheduler | Triggers periodic maintenance tasks on a schedule |
| **Frontend** | Streamlit web app | The visual dashboard users interact with in their browser |

### Networking

All 9 containers sit on a shared **virtual network** called `osint_network`. This means:

- Containers can talk to each other **by name** (the backend calls `mysql` instead of an IP address)
- The outside world can only reach containers through **published ports** (8000 for API, 8501 for dashboard)
- Container-to-container traffic never leaves the virtual network — it's fast and secure

### Data Persistence

Each database container maps a **volume** — a directory on your host machine — to its internal data directory. This means:

- If you stop and restart containers, your data survives
- If you destroy and recreate containers, your data still survives (it's on disk, not in the container)
- You can back up data by simply copying the `data/` folder

### Port Strategy

Every service uses a **non-standard port** to avoid conflicts:

| Standard Port | Our Port | Reason |
|--------------|----------|--------|
| 3306 | 3307 | Host may have MySQL |
| 27017 | 27018 | Host may have MongoDB |
| 9200 | 9201 | Host may have Elasticsearch |
| 7474 / 7687 | 7475 / 7688 | Host may have Neo4j |
| 6379 | 6380 | Host may have Redis |

---

## Module 2: Backend API Layer

### What Is the Backend?

The backend is a **REST API** built with FastAPI — a modern Python web framework. It serves as the **central nervous system** of the platform. Nothing happens without going through it:

- The frontend sends requests to it
- Import jobs are triggered through it
- Search queries pass through it
- Health checks are performed by it

### Why a Separate API Layer?

Instead of having the frontend talk directly to 5 databases, everything goes through one API. This provides:

- **Single point of entry**: Only one URL to secure, monitor, and rate-limit
- **Abstraction**: The frontend doesn't need to know which database holds what — it just asks the API
- **Fallback logic**: If Elasticsearch is down, the API automatically falls back to MongoDB for search. The frontend doesn't even notice
- **Validation**: All incoming data is validated before reaching any database

### The 4 Routers

The API is organized into 4 logical groups (routers):

**1. Health Router** — "Is the system alive?"
- Pings all 5 databases and reports which ones are responding
- Returns overall status: healthy (all up), degraded (some down), or unhealthy (all down)
- Also provides aggregated statistics from across all databases

**2. Search Router** — "Find entities matching this query"
- Accepts a search query with optional filters (entity type, source, deduplication)
- Sends the query to Elasticsearch first (fastest)
- If Elasticsearch fails, falls back to MongoDB (slower but reliable)
- Supports exact match, partial match, fuzzy match (handles typos), and wildcard patterns

**3. Entities Router** — "Tell me about this specific entity"
- Looks up a single entity by its ID or value
- Retrieves relationship data from Neo4j (who is connected to whom)
- Can find the shortest path between any two entities in the graph

**4. Import Router** — "Bring in new data"
- Accepts import requests (which database to import, which tables, field mappings)
- Doesn't process the import directly — instead, it queues a background job via Celery
- Provides status updates on running and completed import jobs

### Configuration Management

All settings (database hosts, ports, passwords, feature flags) are managed through a single `Settings` class. This class:

- Has sensible **default values** for local development
- Reads **environment variables** from Docker (overriding defaults)
- Can also read from a `.env` file
- Is instantiated once and shared across the entire application

### Connection Management

A **DatabaseManager** class handles connections to all 5 databases using the **Singleton pattern** — only one instance exists in the entire application. This prevents:

- Opening too many connections (connection pool exhaustion)
- Reconnecting on every request (wastes time)
- Forgetting to close connections (memory leaks)

It uses **context managers** for MySQL and Neo4j, which automatically close connections after use, even if an error occurs.

### Data Models

The platform uses **Pydantic models** — Python classes that define the exact shape of data. These serve three purposes:

1. **Validation**: Incoming API requests are automatically checked. If a required field is missing or has the wrong type, the API returns a clear error
2. **Documentation**: FastAPI uses these models to auto-generate interactive API docs (Swagger UI)
3. **Serialization**: Converting between Python objects, JSON, and database records

The key models are:

- **OsintEntity**: Represents a single entity (email, IP, domain, username, or phone) with its metadata
- **SearchQuery**: What the user wants to search for, with filters and pagination
- **SearchResult**: What comes back from a search — a list of entities plus metadata like search time
- **ImportJob**: Tracks the status of a data import (pending, running, completed, or failed)
- **HealthCheck**: The response from the health endpoint — each service's status

---

## Module 3: Data Processing Pipeline

### What Is ETL?

ETL stands for **Extract, Transform, Load** — a standard pattern for moving data from one system to another:

1. **Extract**: Pull raw data out of the source (MySQL dump files)
2. **Transform**: Clean it, normalize it, detect entity types
3. **Load**: Push the processed data into the target databases (MongoDB, Elasticsearch, Neo4j)

### The Import Process (Step by Step)

**Step 1: SQL Dump Ingestion**

SQL dump files (`.sql`) are placed in the `data/mysql_dumps/` directory. When an import is triggered, the system:

- Creates a new MySQL database with the source name
- Removes any `DEFINER` clauses from the dump (these cause permission errors on different servers)
- Imports the dump into MySQL using the native MySQL client

**Step 2: Table Discovery**

Once the dump is imported, the system lists all tables in the database. If the user specified particular tables, only those are processed. Otherwise, all tables are included.

**Step 3: Auto Field Detection**

This is one of the platform's most powerful features. Instead of requiring manual configuration for each database, the system **automatically detects** what each column contains by analyzing column names.

It scans column names for keywords:

- Column named `user_email`, `email_address`, or `mail` → detected as **email**
- Column named `ip_address`, `remote_ip`, or `login_ip` → detected as **IP**
- Column named `username`, `login`, or `user_name` → detected as **username**
- Column named `phone`, `mobile`, or `telephone` → detected as **phone**
- Column named `domain`, `hostname`, or `website` → detected as **domain**

Columns that don't match any keyword (like `id`, `created_at`, `status`) are skipped.

Users can also provide a **manual field mapping** via the API, which overrides auto-detection.

**Step 4: Entity Type Detection (Regex)**

Even after field detection, the system **verifies** each value using regular expression patterns:

- **Email**: Must contain `@` with valid domain structure
- **IP**: Must be 4 groups of 1-3 digits separated by dots (e.g., `192.168.1.1`)
- **Phone**: Must start with optional `+`, followed by country code and digits (E.164 format)
- **Hash**: Must be a hexadecimal string of exactly 32, 40, 64, or 128 characters (MD5, SHA1, SHA256, SHA512)
- **Domain**: Must have valid domain name structure with at least one dot
- **Username**: The default fallback — anything that doesn't match the above patterns

The order of checking matters. For example, `1.2.3.4` could technically match a domain pattern, so the IP check runs first.

**Step 5: Record Normalization**

Each row from MySQL is transformed into one or more **OsintEntity** objects. A single row might produce multiple entities — for instance, a row with both an email and an IP address creates two separate entities, each with a reference back to the original record.

Every entity gets:
- A **type** (email, ip, domain, username, phone)
- A **value** (the actual data)
- A **source** (which database it came from)
- A **unique ID** in the format `type:value` (e.g., `email:alice@gmail.com`)
- A copy of the **original raw record** for reference

**Step 6: Fan-Out to Storage**

Each batch of normalized entities is simultaneously stored in three databases:

- **MongoDB**: Gets both the normalized entities and the raw original records (archival)
- **Elasticsearch**: Gets the entities indexed for full-text search
- **Neo4j**: Gets each entity as a graph node, with automatic relationships created between related entities

### Batching

Records are processed in **batches of 1,000** to balance:
- **Memory**: Don't load millions of rows into memory at once
- **Performance**: Bulk database operations are far faster than individual inserts
- **Progress tracking**: After each batch, the import job's progress is updated

### Background Processing (Celery)

Imports can take minutes or hours. Running them directly in the API request would:
- Block the API from serving other requests
- Risk timeout errors
- Give no way to check progress

Instead, the API **queues** import tasks using **Celery** — a distributed task queue. Here's the flow:

1. The API receives an import request
2. It creates an import job record in MongoDB (status: "pending")
3. It sends a task message to Redis (the message broker)
4. A Celery worker picks up the message and starts processing
5. As the worker processes batches, it updates the job status in MongoDB
6. The API can report progress at any time by reading the job status from MongoDB

Celery runs **4 concurrent workers**, meaning 4 imports can run simultaneously. Each worker restarts after processing 50 tasks to prevent memory leaks from long-running processes.

Tasks are routed to **separate queues**: import tasks go to the `imports` queue, and batch processing tasks go to the `processing` queue. This prevents a flood of batch tasks from blocking new import requests.

---

## Module 4: Multi-Database Storage

### Why 4 Different Databases?

This is the most common question about the platform's architecture. The answer: **no single database excels at everything**. Each database is chosen for what it does best:

### Elasticsearch — The Search Engine

**Role**: Full-text search across millions of entities in milliseconds.

**Why Elasticsearch?**
- Designed from the ground up for text search
- Supports fuzzy matching (finding results despite typos)
- Can search across multiple fields simultaneously
- Returns results ranked by relevance
- Handles millions of documents with consistent sub-second performance

**How It Stores Data:**
- All entities go into a single **index** called `osint_entities`
- Each field has a specific **data type** that determines how it's searched:
  - `text` fields are analyzed (split into tokens for full-text search)
  - `keyword` fields are stored as-is (for exact matching and filtering)
  - Some fields have **both** — `text` for searching and `keyword` for exact matching
  - Emails use a special `uax_url_email` analyzer that treats the entire email as one token (instead of splitting at `@`)
  - IPs use the native `ip` type (supports CIDR range queries)

**Search Strategy:**
The platform doesn't just do a simple text match. It runs **4 strategies simultaneously** and combines the results:

1. **Exact match** (highest priority): Is there a record with this exact value? Perfect for emails, IPs, phone numbers.
2. **Phrase match** (high priority): Does the query appear as a complete phrase within a value?
3. **Prefix match** (medium priority): Does any value start with the query? Useful for partial searches.
4. **Fuzzy match** (lowest priority): Is there a value within 1 edit distance? Catches typos like `gmial.com` → `gmail.com`.

Each strategy has a **boost score**. Exact matches score 100, fuzzy matches score 2. Results are sorted by total score, so exact matches always appear first.

**Deduplication:**
When enabled, search results are grouped by value using Elasticsearch's aggregation pipeline, keeping only the highest-scoring result per unique value.

### MongoDB — The Document Store

**Role**: Flexible storage for entities, raw records, and import job logs.

**Why MongoDB?**
- **Schema flexibility**: Each record can have different fields. One source might have email + IP, another might have username + phone + domain. MongoDB doesn't care.
- **Raw record archival**: The original MySQL rows are stored exactly as-is, preserving the audit trail. You can always go back and see the raw data.
- **Upsert support**: When importing, if an entity already exists, it's updated rather than duplicated.
- **Fallback search**: If Elasticsearch goes down, the API falls back to MongoDB's regex search capabilities.

**Three Collections:**
1. **entities**: Normalized entity documents (one per unique entity)
2. **raw_records**: Original MySQL rows wrapped with metadata (source, table, import timestamp)
3. **import_logs**: Job tracking documents (job ID, status, progress count, error messages)

**Indexes:**
MongoDB creates indexes on frequently queried fields (entity_type, value, source, timestamp) and a compound index on (value + entity_type) for fast deduplication checks.

### Neo4j — The Graph Database

**Role**: Mapping and traversing relationships between entities.

**Why Neo4j?**
- Relational and document databases can store relationships, but they're slow at **traversing** them. Finding "all entities connected to X within 3 hops" requires expensive self-joins in SQL.
- Neo4j is built for this. Traversing relationships is a constant-time operation regardless of dataset size.
- It enables questions like:
  - "What other emails share the same domain?"
  - "Which IPs has this username logged in from?"
  - "What's the shortest connection path between email A and IP B?"

**How It Stores Data:**
- Every entity becomes a **node** labeled `:Entity` with properties (type, value, source, etc.)
- **Relationships** are edges between nodes with a type label:
  - `HAS_DOMAIN`: An email node is connected to its domain (alice@gmail.com → gmail.com)
  - `HAS_EMAIL`: A username node is connected to its email
  - `RESOLVES_TO`: A domain node is connected to an IP it resolves to

**Auto-Relationship Creation:**
When an email entity is created, the system automatically:
1. Extracts the domain part (everything after `@`)
2. Creates a domain node if it doesn't exist
3. Creates a `HAS_DOMAIN` relationship between them

This means importing a database with 100,000 emails automatically builds a rich graph showing which accounts share domains, which domains resolve to the same IPs, etc.

**Path Finding:**
Neo4j's `shortestPath` algorithm finds the most direct connection between any two entities, traversing up to 10 hops. This is useful for answering questions like "How are these two seemingly unrelated entities connected?"

### Redis — The Cache & Broker

**Role**: Two distinct functions.

**As a Celery Message Broker:**
When the API queues an import task, the task message is stored in Redis (database 0). Celery workers constantly poll Redis for new tasks. When a task completes, the result is stored in Redis (database 1). This decouples the API from the workers — they don't need to be aware of each other.

**As a Cache (Future):**
Redis can cache frequently searched queries, health check results, and statistics to reduce database load. With `appendonly` mode enabled, cached data persists even if Redis restarts.

### How the 4 Databases Work Together

When you search for "alice@gmail.com":

1. **Elasticsearch** finds all matching entities in milliseconds, ranked by relevance
2. **MongoDB** provides fallback if ES is down, and stores the raw source records you can drill into
3. **Neo4j** shows that alice@gmail.com connects to gmail.com (domain), which connects to 5 other email addresses, and alice99 (username) links back to the same email
4. **Redis** caches the result so repeated searches are instant

No single database could do all four of these well. Together, they create a complete intelligence picture.

---

## Module 5: Frontend Dashboard

### What Is the Frontend?

The frontend is a **Streamlit** web application — a Python framework that turns scripts into interactive web pages. It runs in the browser at `http://localhost:8501` and provides a visual interface for all platform capabilities.

### Why Streamlit?

- **Python-native**: No JavaScript, HTML, or CSS knowledge needed (though the platform adds custom CSS for theming)
- **Rapid development**: UI components like text inputs, buttons, charts, and tables are single function calls
- **Real-time**: The page updates automatically when data changes
- **Data-friendly**: Built-in support for Plotly charts, Pandas DataFrames, and JSON display

### The 6 Pages

**Page 1: Command Center (🏠)**

The overview dashboard. Displays:
- Four key metrics at the top: total entities, raw records, graph nodes, and relationship count
- A **pie chart** showing entity distribution by type (how many emails vs. IPs vs. domains, etc.)
- A **bar chart** showing entity distribution by source (how many from each imported database)

This page answers: "What does my data landscape look like at a glance?"

**Page 2: Intel Search (🔍)**

The core search interface. Provides:
- A text input for the search query
- Expandable filters for entity type, deduplication, and result limit
- A search button that queries the backend API
- Results displayed as **color-coded cards** — each entity type has its own color for quick visual scanning
- Each card expands to show full details including the raw source record

Entity color coding:
- 🔵 Blue = Email
- 🟣 Purple = Username
- 🟢 Green = Domain
- 🟠 Orange = Phone
- 🔴 Red = IP

This page answers: "What do we know about this email/IP/username/phone/domain?"

**Page 3: Analytics (📊)**

Detailed statistical breakdowns from all databases:
- Elasticsearch: entity counts by type, entities by source
- MongoDB: entity collection count, raw records count
- Neo4j: total nodes, total relationships, nodes by type
- Data tables for each breakdown

This page answers: "How much data do we have and how is it distributed?"

**Page 4: Data Import (📥)**

A two-tab interface for importing data:

- **Tab 1 (New Import)**: A form where you enter the source name, dump filename, optional table list, and optional field mapping (as JSON). Clicking "Start Import" sends the request to the backend.
- **Tab 2 (Job Monitor)**: Lists all past and current import jobs with their status (pending, running, completed, failed), progress count, and error messages if any.

This page answers: "How do I bring in new data and track the import?"

**Page 5: Network Map (🕸️)**

The graph exploration interface:
- Enter an entity ID (format: `type:value`, e.g., `email:alice@gmail.com`)
- Adjust the search depth (1 to 3 hops)
- View all connected entities and the relationships between them
- Visualize the network of connections around a single entity

This page answers: "What is this entity connected to and how?"

**Page 6: System Status (⚙️)**

Operational monitoring:
- A grid showing each of the 5 database services with their status (✅ or ❌) and port numbers
- Live statistics from each database
- Quick action buttons for common operations

This page answers: "Is everything running properly?"

### The Hacker/Cyber Theme

The entire dashboard uses a custom dark theme designed to look like a cybersecurity terminal:

- **Background**: Deep navy (`#0a0e27`)
- **Primary accent**: Neon green (`#00ff41`) — used for metrics, highlights, success states
- **Secondary accent**: Cyan (`#00d9ff`) — used for headers and links
- **Alert accent**: Hot pink/red (`#ff006e`) — used for errors and warnings
- **Fonts**: Monospace fonts (Fira Code and Share Tech Mono) for a terminal feel
- **Effects**: CSS glow animations on metrics, gradient backgrounds on the sidebar, ASCII art header

### API Integration

The frontend never talks to databases directly. It communicates exclusively through the backend API using these helper functions:

- **Health check**: Pings the `/health` endpoint to show service status in the sidebar
- **Statistics**: Calls `/stats` for the Command Center and Analytics pages
- **Search**: Posts to `/search` with the user's query and filters
- **Relationships**: Calls `/entities/{id}/relationships` for the Network Map
- **Import**: Posts to `/import/mysql` to start imports and polls `/import/status/{id}` for progress
- **Import jobs**: Calls `/import/jobs` to list all past imports

Each function has a **try/except** wrapper that returns sensible defaults if the backend is unreachable, preventing the dashboard from crashing when services are down.

---

## Module 6: Operations & Monitoring

### Health Monitoring

The `/health` endpoint is the platform's pulse. It individually pings each of the 5 databases using the lightest possible operation:

- **MySQL**: Executes `SELECT 1` (simplest valid SQL query)
- **MongoDB**: Runs the `ping` admin command
- **Elasticsearch**: Calls the HTTP `ping` endpoint
- **Neo4j**: Executes `RETURN 1` (simplest valid Cypher query)
- **Redis**: Sends the `PING` command

Based on results, the overall status is classified:
- **Healthy**: All 5 services responding
- **Degraded**: Some services down, but platform is partially functional
- **Unhealthy**: All services down

The frontend sidebar continuously polls this endpoint to show real-time service status.

### Logging

The platform uses **Loguru** — a modern Python logging library that provides:

- **Structured output**: Each log line includes timestamp, severity level, module name, function name, and line number
- **Colored console output**: Different colors for INFO, WARNING, ERROR, and CRITICAL messages
- **File rotation**: Log files are automatically rotated at 100MB to prevent disk fill
- **Retention**: Old logs are automatically deleted after 30 days
- **Log level control**: Configurable via the `LOG_LEVEL` setting (default: INFO)

Log files are written to `logs/osint_platform.log` inside the backend container, and also streamed to Docker's log system (accessible via `docker-compose logs`).

### Background Task Management

**Celery Worker** configuration is tuned for import workloads:

- **4 concurrent workers**: Can process 4 imports or batches simultaneously
- **1-hour timeout**: No single task runs longer than 1 hour (prevents stuck jobs)
- **Worker recycling**: Each worker process restarts after 50 tasks to prevent memory leaks from long-running Python processes
- **Prefetch disabled**: Workers fetch one task at a time, preventing one slow import from blocking other tasks

**Queue routing** separates concerns:
- The `imports` queue handles `import_mysql_dump` tasks
- The `processing` queue handles `process_batch` tasks
- This ensures that a burst of batch-processing tasks doesn't prevent new imports from being accepted

### Shell Scripts

The platform includes numerous shell scripts for common operations:

**Lifecycle:**
- `start.sh`: Builds and starts all containers
- `stop.sh`: Stops all containers
- `status.sh`: Shows which containers are running and their ports

**Import:**
- `import_all_complete.sh`: Imports every SQL dump file from the dumps directory
- `import_fresh.sh`: Wipes all data and reimports everything from scratch
- `monitor_import.sh`: Watches import progress in real-time

**Search & Verification:**
- `smart_search.sh`: Searches for an entity from the command line
- `check_entity.sh`: Looks up a specific entity across all databases
- `verify_system.sh`: Comprehensive system health check
- `verify_dumps.sh`: Validates SQL dump files before import

**Troubleshooting:**
- `fix_databases.sh`: Fixes common database connection and permission issues
- `fix_permissions.sh`: Resets file and directory permissions
- `clean_and_reimport.sh`: Nuclear option — destroys all data and starts over
- `pre_cleanup_check.sh`: Preview what would be removed before a cleanup

### Makefile

The `Makefile` provides developer-friendly shortcuts that are easier to remember than full Docker commands:

- `make start` / `make stop` / `make status`: Container lifecycle
- `make logs`: Follow all container logs in real-time
- `make backup`: Creates a timestamped compressed archive of all data
- `make health` / `make stats`: Quick API checks from the terminal
- `make shell-backend` / `make shell-mysql` / `make shell-mongo`: Open interactive shells inside containers
- `make init`: Initialize Elasticsearch indices and Neo4j constraints

### Backup Strategy

Data persistence follows a layered approach:

1. **Docker volumes**: Data directories on the host (`data/mysql/`, `data/mongodb/`, etc.) persist across container restarts
2. **Manual backups**: `make backup` creates a compressed archive of the entire `data/` directory with a timestamp
3. **MySQL dumps**: The original SQL dump files remain in `data/mysql_dumps/` — data can always be reimported from scratch

### Security Notes

The platform is designed for **local/private network use**, not public internet exposure:

- Elasticsearch has security **disabled** (`xpack.security.enabled=false`)
- CORS allows **all origins** (`allow_origins=["*"]`)
- Default passwords are used across all services
- No TLS/HTTPS is configured
- No authentication is required to access the API or dashboard

For any internet-facing deployment, all of these would need to be hardened.

---

## How Everything Connects

### Search Flow

```
User → Dashboard → Backend API → Elasticsearch → Results
                                ↘ (fallback) MongoDB → Results
                                         ↓
                                  User clicks entity
                                         ↓
                          Backend API → Neo4j → Relationship graph
```

1. User types a search query in the Dashboard (Module 5)
2. Dashboard sends an HTTP request to the Backend API (Module 2)
3. API routes the query to Elasticsearch (Module 4) for full-text search
4. If ES is down, API automatically falls back to MongoDB (Module 4)
5. Results return through the API to the Dashboard
6. When the user clicks an entity to explore relationships, the Dashboard calls the API again
7. API queries Neo4j (Module 4) for the entity's graph neighborhood
8. The graph data returns to the Dashboard for visualization

### Import Flow

```
SQL Dump → API Request → Redis Queue → Celery Worker → MySQL Import
                                                      → Normalize
                                                      → MongoDB (store)
                                                      → Elasticsearch (index)
                                                      → Neo4j (graph)
```

1. User places SQL dump in `data/mysql_dumps/` and triggers import via Dashboard or API (Module 5/2)
2. API creates a job record in MongoDB and queues a task in Redis (Module 6)
3. Celery Worker picks up the task and imports the dump into MySQL (Module 3)
4. Worker reads each table in batches, auto-detects fields, normalizes records (Module 3)
5. Normalized entities fan out to MongoDB, Elasticsearch, and Neo4j (Module 4)
6. Job progress is updated in MongoDB throughout (Module 6)
7. Dashboard polls the job status endpoint to show real-time progress (Module 5)

### Health Check Flow

```
Dashboard Sidebar → API /health → Ping MySQL ✓
                                → Ping MongoDB ✓
                                → Ping Elasticsearch ✓
                                → Ping Neo4j ✓
                                → Ping Redis ✓
                                → Return "healthy"
```

The Dashboard sidebar continuously polls the health endpoint (Module 6) to display real-time service indicators — green for up, red for down.

---

## Key Design Decisions Summary

| Decision | Why |
|----------|-----|
| 4 databases instead of 1 | Each excels at a different task (search, storage, graphs, caching) |
| Background processing via Celery | Imports can take hours — don't block the API |
| Auto field detection | Don't require manual config for each new database |
| Regex entity detection | Verify data types regardless of column naming |
| Custom ports | Avoid conflicts with existing services |
| Singleton DatabaseManager | Prevent connection pool exhaustion |
| Pydantic models | Automatic validation, documentation, and serialization |
| Container orchestration | Reproducible, isolated, easy to deploy and destroy |
| Loguru logging | Structured, rotated, retained automatically |
| Fallback search | Platform remains functional even when ES is down |

---

*Generated: February 12, 2026*  
*Purpose: Theory reference — no code, concepts only*
