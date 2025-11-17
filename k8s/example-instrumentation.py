"""
Example: How to add Prometheus metrics to your FastAPI service

This example shows how to instrument any of the Nexus FastAPI services
(SQL Query Generator, Intent Agent, SQL Validator) with Prometheus metrics.

Usage:
1. Add prometheus-client and prometheus-fastapi-instrumentator to requirements.txt
2. Add the instrumentation code from this file to your app.py or backend.py
3. Redeploy your service
"""

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
import time

# Create FastAPI app
app = FastAPI(title="Nexus Service Example")

# ============================================================================
# OPTION 1: Quick Setup - Automatic instrumentation (Recommended for most cases)
# ============================================================================

# This single line adds comprehensive metrics automatically
Instrumentator().instrument(app).expose(app)

# That's it! Your /metrics endpoint is now available with:
# - HTTP request duration
# - HTTP request count by method, path, status
# - Concurrent requests
# And more...


# ============================================================================
# OPTION 2: Custom Metrics (For advanced use cases)
# ============================================================================

# Define custom metrics for business-specific monitoring

# Counter: Counts events (only goes up)
sql_queries_total = Counter(
    'nexus_sql_queries_total',
    'Total number of SQL queries processed',
    ['query_type', 'status']  # Labels for grouping
)

intent_classifications_total = Counter(
    'nexus_intent_classifications_total',
    'Total number of intent classifications',
    ['intent_type', 'confidence_level']
)

validation_requests_total = Counter(
    'nexus_validation_requests_total',
    'Total validation requests',
    ['validation_result']
)

# Histogram: Tracks distribution of values (e.g., latency, sizes)
query_processing_duration = Histogram(
    'nexus_query_processing_duration_seconds',
    'Time spent processing SQL queries',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]  # Define your own buckets
)

model_inference_duration = Histogram(
    'nexus_model_inference_duration_seconds',
    'Time spent on model inference',
    buckets=[0.05, 0.1, 0.5, 1.0, 2.0]
)

# Gauge: Can go up and down (e.g., queue size, active connections)
active_connections = Gauge(
    'nexus_active_connections',
    'Number of active database connections'
)

pending_queries = Gauge(
    'nexus_pending_queries',
    'Number of queries waiting to be processed'
)

model_loaded = Gauge(
    'nexus_model_loaded',
    'Whether the ML model is loaded (1=loaded, 0=not loaded)'
)


# ============================================================================
# Example endpoints using custom metrics
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "nexus-example"}


@app.post("/api/query")
async def process_query(request: Request):
    """
    Example: SQL Query Generator endpoint with metrics
    """
    # Track active queries
    pending_queries.inc()
    active_connections.inc()

    # Measure processing time
    start_time = time.time()

    try:
        # Simulate query processing
        query_type = "SELECT"  # Get this from your logic
        result = {"query": "SELECT * FROM users", "status": "success"}

        # Record successful query
        sql_queries_total.labels(
            query_type=query_type,
            status="success"
        ).inc()

        return result

    except Exception as e:
        # Record failed query
        sql_queries_total.labels(
            query_type="unknown",
            status="error"
        ).inc()
        raise

    finally:
        # Record processing duration
        duration = time.time() - start_time
        query_processing_duration.observe(duration)

        # Decrease active counters
        pending_queries.dec()
        active_connections.dec()


@app.post("/api/classify")
async def classify_intent(request: Request):
    """
    Example: Intent Agent endpoint with metrics
    """
    start_time = time.time()

    try:
        # Simulate intent classification
        intent = "query"  # Get from your model
        confidence = 0.95  # Get from your model

        # Determine confidence level bucket
        if confidence > 0.9:
            confidence_level = "high"
        elif confidence > 0.7:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Record classification
        intent_classifications_total.labels(
            intent_type=intent,
            confidence_level=confidence_level
        ).inc()

        result = {"intent": intent, "confidence": confidence}
        return result

    finally:
        duration = time.time() - start_time
        model_inference_duration.observe(duration)


@app.post("/api/validate")
async def validate_sql(request: Request):
    """
    Example: SQL Validator endpoint with metrics
    """
    try:
        # Simulate validation
        is_valid = True  # Get from your validation logic

        result_label = "valid" if is_valid else "invalid"

        # Record validation
        validation_requests_total.labels(
            validation_result=result_label
        ).inc()

        return {"valid": is_valid}

    except Exception as e:
        validation_requests_total.labels(
            validation_result="error"
        ).inc()
        raise


# ============================================================================
# Application lifecycle hooks
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Initialize metrics on startup
    """
    print("Starting up service...")

    # Set initial gauge values
    pending_queries.set(0)
    active_connections.set(0)
    model_loaded.set(1)  # Indicate model is loaded

    print("Prometheus metrics initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown
    """
    print("Shutting down service...")
    model_loaded.set(0)


# ============================================================================
# Manual metrics endpoint (if not using Instrumentator)
# ============================================================================

# If you're not using Instrumentator and want to manually expose metrics:
from fastapi.responses import Response

@app.get("/metrics-manual")
async def metrics_manual():
    """
    Manual metrics endpoint
    Only use this if you're NOT using Instrumentator
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain; charset=utf-8"
    )


# ============================================================================
# Middleware for automatic request tracking (if not using Instrumentator)
# ============================================================================

from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Custom middleware to track requests
    Only use this if you need custom logic beyond Instrumentator
    """

    async def dispatch(self, request: Request, call_next):
        # Track request start
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # You can add custom logic here to track specific metrics
        # based on request path, method, status code, etc.

        return response


# Uncomment to use custom middleware
# app.add_middleware(MetricsMiddleware)


# ============================================================================
# Usage Instructions
# ============================================================================

"""
To use this in your services:

1. SQL Query Generator (SQL_QUERY_GENERATOR/app.py):
   - Add: from prometheus_fastapi_instrumentator import Instrumentator
   - Add: Instrumentator().instrument(app).expose(app)
   - Add custom metrics for query processing

2. Intent Agent (Intent-Agent/backend.py):
   - Add: from prometheus_fastapi_instrumentator import Instrumentator
   - Add: Instrumentator().instrument(app).expose(app)
   - Add custom metrics for model inference

3. SQL Validator Agent (sql_validator_agent/app.py):
   - Add: from prometheus_fastapi_instrumentator import Instrumentator
   - Add: Instrumentator().instrument(app).expose(app)
   - Add custom metrics for validation results

4. Update requirements.txt in each service:
   prometheus-client==0.19.0
   prometheus-fastapi-instrumentator==6.1.0

5. Rebuild Docker images:
   docker build -t your-service:latest .

6. Update Kubernetes deployments with annotations:
   annotations:
     prometheus.io/scrape: "true"
     prometheus.io/port: "8000"  # Your service port
     prometheus.io/path: "/metrics"

7. Verify metrics are exposed:
   curl http://localhost:8000/metrics
"""
