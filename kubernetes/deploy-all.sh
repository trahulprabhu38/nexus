#!/bin/bash

# Nexus Platform - Complete Deployment Script
# This script deploys all Nexus services in the correct order

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "========================================="
echo "Nexus Platform Deployment"
echo "========================================="
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if kubectl can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

print_info "Connected to Kubernetes cluster successfully"
CONTEXT=$(kubectl config current-context)
print_info "Current context: $CONTEXT"
echo ""

# Confirm deployment
read -p "Do you want to deploy the Nexus platform to this cluster? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

echo ""
print_step "Step 1/7: Creating Namespaces..."
echo ""

# Create namespaces
kubectl apply -f 00-namespace.yaml
sleep 2

echo ""
print_step "Step 2/7: Creating Secrets and ConfigMaps..."
echo ""

# Apply secrets and configmaps
kubectl apply -f secrets.yml
kubectl apply -f configmap.yml
kubectl apply -f sql-query-gen-secrets.yaml
kubectl apply -f sql-query-gen-configmap.yaml

sleep 2

echo ""
print_step "Step 3/7: Creating PersistentVolumeClaims..."
echo ""

# Apply PVCs (they are in deployment.yml, prometheus-deployment.yaml, and grafana-deployment.yaml)
print_info "PVCs will be created with deployments..."

echo ""
print_step "Step 4/7: Deploying Database (PostgreSQL)..."
echo ""

# Deploy PostgreSQL and SQL Validator
kubectl apply -f deployment.yml
kubectl apply -f svc.yml

print_info "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres-deployment -n default || print_warning "PostgreSQL deployment timeout - check manually"

echo ""
print_step "Step 5/7: Deploying Microservices..."
echo ""

# Deploy SQL Query Generator
print_info "Deploying SQL Query Generator..."
kubectl apply -f sql-query-gen-deployment.yaml
kubectl apply -f sql-query-gen-service.yaml

# Deploy Intent Agent
print_info "Deploying Intent Agent..."
kubectl apply -f intent-agent-deployment.yaml
kubectl apply -f intent-agent-service.yaml

# Deploy Column Pruning
print_info "Deploying Column Pruning..."
kubectl apply -f column-prune-deploy.yml
kubectl apply -f column-prune-svc.yml

# Deploy Frontend
print_info "Deploying Frontend..."
kubectl apply -f frontend-deploy.yml
kubectl apply -f frontend-svc.yml

print_info "Waiting for microservices to be ready..."
sleep 10

echo ""
print_step "Step 6/7: Deploying Monitoring Stack..."
echo ""

# Deploy Prometheus
print_info "Deploying Prometheus..."
kubectl apply -f prometheus-deployment.yaml

print_info "Waiting for Prometheus to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n nexus || print_warning "Prometheus deployment timeout - check manually"

# Deploy Grafana
print_info "Deploying Grafana..."
kubectl apply -f grafana-deployment.yaml

print_info "Waiting for Grafana to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n nexus || print_warning "Grafana deployment timeout - check manually"

echo ""
print_step "Step 7/7: Verifying Deployment..."
echo ""

# Check deployment status
print_info "Checking deployments in default namespace..."
kubectl get deployments -n default

echo ""
print_info "Checking deployments in nexus namespace..."
kubectl get deployments -n nexus

echo ""
print_info "Checking all pods..."
kubectl get pods --all-namespaces | grep -E "(default|nexus|NAME)"

echo ""
print_info "Checking all services..."
kubectl get svc --all-namespaces | grep -E "(default|nexus|NAME)"

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""

# Get service endpoints
print_info "Service Endpoints:"
echo ""

# Get NodePort for services
echo "Services in default namespace:"
kubectl get svc -n default -o wide

echo ""
echo "Services in nexus namespace:"
kubectl get svc -n nexus -o wide

echo ""
print_info "To access services:"
echo ""

# Try to get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null)
if [ -z "$NODE_IP" ]; then
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
fi

if [ -n "$NODE_IP" ]; then
    echo "Node IP: $NODE_IP"
    echo ""

    # Get NodePort for each service
    SQL_QUERY_PORT=$(kubectl get svc sql-query-generator-nodeport -n default -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    SQL_VALIDATOR_PORT=$(kubectl get svc sql-validator-api-service -n default -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    INTENT_AGENT_PORT=$(kubectl get svc intent-agent -n nexus -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    COLUMN_PRUNE_PORT=$(kubectl get svc nexus-column-prune-service -n nexus -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    FRONTEND_PORT=$(kubectl get svc nexus-frontend-service -n nexus -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    PROMETHEUS_PORT=$(kubectl get svc prometheus -n nexus -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    GRAFANA_PORT=$(kubectl get svc grafana -n nexus -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)

    echo "Application Services:"
    [ -n "$SQL_QUERY_PORT" ] && echo "  SQL Query Generator: http://${NODE_IP}:${SQL_QUERY_PORT}"
    [ -n "$SQL_VALIDATOR_PORT" ] && echo "  SQL Validator API:   http://${NODE_IP}:${SQL_VALIDATOR_PORT}"
    [ -n "$INTENT_AGENT_PORT" ] && echo "  Intent Agent:        http://${NODE_IP}:${INTENT_AGENT_PORT}"
    [ -n "$COLUMN_PRUNE_PORT" ] && echo "  Column Pruning:      http://${NODE_IP}:${COLUMN_PRUNE_PORT}"
    [ -n "$FRONTEND_PORT" ] && echo "  Frontend:            http://${NODE_IP}:${FRONTEND_PORT}"
    echo ""
    echo "Monitoring Services:"
    [ -n "$PROMETHEUS_PORT" ] && echo "  Prometheus:          http://${NODE_IP}:${PROMETHEUS_PORT}"
    [ -n "$GRAFANA_PORT" ] && echo "  Grafana:             http://${NODE_IP}:${GRAFANA_PORT} (admin/admin123)"
fi

echo ""
print_info "Port Forwarding Options:"
echo "  kubectl port-forward -n default svc/sql-query-generator 8000:80"
echo "  kubectl port-forward -n default svc/sql-validator-api-service 8001:8000"
echo "  kubectl port-forward -n nexus svc/intent-agent 8080:80"
echo "  kubectl port-forward -n nexus svc/nexus-column-prune-service 8501:8501"
echo "  kubectl port-forward -n nexus svc/nexus-frontend-service 3000:80"
echo "  kubectl port-forward -n nexus svc/prometheus 9090:9090"
echo "  kubectl port-forward -n nexus svc/grafana 3000:3000"

echo ""
print_warning "IMPORTANT: Change the default Grafana password after first login!"

echo ""
print_info "Next Steps:"
echo "  1. Access services using the URLs above"
echo "  2. Check logs: kubectl logs -f deployment/<name> -n <namespace>"
echo "  3. Monitor pods: kubectl get pods --all-namespaces -w"
echo "  4. Configure Grafana dashboards"
echo "  5. Add metrics to your services (see monitoring/README.md)"

echo ""
print_info "To delete all resources:"
echo "  ./delete-all.sh"
echo "  or"
echo "  kubectl delete namespace nexus"
echo "  kubectl delete -f deployment.yml"
echo "  kubectl delete -f svc.yml"

echo ""
print_info "Deployment script completed successfully!"
echo ""
