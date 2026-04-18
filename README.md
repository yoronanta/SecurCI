# SecurCI 

SecurCI is a lightweight security scanning instrument. I created it as a training project, trying to use as many technologies as possible while learning AppSec basics. The project description bellow was AI-generated since I made it a while ago and I don't recall all the details. 

## Architecture

- **API (`api/ciapi.py`)**: FastAPI application that accepts scan requests, generates a task ID, and enqueues the request in Redis.
- **Analyzer (`analyzer/analyzer.py`)**: Worker that listens to the Redis queue, clones the repository, runs Bandit and Safety scans, and stores the results back in Redis.
- **Redis**: Used as a message broker between the API and the analyzer.
- **Docker Compose**: Orchestrates the services (Redis, API, Analyzer) for easy deployment.

## Components

### API Endpoints

- `POST /scan`: Accepts a JSON payload with `repo_url` and optional `branch` (defaults to "main"). Returns a task ID and status.
- `GET /scan/{task_id}`: Returns the full task data including scan results.
- `GET /status/{task_id}`: Returns only the status of a task.

### Analyzer Worker

The worker continuously listens to the `scan_queue` in Redis. For each task:
1. Clones the repository (shallow clone, depth=1).
2. Runs Bandit for static application security testing (SAST).
3. Runs Safety for dependency vulnerability scanning.
4. Aggregates results and stores them in Redis under `task:{task_id}`.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Running with Docker Compose

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd securCI
   ```

2. Build and start the services:
   ```bash
   docker-compose up --build
   ```

3. The API will be available at `http://localhost:8000`.

### Using the API

Submit a scan request:
```bash
curl -X POST "http://localhost:8000/scan" \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/example/repo.git"}'
```

Check the status of a task (replace `<task_id>` with the ID from the response):
```bash
curl "http://localhost:8000/scan/<task_id>"
```

## Configuration

- The API and analyzer connect to Redis at host `redis` (the service name in docker-compose) and port 6379.
- You can change the Redis host and port via environment variables:
  - `REDIS_HOST`
  - `REDIS_PORT`

## Security Tools Used

- [Bandit](https://bandit.readthedocs.io/): Python security linter that finds common security issues in Python code.
- [Safety](https://pyup.io/safety/): Checks Python dependencies for known security vulnerabilities.

