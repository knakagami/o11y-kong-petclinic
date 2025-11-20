#!/bin/bash

# Deploy Spring PetClinic Microservices to Kubernetes (k3s)
# This script deploys all microservices in the correct order with health checks

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

# Helper function to wait for deployment to be ready
wait_for_deployment() {
    local namespace=$1
    local deployment=$2
    local timeout=${3:-300}  # Default 5 minutes
    
    print_message "$YELLOW" "Waiting for deployment/$deployment to be ready..."
    
    if kubectl wait --for=condition=available --timeout=${timeout}s \
        deployment/$deployment -n $namespace 2>/dev/null; then
        print_message "$GREEN" "✓ $deployment is ready"
        return 0
    else
        print_message "$RED" "✗ $deployment failed to become ready within ${timeout}s"
        return 1
    fi
}

# Helper function to check if pod is running
check_pod_running() {
    local namespace=$1
    local app=$2
    
    pod_count=$(kubectl get pods -n $namespace -l app=$app --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    if [ "$pod_count" -gt 0 ]; then
        return 0
    else
        return 1
    fi
}

print_message "$BLUE" "============================================"
print_message "$BLUE" "Spring PetClinic Microservices Deployment"
print_message "$BLUE" "============================================"
echo ""

# Step 1: Create namespace
print_message "$YELLOW" "Step 1: Creating namespace..."
kubectl apply -f k8s/namespace.yaml
echo ""

# Step 2: Deploy Config Server
print_message "$YELLOW" "Step 2: Deploying Config Server..."
kubectl apply -f k8s/config-server/
wait_for_deployment petclinic config-server 300
echo ""

# Wait a bit for config server to be fully ready
print_message "$YELLOW" "Waiting 30 seconds for Config Server to be fully operational..."
sleep 30
echo ""

# Step 3: Deploy Discovery Server (Eureka)
print_message "$YELLOW" "Step 3: Deploying Discovery Server (Eureka)..."
kubectl apply -f k8s/discovery-server/
wait_for_deployment petclinic discovery-server 300
echo ""

# Wait a bit for discovery server to be fully ready
print_message "$YELLOW" "Waiting 30 seconds for Discovery Server to be fully operational..."
sleep 30
echo ""

# Step 4: Deploy Business Services (in parallel)
print_message "$YELLOW" "Step 4: Deploying Business Services..."

print_message "$BLUE" "Deploying Customers Service..."
kubectl apply -f k8s/customers-service/ &

print_message "$BLUE" "Deploying Visits Service..."
kubectl apply -f k8s/visits-service/ &

print_message "$BLUE" "Deploying Vets Service..."
kubectl apply -f k8s/vets-service/ &

print_message "$BLUE" "Deploying GenAI Service (Java)..."
kubectl apply -f k8s/genai-service/ &

print_message "$BLUE" "Deploying GenAI Python Service..."
kubectl apply -f k8s/genai-python/ &

# Wait for all background jobs to complete
wait

echo ""
print_message "$YELLOW" "Waiting for business services to be ready..."

# Wait for each service to be ready
wait_for_deployment petclinic customers-service 300 &
wait_for_deployment petclinic visits-service 300 &
wait_for_deployment petclinic vets-service 300 &
wait_for_deployment petclinic genai-service 300 &
wait_for_deployment petclinic genai-python 300 &

# Wait for all health checks
wait

echo ""

# Step 5: Deploy Admin Server
print_message "$YELLOW" "Step 5: Deploying Admin Server..."
kubectl apply -f k8s/admin-server/
wait_for_deployment petclinic admin-server 300
echo ""

# Step 6: Deploy Frontend (Web UI)
print_message "$YELLOW" "Step 6: Deploying Frontend (Web UI)..."
kubectl apply -f k8s/frontend/
wait_for_deployment petclinic frontend 300
echo ""

# Step 7: Display deployment status
print_message "$GREEN" "============================================"
print_message "$GREEN" "Deployment Summary"
print_message "$GREEN" "============================================"
echo ""

print_message "$BLUE" "Pods in petclinic namespace:"
kubectl get pods -n petclinic
echo ""

print_message "$BLUE" "Services in petclinic namespace:"
kubectl get services -n petclinic
echo ""

print_message "$GREEN" "============================================"
print_message "$GREEN" "✓ All services deployed successfully!"
print_message "$GREEN" "============================================"
echo ""

print_message "$YELLOW" "Next steps:"
echo "1. Deploy Kong Gateway: ./scripts/deploy-kong.sh"
echo "2. Check service status: kubectl get all -n petclinic"
echo "3. View logs: kubectl logs -f deployment/<service-name> -n petclinic"
echo ""

print_message "$BLUE" "Service Endpoints (within cluster):"
echo "- Config Server: http://config-server.petclinic.svc.cluster.local:8888"
echo "- Discovery Server: http://discovery-server.petclinic.svc.cluster.local:8761"
echo "- Frontend (Web UI): http://frontend.petclinic.svc.cluster.local:8080"
echo "- Customers Service: http://customers-service.petclinic.svc.cluster.local:8081"
echo "- Visits Service: http://visits-service.petclinic.svc.cluster.local:8082"
echo "- Vets Service: http://vets-service.petclinic.svc.cluster.local:8083"
echo "- GenAI Service (Java): http://genai-service.petclinic.svc.cluster.local:8084"
echo "- GenAI Python Service: http://genai-python.petclinic.svc.cluster.local:8085"
echo "- Admin Server: http://admin-server.petclinic.svc.cluster.local:9090"
echo ""

