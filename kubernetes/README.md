# Nexus Kubernetes Deployment

This directory contains all Kubernetes manifests for deploying the Nexus platform.

## ✅ What Was Fixed

### 1. Namespace Issues ✓
- **Problem**: Resources were split between `default`, `nexus`, and some had no namespace
- **Solution**:
  - Created `00-namespace.yaml` to explicitly create the `nexus` namespace
  - All backend services in `default` namespace (sql-query-gen, sql-validator, postgres)
  - All monitoring in `nexus` namespace (prometheus, grafana)
  - All frontend/UI services in `nexus` namespace (frontend, column-prune, intent-agent)

### 2. PersistentVolume Issues ✓
- **Problem**: SQL Validator PV used `hostPath: /mnt/data` which doesn't work on all clusters
- **Solution**:
  - Removed manual PV definition
  - Using dynamic provisioning with default StorageClass
  - Works on minikube, GKE, EKS, AKS out of the box

### 3. ConfigMap/Secret References ✓
- **Problem**: SQL Query Generator referenced ConfigMaps/Secrets without namespaces
- **Solution**:
  - Added `namespace: default` to all ConfigMaps and Secrets
  - Verified all references match deployment expectations

### 4. Service Port Mismatches ✓
- **Problem**: Frontend service had `targetPort: 3000` but container runs on port 80
- **Solution**: Fixed targetPort to match actual container ports

## 📁 Directory Structure

```
kubernetes/
├── 00-namespace.yaml                 # Namespace definitions (APPLY FIRST)
├── secrets.yml                       # SQL Validator secrets
├── configmap.yml                     # SQL Validator configmap
├── sql-query-gen-secrets.yaml        # SQL Query Generator secrets
├── sql-query-gen-configmap.yaml      # SQL Query Generator configmap
├── deployment.yml                    # PostgreSQL + SQL Validator deployments + PVC
├── svc.yml                           # PostgreSQL + SQL Validator services
├── sql-query-gen-deployment.yaml     # SQL Query Generator deployment
├── sql-query-gen-service.yaml        # SQL Query Generator services (ClusterIP + NodePort)
├── intent-agent-deployment.yaml      # Intent Agent deployment
├── intent-agent-service.yaml         # Intent Agent service
├── column-prune-deploy.yml           # Column Pruning deployment
├── column-prune-svc.yml              # Column Pruning service
├── frontend-deploy.yml               # Frontend deployment
├── frontend-svc.yml                  # Frontend service
├── prometheus-deployment.yaml        # Prometheus with ConfigMaps, RBAC, PVC
├── grafana-deployment.yaml           # Grafana with ConfigMaps, dashboards, PVC
├── service-monitors.yaml             # ServiceMonitors for Prometheus Operator (optional)
├── deploy-all.sh                     # ⭐ Automated deployment script
├── delete-all.sh                     # Automated deletion script
├── deploy-monitoring.sh              # Deploy only monitoring stack
└── README.md                         # This file
```

## 🏗️ Resource Organization

### Default Namespace
Services that interact with the database or backend processing:
- ✅ PostgreSQL Database (with PVC)
- ✅ SQL Validator API
- ✅ SQL Query Generator

### Nexus Namespace
User-facing services and monitoring:
- ✅ Frontend
- ✅ Column Pruning
- ✅ Intent Agent
- ✅ Prometheus (with PVC)
- ✅ Grafana (with PVC)

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
cd kubernetes

# Deploy everything
./deploy-all.sh

# Or deploy only monitoring
./deploy-monitoring.sh
```

### Option 2: Manual Deployment

```bash
cd kubernetes

# 1. Create namespaces
kubectl apply -f 00-namespace.yaml

# 2. Create secrets and configmaps
kubectl apply -f secrets.yml
kubectl apply -f configmap.yml
kubectl apply -f sql-query-gen-secrets.yaml
kubectl apply -f sql-query-gen-configmap.yaml

# 3. Deploy database and SQL validator
kubectl apply -f deployment.yml
kubectl apply -f svc.yml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres-deployment -n default

# 4. Deploy SQL Query Generator
kubectl apply -f sql-query-gen-deployment.yaml
kubectl apply -f sql-query-gen-service.yaml

# 5. Deploy Intent Agent
kubectl apply -f intent-agent-deployment.yaml
kubectl apply -f intent-agent-service.yaml

# 6. Deploy Column Pruning
kubectl apply -f column-prune-deploy.yml
kubectl apply -f column-prune-svc.yml

# 7. Deploy Frontend
kubectl apply -f frontend-deploy.yml
kubectl apply -f frontend-svc.yml

# 8. Deploy Monitoring
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f grafana-deployment.yaml
```

## ✅ Verifying Deployment

```bash
# Check all pods
kubectl get pods --all-namespaces

# Check deployments
kubectl get deployments -n default
kubectl get deployments -n nexus

# Check services
kubectl get svc -n default
kubectl get svc -n nexus

# Check PVCs
kubectl get pvc --all-namespaces

# Check pod logs
kubectl logs -f deployment/sql-query-generator -n default
kubectl logs -f deployment/prometheus -n nexus
```

## 🌐 Accessing Services

### Method 1: NodePort (Default)

Get node IP and service ports:

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
[ -z "$NODE_IP" ] && NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get service ports
kubectl get svc --all-namespaces | grep NodePort
```

### Method 2: Port Forwarding (For Development)

```bash
# SQL Query Generator
kubectl port-forward -n default svc/sql-query-generator 8000:80

# SQL Validator
kubectl port-forward -n default svc/sql-validator-api-service 8001:8000

# Intent Agent
kubectl port-forward -n nexus svc/intent-agent 8080:80

# Column Pruning
kubectl port-forward -n nexus svc/nexus-column-prune-service 8501:8501

# Frontend
kubectl port-forward -n nexus svc/nexus-frontend-service 3000:80

# Prometheus
kubectl port-forward -n nexus svc/prometheus 9090:9090

# Grafana
kubectl port-forward -n nexus svc/grafana 3000:3000
# Access at http://localhost:3000 (admin/admin123)
```

## 💾 Storage Configuration

All PersistentVolumeClaims use **dynamic provisioning**:

| Cluster | Default StorageClass | Notes |
|---------|---------------------|-------|
| Minikube | `standard` | Enable with `minikube addons enable default-storageclass` |
| GKE | `standard` or `standard-rwo` | HDD or SSD |
| EKS | `gp2` | GP2 EBS volumes |
| AKS | `default` | Azure Disk |

To use a specific StorageClass:

```yaml
spec:
  storageClassName: fast-ssd  # Your storage class
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

## 📊 Scaling Services

```bash
# Scale SQL Query Generator
kubectl scale deployment/sql-query-generator --replicas=5 -n default

# Auto-scaling
kubectl autoscale deployment sql-query-generator \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n default
```

## 🔄 Updating Services

```bash
# Update image
kubectl set image deployment/sql-query-generator \
  sql-query-generator=trahulprabhu38/sql-query-generator:v2 \
  -n default

# Check rollout status
kubectl rollout status deployment/sql-query-generator -n default

# Rollback if needed
kubectl rollout undo deployment/sql-query-generator -n default
```

## 🐛 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n default
kubectl get pods -n nexus

# Describe pod
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>

# Previous logs (if crashed)
kubectl logs <pod-name> -n <namespace> --previous
```

### PVC Not Binding

```bash
# Check PVC status
kubectl get pvc --all-namespaces

# Check StorageClass
kubectl get storageclass

# For minikube
minikube addons enable default-storageclass
minikube addons enable storage-provisioner
```

### ConfigMap/Secret Not Found

```bash
# List all configmaps
kubectl get configmap -n default
kubectl get configmap -n nexus

# Apply if missing
kubectl apply -f 00-namespace.yaml
kubectl apply -f secrets.yml
kubectl apply -f configmap.yml
```

### Grafana ConfigMap Error

If you see "Resource not found: v1/ConfigMap:grafana-datasources":

```bash
# The ConfigMaps are defined in grafana-deployment.yaml
# Ensure you apply it in correct order:
kubectl apply -f 00-namespace.yaml  # First
kubectl apply -f grafana-deployment.yaml  # Then this
```

### Service Not Accessible

```bash
# Check service
kubectl get svc <service-name> -n <namespace>

# Check endpoints
kubectl get endpoints <service-name> -n <namespace>

# Test from within cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://<service-name>.<namespace>:8000
```

## 🧹 Cleanup

```bash
# Delete everything
./delete-all.sh

# Or delete manually
kubectl delete namespace nexus
kubectl delete -f deployment.yml
kubectl delete -f svc.yml
kubectl delete -f sql-query-gen-deployment.yaml
kubectl delete -f sql-query-gen-service.yaml
```

## 🔒 Security Notes

1. **Change default passwords**:
   - Grafana: admin/admin123 → Change immediately!
   - PostgreSQL: Update secrets.yml

2. **Use real secrets**: The current secrets.yml has base64 encoded values. Replace with actual secrets.

3. **Create secrets securely**:
```bash
kubectl create secret generic my-secret \
  --from-literal=password='my-secure-password' \
  --dry-run=client -o yaml > secret.yaml
```

## 📚 Additional Resources

- **Jenkins Setup**: See `/JENKINS_SETUP.md` in root directory
- **Monitoring Guide**: See `/monitoring/README.md` in root directory
- **Quick Start**: See `/QUICK_START.md` in root directory
- **Service Instrumentation**: See `/monitoring/example-instrumentation.py`

## 🎯 Next Steps

1. ✅ Deploy services using `./deploy-all.sh`
2. ✅ Access Grafana and change default password
3. ⏳ Add Prometheus metrics to your services
4. ⏳ Create custom Grafana dashboards
5. ⏳ Set up alerting rules
6. ⏳ Configure CI/CD pipeline

---

**All issues fixed! Ready to deploy!** 🎉
