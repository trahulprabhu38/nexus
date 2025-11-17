# Nexus Monitoring Setup Guide

This guide will help you set up Prometheus and Grafana monitoring for your Nexus microservices platform.

## Architecture

- **Prometheus**: Collects and stores metrics from all services
- **Grafana**: Visualizes metrics with pre-built dashboards
- **Service Discovery**: Automatic discovery of Kubernetes services

## Quick Start

### 1. Deploy Prometheus

```bash
# Apply Prometheus deployment
kubectl apply -f k8s/prometheus-deployment.yaml

# Verify Prometheus is running
kubectl get pods -n monitoring
kubectl get svc -n monitoring

# Access Prometheus UI
# URL: http://<node-ip>:30090
```

### 2. Deploy Grafana

```bash
# Apply Grafana deployment
kubectl apply -f k8s/grafana-deployment.yaml

# Verify Grafana is running
kubectl get pods -n monitoring

# Access Grafana UI
# URL: http://<node-ip>:30300
# Default credentials: admin / admin123
```

### 3. Add Prometheus Annotations to Services

To enable Prometheus scraping, add these annotations to your service pods:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"  # Your service port
    prometheus.io/path: "/metrics"  # Metrics endpoint
```

## Instrumenting Your Services

### Python FastAPI Services

Add Prometheus metrics to your FastAPI applications:

#### 1. Install Dependencies

```bash
pip install prometheus-client prometheus-fastapi-instrumentator
```

#### 2. Update your FastAPI app

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Instrument your FastAPI app
Instrumentator().instrument(app).expose(app)

# Your existing routes...
@app.get("/")
async def root():
    return {"message": "Hello World"}
```

This automatically exposes metrics at `/metrics` endpoint.

### Custom Metrics Example

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define custom metrics
request_count = Counter('app_requests_total', 'Total app requests', ['method', 'endpoint'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration')
active_requests = Gauge('app_active_requests', 'Number of active requests')

# Use in your code
@app.get("/api/query")
async def query_endpoint():
    request_count.labels(method='GET', endpoint='/api/query').inc()
    active_requests.inc()

    start_time = time.time()
    try:
        # Your logic here
        result = {"status": "success"}
        return result
    finally:
        duration = time.time() - start_time
        request_duration.observe(duration)
        active_requests.dec()
```

## Updating Existing Services

### SQL Query Generator (SQL_QUERY_GENERATOR/app.py)

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add this after creating FastAPI app
Instrumentator().instrument(app).expose(app)

# Your existing code continues...
```

### Intent Agent (Intent-Agent/backend.py)

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add instrumentation
Instrumentator().instrument(app).expose(app)

# Your existing routes...
```

### SQL Validator Agent (sql_validator_agent/app.py)

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add instrumentation
Instrumentator().instrument(app).expose(app)

# Your existing validation endpoints...
```

### Column Pruning (Streamlit)

For Streamlit apps, add a separate metrics endpoint:

```python
from prometheus_client import make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
import streamlit as st

# Your Streamlit app code...

# Add metrics endpoint on a different port
def setup_metrics_server():
    from flask import Flask
    app = Flask(__name__)
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
    })
    run_simple('0.0.0.0', 8501, app, use_reloader=False, use_debugger=False)
```

## Update Deployment Manifests

Add Prometheus annotations to your deployment manifests:

### Example: sql-query-gen-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sql-query-gen-deployment
spec:
  template:
    metadata:
      labels:
        app: sql-query-gen
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: sql-query-gen
        image: trahulprabhu38/sql-query-gen:latest
        # ... rest of your config
```

Repeat for all services (intent-agent, sql-validator, column-prune, frontend).

## Accessing the Dashboards

### Prometheus

- **URL**: `http://<node-ip>:30090`
- **Features**:
  - Query metrics using PromQL
  - View targets and service discovery
  - Check alerts
  - View configuration

### Grafana

- **URL**: `http://<node-ip>:30300`
- **Default Login**:
  - Username: `admin`
  - Password: `admin123` (CHANGE THIS!)

#### Pre-configured Dashboard

The "Nexus Services Overview" dashboard is automatically provisioned with:
- Service availability status
- CPU usage by service
- Memory usage by service
- Request rate
- Error rate
- Pod restart count

#### Creating Custom Dashboards

1. Login to Grafana
2. Click "+" → "Dashboard"
3. Add Panel
4. Select "Prometheus" as data source
5. Enter PromQL query (examples below)

#### Useful PromQL Queries

```promql
# Service uptime
up{job="nexus-services"}

# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# CPU usage
rate(container_cpu_usage_seconds_total{namespace="default"}[5m])

# Memory usage
container_memory_working_set_bytes{namespace="default"}

# Pod restart count
kube_pod_container_status_restarts_total{namespace="default"}
```

## Alerting (Optional)

To enable alerting, you need to deploy Alertmanager:

```yaml
# alertmanager-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: nexus
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m

    route:
      group_by: ['alertname', 'cluster']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'email'

    receivers:
    - name: 'email'
      email_configs:
      - to: 'your-email@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

## Testing Metrics

### 1. Check if metrics are exposed

```bash
# For SQL Query Generator
kubectl port-forward -n default svc/sql-query-gen-service 8000:8000
curl http://localhost:8000/metrics

# For Intent Agent
kubectl port-forward -n default svc/intent-agent-service 8080:8080
curl http://localhost:8080/metrics
```

### 2. Verify Prometheus is scraping

1. Access Prometheus UI: `http://<node-ip>:30090`
2. Go to Status → Targets
3. Verify all services show as "UP"

### 3. Query metrics in Prometheus

1. Go to Graph tab
2. Enter query: `up{job="nexus-services"}`
3. Execute and verify results

## Troubleshooting

### Services not showing in Prometheus targets

1. Check if pods have correct annotations:
```bash
kubectl get pods -n default -o yaml | grep -A 3 prometheus.io
```

2. Check Prometheus logs:
```bash
kubectl logs -n monitoring deployment/prometheus
```

3. Verify service discovery:
```bash
kubectl get endpoints -n default
```

### Grafana can't connect to Prometheus

1. Check if Prometheus service is running:
```bash
kubectl get svc -n monitoring prometheus
```

2. Test connectivity from Grafana pod:
```bash
kubectl exec -it -n monitoring deployment/grafana -- wget -O- http://prometheus:9090/api/v1/query?query=up
```

### No metrics showing up

1. Ensure your services are exposing `/metrics` endpoint
2. Check if `prometheus-client` is installed in your services
3. Verify port numbers in annotations match your service ports

## Production Recommendations

1. **Change default passwords**:
   - Update Grafana admin password
   - Use Kubernetes secrets for sensitive data

2. **Enable persistence**:
   - Already configured via PVCs
   - Ensure your cluster has StorageClass configured

3. **Resource limits**:
   - Adjust CPU/memory limits based on your workload
   - Monitor Prometheus disk usage

4. **High availability**:
   - Run multiple Prometheus replicas
   - Use Thanos for long-term storage

5. **Security**:
   - Enable TLS for Prometheus and Grafana
   - Use authentication for Prometheus
   - Implement network policies

6. **Backup**:
   - Backup Grafana dashboards
   - Backup Prometheus data or use remote storage

## Monitoring Best Practices

1. **Use labels effectively**: Label your metrics with service name, environment, version
2. **Keep cardinality low**: Don't use high-cardinality values (like user IDs) as labels
3. **Set appropriate scrape intervals**: 15-30s is usually sufficient
4. **Define SLOs**: Set up Service Level Objectives for critical services
5. **Create runbooks**: Document what to do when alerts fire

## Next Steps

1. Add custom business metrics to your services
2. Create service-specific Grafana dashboards
3. Set up alerting rules
4. Configure Alertmanager for notifications
5. Implement distributed tracing (Jaeger/Tempo)
6. Add log aggregation (Loki/ELK)

## Support

For issues or questions:
- Check Prometheus documentation: https://prometheus.io/docs/
- Check Grafana documentation: https://grafana.com/docs/
- Review Kubernetes service discovery: https://prometheus.io/docs/prometheus/latest/configuration/configuration/#kubernetes_sd_config
