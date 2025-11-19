#!/bin/bash

# Deploy Kong API Gateway with Ingress Controller to Kubernetes (k3s)
# This script installs Kong using Helm and applies routing configuration

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$BLUE" "============================================"
print_message "$BLUE" "Kong API Gateway Deployment"
print_message "$BLUE" "============================================"
echo ""

# Step 1: Check if Helm is installed
print_message "$YELLOW" "Step 1: Checking prerequisites..."
if ! command -v helm &> /dev/null; then
    print_message "$RED" "✗ Helm is not installed. Please install Helm first."
    echo "Visit: https://helm.sh/docs/intro/install/"
    exit 1
fi
print_message "$GREEN" "✓ Helm is installed"
echo ""

# Step 2: Add Kong Helm repository
print_message "$YELLOW" "Step 2: Adding Kong Helm repository..."
helm repo add kong https://charts.konghq.com
helm repo update
print_message "$GREEN" "✓ Kong Helm repository added and updated"
echo ""

# Step 3: Create kong namespace
print_message "$YELLOW" "Step 3: Creating kong namespace..."
kubectl create namespace kong --dry-run=client -o yaml | kubectl apply -f -
print_message "$GREEN" "✓ Kong namespace created"
echo ""

# Step 4: Install Kong using Helm
print_message "$YELLOW" "Step 4: Installing Kong Gateway with Ingress Controller..."
helm upgrade --install kong kong/ingress \
    --namespace kong \
    --values kong/values.yaml \
    --wait \
    --timeout 10m
print_message "$GREEN" "✓ Kong Gateway installed successfully"
echo ""

# Wait for Kong to be ready
print_message "$YELLOW" "Waiting for Kong pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-kong -n kong --timeout=300s
print_message "$GREEN" "✓ Kong pods are ready"
echo ""

# Step 5: Apply Kong Ingress resources
print_message "$YELLOW" "Step 5: Applying Kong Ingress resources for PetClinic services..."
kubectl apply -f kong/kong-resources.yaml
print_message "$GREEN" "✓ Kong Ingress resources applied"
echo ""

# Step 6: Display Kong deployment status
print_message "$GREEN" "============================================"
print_message "$GREEN" "Deployment Summary"
print_message "$GREEN" "============================================"
echo ""

print_message "$BLUE" "Kong Pods:"
kubectl get pods -n kong
echo ""

print_message "$BLUE" "Kong Services:"
kubectl get services -n kong
echo ""

print_message "$BLUE" "Kong Ingress Resources:"
kubectl get ingress -n petclinic
echo ""

print_message "$BLUE" "Kong Plugins:"
kubectl get kongplugin -n petclinic 2>/dev/null || echo "No Kong plugins found"
echo ""

# Get Kong Proxy Service details
PROXY_SERVICE=$(kubectl get svc -n kong -l app.kubernetes.io/name=ingress-kong,app.kubernetes.io/component=app -o jsonpath='{.items[0].metadata.name}')
PROXY_PORT=$(kubectl get svc $PROXY_SERVICE -n kong -o jsonpath='{.spec.ports[?(@.name=="kong-proxy")].nodePort}')
ADMIN_PORT=$(kubectl get svc -n kong -l app.kubernetes.io/name=ingress-kong,app.kubernetes.io/component=app -o jsonpath='{.items[0].spec.ports[?(@.name=="kong-admin")].nodePort}')

print_message "$GREEN" "============================================"
print_message "$GREEN" "✓ Kong Gateway deployed successfully!"
print_message "$GREEN" "============================================"
echo ""

print_message "$YELLOW" "Kong Access Information:"
echo ""
print_message "$BLUE" "Kong Proxy (API Gateway):"
echo "  - HTTP:  http://localhost:${PROXY_PORT}"
echo "  - HTTPS: https://localhost:32443 (if configured)"
echo ""
print_message "$BLUE" "Kong Admin API:"
echo "  - HTTP: http://localhost:${ADMIN_PORT}"
echo ""

print_message "$YELLOW" "API Endpoints (through Kong Gateway):"
echo "  - Customers API: http://localhost:${PROXY_PORT}/api/customer"
echo "  - Visits API:    http://localhost:${PROXY_PORT}/api/visit"
echo "  - Vets API:      http://localhost:${PROXY_PORT}/api/vet"
echo "  - GenAI API:     http://localhost:${PROXY_PORT}/api/genai"
echo "  - Admin UI:      http://localhost:${PROXY_PORT}/admin"
echo ""

print_message "$YELLOW" "Example API calls:"
echo "  curl http://localhost:${PROXY_PORT}/api/vet/vets"
echo "  curl http://localhost:${PROXY_PORT}/api/customer/owners"
echo ""

print_message "$BLUE" "Useful commands:"
echo "  - View Kong logs: kubectl logs -f deployment/kong-controller -n kong"
echo "  - View Kong config: kubectl get ingress -n petclinic"
echo "  - Test Kong Admin: curl http://localhost:${ADMIN_PORT}/status"
echo ""

print_message "$GREEN" "Setup complete! 🎉"
echo ""

