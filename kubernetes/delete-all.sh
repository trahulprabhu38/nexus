#!/bin/bash

# Nexus Platform - Complete Deletion Script
# This script removes all Nexus services and resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "========================================="
echo "Nexus Platform Deletion"
echo "========================================="
echo ""

print_warning "This will delete ALL Nexus resources from the cluster!"
print_warning "This includes:"
echo "  - All deployments in 'default' and 'nexus' namespaces"
echo "  - All services"
echo "  - All PersistentVolumeClaims (data will be lost!)"
echo "  - All ConfigMaps and Secrets"
echo "  - The 'nexus' namespace"
echo ""

read -p "Are you sure you want to continue? (yes/no) " -r
echo ""
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Deletion cancelled"
    exit 0
fi

print_info "Deleting Nexus resources..."
echo ""

# Delete monitoring stack
print_info "Deleting monitoring stack (Prometheus, Grafana)..."
kubectl delete -f grafana-deployment.yaml --ignore-not-found=true
kubectl delete -f prometheus-deployment.yaml --ignore-not-found=true

# Delete microservices
print_info "Deleting microservices..."
kubectl delete -f frontend-deploy.yml --ignore-not-found=true
kubectl delete -f frontend-svc.yml --ignore-not-found=true
kubectl delete -f column-prune-deploy.yml --ignore-not-found=true
kubectl delete -f column-prune-svc.yml --ignore-not-found=true
kubectl delete -f intent-agent-deployment.yaml --ignore-not-found=true
kubectl delete -f intent-agent-service.yaml --ignore-not-found=true
kubectl delete -f sql-query-gen-deployment.yaml --ignore-not-found=true
kubectl delete -f sql-query-gen-service.yaml --ignore-not-found=true

# Delete database and validator
print_info "Deleting database and SQL validator..."
kubectl delete -f deployment.yml --ignore-not-found=true
kubectl delete -f svc.yml --ignore-not-found=true

# Delete ConfigMaps and Secrets
print_info "Deleting ConfigMaps and Secrets..."
kubectl delete -f configmap.yml --ignore-not-found=true
kubectl delete -f secrets.yml --ignore-not-found=true
kubectl delete -f sql-query-gen-configmap.yaml --ignore-not-found=true
kubectl delete -f sql-query-gen-secrets.yaml --ignore-not-found=true

# Delete namespace
print_info "Deleting nexus namespace..."
kubectl delete namespace nexus --ignore-not-found=true

echo ""
print_info "Checking remaining resources..."
echo ""

# Check if any resources remain
echo "Remaining deployments in default:"
kubectl get deployments -n default | grep -E "(sql-|postgres|nexus)" || echo "  None"

echo ""
echo "Remaining services in default:"
kubectl get svc -n default | grep -E "(sql-|postgres|nexus)" || echo "  None"

echo ""
echo "Remaining PVCs:"
kubectl get pvc --all-namespaces | grep -E "(postgres|prometheus|grafana)" || echo "  None"

echo ""
print_info "Deletion complete!"
print_warning "Note: PersistentVolumes may still exist depending on retention policy"
print_info "To list PVs: kubectl get pv"
print_info "To delete a specific PV: kubectl delete pv <pv-name>"
echo ""
