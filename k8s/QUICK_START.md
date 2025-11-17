# Nexus Platform - Quick Start Guide

Complete guide to build, deploy, and monitor the Nexus microservices platform.

## Overview

The Nexus platform consists of:
- **5 Microservices**: SQL Query Generator, Intent Agent, SQL Validator, Column Pruning, Frontend
- **CI/CD**: Jenkins pipeline for automated builds
- **Monitoring**: Prometheus + Grafana stack
- **Orchestration**: Kubernetes deployments

## Prerequisites

- Docker installed
- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured
- Jenkins server (optional, for CI/CD)
- Git

## Quick Start (5 Minutes)

### 1. Deploy Services to Kubernetes

```bash
# Navigate to k8s directory
cd k8s

# Deploy PostgreSQL database
kubectl apply -f deployment.yml

# Deploy all microservices
kubectl apply -f sql-query-gen-deployment.yaml
kubectl apply -f intent-agent-deployment.yaml
kubectl apply -f column-prune-deploy.yml
kubectl apply -f frontend-deploy.yml

# Check status
kubectl get pods
kubectl get svc
```

### 2. Deploy Monitoring Stack

```bash
# Make deployment script executable
chmod +x monitoring/deploy-monitoring.sh

# Deploy Prometheus and Grafana
cd monitoring
./deploy-monitoring.sh

# Or manually:
kubectl apply -f ../k8s/prometheus-deployment.yaml
kubectl apply -f ../k8s/grafana-deployment.yaml
```

### 3. Access the Services

```bash
# Get node IP
kubectl get nodes -o wide

# Access services (using NodePort)
# SQL Query Generator: http://<node-ip>:30001
# Intent Agent: http://<node-ip>:30002
# Frontend: http://<node-ip>:30003
# Prometheus: http://<node-ip>:30090
# Grafana: http://<node-ip>:30300 (admin/admin123)
```

## Complete Setup Guide

### Part 1: Jenkins CI/CD Setup

#### 1.1 Install Jenkins

```bash
# Using Docker
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts

# Get initial password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

#### 1.2 Configure Jenkins

1. Access Jenkins at `http://localhost:8080`
2. Install suggested plugins
3. Install additional plugins:
   - Docker Pipeline
   - Kubernetes CLI
   - Blue Ocean (optional)

#### 1.3 Add Credentials

1. **Docker Hub**:
   - Manage Jenkins → Credentials
   - Add Username/Password
   - ID: `dockerhub-credentials`
   - Username: `trahulprabhu38`
   - Password: Your Docker Hub token

2. **Kubernetes** (if needed):
   - Add Secret file
   - ID: `kubeconfig`
   - File: Your ~/.kube/config

#### 1.4 Create Pipeline

1. New Item → Pipeline
2. Name: `Nexus-Build-Pipeline`
3. Configure:
   - Pipeline script from SCM
   - SCM: Git
   - Repository URL: Your repo URL
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`

#### 1.5 Run Build

1. Build with Parameters
2. Select services to build
3. Choose tag version
4. Click Build

### Part 2: Manual Docker Builds

If not using Jenkins, build manually:

```bash
# Build all services
cd SQL_QUERY_GENERATOR
docker build -t trahulprabhu38/sql-query-gen:latest .
docker push trahulprabhu38/sql-query-gen:latest

cd ../Intent-Agent
docker build -t trahulprabhu38/intent-agent:latest .
docker push trahulprabhu38/intent-agent:latest

cd ../sql_validator_agent
docker build -t trahulprabhu38/sql-validator:latest .
docker push trahulprabhu38/sql-validator:latest

cd ../column\ pruning
docker build -t trahulprabhu38/column-prune:latest .
docker push trahulprabhu38/column-prune:latest

cd ../frontend
docker build -t trahulprabhu38/nexus-frontend:latest .
docker push trahulprabhu38/nexus-frontend:latest
```

### Part 3: Monitoring Setup

#### 3.1 Deploy Prometheus

```bash
kubectl apply -f k8s/prometheus-deployment.yaml

# Wait for ready
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open http://localhost:9090
```

#### 3.2 Deploy Grafana

```bash
kubectl apply -f k8s/grafana-deployment.yaml

# Wait for ready
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n monitoring

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Open http://localhost:3000 (admin/admin123)
```

#### 3.3 Add Metrics to Services

1. **Update requirements.txt** in each service:
```txt
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
```

2. **Add instrumentation** to your FastAPI apps:
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

3. **Add annotations** to deployments:
```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
```

4. **Rebuild and deploy**:
```bash
# Rebuild images with Jenkins or manually
# Then update deployments:
kubectl rollout restart deployment/sql-query-gen-deployment
kubectl rollout restart deployment/intent-agent-deployment
kubectl rollout restart deployment/sql-validator-api-deployment
kubectl rollout restart deployment/column-prune-deployment
kubectl rollout restart deployment/frontend-deployment
```

### Part 4: Verify Everything

#### 4.1 Check Services

```bash
# Check all pods
kubectl get pods --all-namespaces

# Check services
kubectl get svc --all-namespaces

# Check endpoints
kubectl get endpoints
```

#### 4.2 Test Services

```bash
# SQL Query Generator
curl http://<node-ip>:30001/health
curl http://<node-ip>:30001/metrics

# Intent Agent
curl http://<node-ip>:30002/health
curl http://<node-ip>:30002/metrics

# SQL Validator
curl http://<node-ip>:30000/health
curl http://<node-ip>:30000/metrics
```

#### 4.3 Check Prometheus Targets

1. Open Prometheus UI: `http://<node-ip>:30090`
2. Go to Status → Targets
3. Verify all services show as "UP"

#### 4.4 View Grafana Dashboards

1. Open Grafana: `http://<node-ip>:30300`
2. Login: admin / admin123
3. Go to Dashboards
4. Open "Nexus Services Overview"
5. You should see metrics for all services

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SQL Query    │  │ Intent Agent │  │ SQL Validator│      │
│  │ Generator    │  │              │  │              │      │
│  │ (Port 8000)  │  │ (Port 8080)  │  │ (Port 8000)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                  ↓                  ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Column       │  │   Frontend   │  │  PostgreSQL  │      │
│  │ Pruning      │  │              │  │   Database   │      │
│  │ (Port 8501)  │  │ (Port 80)    │  │ (Port 5432)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                  ↓                  ↓              │
│  ═══════════════════════════════════════════════════════    │
│                     Prometheus Scrapes                       │
│  ═══════════════════════════════════════════════════════    │
│         ↓                                                     │
│  ┌────────────────────────┐      ┌────────────────────┐     │
│  │      Prometheus        │ ───→ │      Grafana       │     │
│  │    (Port 9090)         │      │    (Port 3000)     │     │
│  └────────────────────────┘      └────────────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │
                    Jenkins CI/CD
              (Builds & Deploys Images)
```

## CI/CD Flow

```
Developer Push → Git Repository
                      ↓
              Webhook Trigger
                      ↓
                 Jenkins Pipeline
                      ↓
        ┌─────────────┴─────────────┐
        ↓                           ↓
   Build Docker Images        Run Tests
        ↓                           ↓
   Push to Registry          Security Scan
        ↓                           ↓
        └─────────────┬─────────────┘
                      ↓
            Deploy to Kubernetes
                      ↓
            Verify Deployment
                      ↓
         Prometheus/Grafana Monitor
```

## Common Commands

### Jenkins
```bash
# View Jenkins logs
docker logs -f jenkins

# Restart Jenkins
docker restart jenkins

# Backup Jenkins
docker exec jenkins tar czf /var/jenkins_home/backup.tar.gz /var/jenkins_home
```

### Kubernetes
```bash
# View logs
kubectl logs -f deployment/sql-query-gen-deployment

# Scale deployment
kubectl scale deployment/sql-query-gen-deployment --replicas=3

# Update image
kubectl set image deployment/sql-query-gen-deployment \
  sql-query-gen=trahulprabhu38/sql-query-gen:v2

# Rollback
kubectl rollout undo deployment/sql-query-gen-deployment

# Delete all
kubectl delete -f k8s/
```

### Monitoring
```bash
# Port forward Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Port forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Check Prometheus config
kubectl get configmap -n monitoring prometheus-config -o yaml

# Restart Prometheus
kubectl rollout restart deployment/prometheus -n monitoring
```

### Docker
```bash
# List images
docker images | grep trahulprabhu38

# Remove old images
docker image prune -a

# View image layers
docker history trahulprabhu38/sql-query-gen:latest

# Inspect image
docker inspect trahulprabhu38/sql-query-gen:latest
```

## Troubleshooting

### Services not starting
```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### Metrics not showing
```bash
# Check if /metrics endpoint exists
kubectl port-forward <pod-name> 8000:8000
curl http://localhost:8000/metrics

# Check Prometheus targets
# Prometheus UI → Status → Targets
```

### Jenkins build fails
```bash
# Check Jenkins logs
docker logs jenkins

# Verify Docker access
docker exec jenkins docker ps

# Verify kubectl access
docker exec jenkins kubectl get nodes
```

## Security Best Practices

1. **Change default passwords**:
   - Grafana: admin/admin123
   - Update in production!

2. **Use secrets**:
   ```bash
   kubectl create secret generic db-password --from-literal=password=yourpassword
   ```

3. **Enable RBAC**:
   - Already configured in prometheus-deployment.yaml

4. **Use network policies**:
   ```bash
   kubectl apply -f network-policies.yaml
   ```

5. **Scan images**:
   ```bash
   trivy image trahulprabhu38/sql-query-gen:latest
   ```

## Performance Tuning

### Kubernetes
- Adjust resource limits in deployments
- Use HorizontalPodAutoscaler
- Configure PodDisruptionBudgets

### Prometheus
- Adjust scrape intervals
- Configure retention period
- Use recording rules

### Jenkins
- Use distributed builds
- Enable Docker layer caching
- Use pipeline caching

## Next Steps

1. ✅ Setup Jenkins CI/CD
2. ✅ Deploy to Kubernetes
3. ✅ Setup monitoring
4. ☐ Configure alerting
5. ☐ Setup log aggregation (ELK/Loki)
6. ☐ Implement distributed tracing (Jaeger)
7. ☐ Add API gateway (Kong/Istio)
8. ☐ Setup service mesh
9. ☐ Configure auto-scaling
10. ☐ Implement blue-green deployments

## Resources

- **Jenkins Setup**: See `JENKINS_SETUP.md`
- **Monitoring Guide**: See `monitoring/README.md`
- **Jenkinsfile**: See `Jenkinsfile`
- **Kubernetes Manifests**: See `k8s/` directory

## Support

For issues:
1. Check logs: `kubectl logs <pod-name>`
2. Check events: `kubectl get events`
3. Check service status: `kubectl get svc`
4. Review documentation in this repository

Happy deploying! 🚀
