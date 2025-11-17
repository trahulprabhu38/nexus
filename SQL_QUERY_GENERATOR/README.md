# SQL Query Generator API

A FastAPI-based microservice that converts natural language queries into SQL using AI agents powered by CrewAI and Ollama.

## Features

- RESTful API for SQL generation from natural language
- AI-powered query generation using CrewAI framework
- Docker containerization
- Kubernetes-ready deployment
- Health check endpoints
- Structured logging
- Production-ready configurations

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│  FastAPI     │─────▶│   CrewAI    │
│             │◀─────│  Endpoint    │◀─────│   Agent     │
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │   Ollama    │
                                            │   LLM       │
                                            └─────────────┘
```

## API Endpoints

### GET /
Health check endpoint returning service status.

**Response:**
```json
{
  "status": "healthy",
  "service": "SQL Query Generator",
  "version": "1.0.0"
}
```

### GET /health
Kubernetes health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

### POST /generate-sql
Generate SQL query from natural language input.

**Request:**
```json
{
  "query": "Get all students who scored more than 90 in Math"
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM student s JOIN marks m ON s.id = m.student_id WHERE m.subject = 'Math' AND m.marks > 90",
  "input_query": "Get all students who scored more than 90 in Math"
}
```

## Local Development

### Prerequisites

- Python 3.10+
- Ollama running locally
- Virtual environment (recommended)

### Setup

1. Clone the repository and navigate to the directory:
```bash
cd SQL_QUERY_GENERATOR
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Ensure Ollama is running:
```bash
ollama serve
ollama pull llama3
```

5. Run the application:
```bash
python app.py
# Or with uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

6. Access the API:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker Deployment

### Build Image

```bash
docker build -t sql-query-generator:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e OLLAMA_HOST=host.docker.internal \
  sql-query-generator:latest
```

### Using Docker Compose (Optional)

Create a `docker-compose.yml`:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

Run with:
```bash
docker-compose up -d
```

## Kubernetes Deployment

See [k8s/README.md](k8s/README.md) for detailed Kubernetes deployment instructions.

### Quick Deploy

```bash
# Build and tag image
docker build -t <your-registry>/sql-query-generator:latest .
docker push <your-registry>/sql-query-generator:latest

# Deploy to Kubernetes
kubectl apply -f k8s/

# Access the service
kubectl port-forward svc/sql-query-generator 8000:80
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama service endpoint | `http://localhost:11434` |
| `LLM_MODEL` | LLM model to use | `ollama/llama3` |
| `LLM_TEMPERATURE` | Temperature for LLM | `0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |

### Database Schema

The application uses a schema defined in `schema.json`:
```json
{
  "student": ["id", "name", "year"],
  "marks": ["student_id", "subject", "marks"]
}
```

## Project Structure

```
SQL_QUERY_GENERATOR/
├── app.py                 # FastAPI application
├── sql_agent.py          # CrewAI agent configuration
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── .dockerignore        # Docker ignore rules
├── schema.json          # Database schema
├── k8s/                 # Kubernetes manifests
│   ├── configmap.yaml   # Configuration
│   ├── secrets.yaml     # Secrets
│   ├── deployment.yaml  # Deployment spec
│   ├── service.yaml     # Service definitions
│   └── README.md        # K8s deployment guide
└── utils/               # Utility modules
    ├── prompt_template.py
    ├── table_mapping.py
    ├── llm_client.py
    └── guardrails.py
```

## Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Generate SQL
curl -X POST http://localhost:8000/generate-sql \
  -H "Content-Type: application/json" \
  -d '{"query": "Get all students who scored more than 90 in Math"}'
```

### Using Swagger UI

Navigate to http://localhost:8000/docs for interactive API documentation and testing.

## Production Considerations

1. **Security**
   - Use proper secret management (e.g., Kubernetes Secrets, HashiCorp Vault)
   - Enable HTTPS/TLS
   - Implement API authentication (API keys, JWT)
   - Add rate limiting

2. **Monitoring**
   - Add Prometheus metrics
   - Implement distributed tracing
   - Set up centralized logging (ELK, Loki)
   - Configure alerts

3. **Performance**
   - Implement caching for common queries
   - Add request timeout handling
   - Configure connection pooling
   - Optimize resource limits

4. **Scalability**
   - Use Horizontal Pod Autoscaler in Kubernetes
   - Implement load balancing
   - Add Redis for caching
   - Consider async processing for long queries

## Troubleshooting

### Ollama Connection Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Set OLLAMA_HOST environment variable
export OLLAMA_HOST=http://your-ollama-host:11434
```

### Docker Network Issues

```bash
# Use host network mode on Linux
docker run --network host sql-query-generator:latest

# Or use host.docker.internal on Mac/Windows
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review logs: `kubectl logs -l app=sql-query-generator`
