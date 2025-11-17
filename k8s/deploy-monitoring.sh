#!/bin/bash

# Nexus Monitoring Stack Deployment Script
# This script deploys Prometheus and Grafana to your Kubernetes cluster

set -e

echo "========================================="
echo "Nexus Monitoring Stack Deployment"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
echo ""

# Get current context
CONTEXT=$(kubectl config current-context)
print_info "Current context: $CONTEXT"
echo ""

# Confirm deployment
read -p "Do you want to deploy the monitoring stack to this cluster? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

echo ""
print_info "Step 1/5: Deploying Prometheus..."
echo ""

# Deploy Prometheus
kubectl apply -f ../k8s/prometheus-deployment.yaml

# Wait for Prometheus to be ready
print_info "Waiting for Prometheus to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring

print_info "Prometheus deployed successfully"
echo ""

print_info "Step 2/5: Deploying Grafana..."
echo ""

# Deploy Grafana
kubectl apply -f ../k8s/grafana-deployment.yaml

# Wait for Grafana to be ready
print_info "Waiting for Grafana to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n monitoring

print_info "Grafana deployed successfully"
echo ""

print_info "Step 3/5: Verifying deployments..."
echo ""

# Check pod status
kubectl get pods -n monitoring

echo ""
print_info "Step 4/5: Getting service information..."
echo ""

# Get service information
kubectl get svc -n monitoring

echo ""
print_info "Step 5/5: Getting access information..."
echo ""

# Get NodePort for Prometheus
PROMETHEUS_PORT=$(kubectl get svc prometheus -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')
# Get NodePort for Grafana
GRAFANA_PORT=$(kubectl get svc grafana -n monitoring -o jsonpath='{.spec.ports[0].nodePort}')

# Try to get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
if [ -z "$NODE_IP" ]; then
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
fi

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Prometheus UI:"
echo "  URL: http://${NODE_IP}:${PROMETHEUS_PORT}"
echo "  or use port-forward: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "  then access: http://localhost:9090"
echo ""
echo "Grafana UI:"
echo "  URL: http://${NODE_IP}:${GRAFANA_PORT}"
echo "  or use port-forward: kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "  then access: http://localhost:3000"
echo "  Default credentials: admin / admin123"
echo ""
print_warning "IMPORTANT: Change the default Grafana password after first login!"
echo ""
echo "Next steps:"
echo "  1. Access Grafana and change the default password"
echo "  2. Verify Prometheus is scraping targets: Status → Targets"
echo "  3. View the pre-configured 'Nexus Services Overview' dashboard"
echo "  4. Add prometheus annotations to your service deployments"
echo "  5. Instrument your services with prometheus-client library"
echo ""
echo "For detailed instructions, see monitoring/README.md"
echo ""

# Optional: Add annotations to existing deployments
echo ""
read -p "Do you want to add Prometheus annotations to existing deployments? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Adding Prometheus annotations to deployments..."

    # Add annotations to SQL Query Generator
    kubectl patch deployment sql-query-gen-deployment -n default -p '{"spec":{"template":{"metadata":{"annotations":{"prometheus.io/scrape":"true","prometheus.io/port":"8000","prometheus.io/path":"/metrics"}}}}}' 2>/dev/null || print_warning "Could not patch sql-query-gen-deployment (might not exist yet)"

    # Add annotations to Intent Agent
    kubectl patch deployment intent-agent-deployment -n default -p '{"spec":{"template":{"metadata":{"annotations":{"prometheus.io/scrape":"true","prometheus.io/port":"8080","prometheus.io/path":"/metrics"}}}}}' 2>/dev/null || print_warning "Could not patch intent-agent-deployment (might not exist yet)"

    # Add annotations to SQL Validator
    kubectl patch deployment sql-validator-api-deployment -n default -p '{"spec":{"template":{"metadata":{"annotations":{"prometheus.io/scrape":"true","prometheus.io/port":"8000","prometheus.io/path":"/metrics"}}}}}' 2>/dev/null || print_warning "Could not patch sql-validator-api-deployment (might not exist yet)"

    # Add annotations to Column Pruning
    kubectl patch deployment column-prune-deployment -n default -p '{"spec":{"template":{"metadata":{"annotations":{"prometheus.io/scrape":"true","prometheus.io/port":"8501","prometheus.io/path":"/metrics"}}}}}' 2>/dev/null || print_warning "Could not patch column-prune-deployment (might not exist yet)"

    # Add annotations to Frontend
    kubectl patch deployment frontend-deployment -n default -p '{"spec":{"template":{"metadata":{"annotations":{"prometheus.io/scrape":"true","prometheus.io/port":"80","prometheus.io/path":"/metrics"}}}}}' 2>/dev/null || print_warning "Could not patch frontend-deployment (might not exist yet)"

    print_info "Annotations added (if deployments existed)"
fi

echo ""
print_info "Monitoring stack deployment complete!"
echo ""
