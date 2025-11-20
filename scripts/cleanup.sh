#!/bin/bash

# Cleanup script to remove all deployed resources
# Use with caution - this will delete all PetClinic and Kong resources

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
print_message "$BLUE" "Spring PetClinic Cleanup"
print_message "$BLUE" "============================================"
echo ""

print_message "$RED" "WARNING: This will delete all PetClinic and Kong resources!"
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_message "$YELLOW" "Cleanup cancelled."
    exit 0
fi

# Delete Kong resources
print_message "$YELLOW" "Removing Kong resources..."
kubectl delete -f kong/kong-resources.yaml --ignore-not-found=true
echo ""

# Uninstall Kong Helm release
print_message "$YELLOW" "Uninstalling Kong Gateway..."
helm uninstall kong -n kong --ignore-not-found 2>/dev/null || true
echo ""

# Delete Kong namespace
print_message "$YELLOW" "Deleting kong namespace..."
kubectl delete namespace kong --ignore-not-found=true
echo ""

# Delete PetClinic services
print_message "$YELLOW" "Removing PetClinic services..."
kubectl delete -f k8s/admin-server/ --ignore-not-found=true
kubectl delete -f k8s/genai-service/ --ignore-not-found=true
kubectl delete -f k8s/vets-service/ --ignore-not-found=true
kubectl delete -f k8s/visits-service/ --ignore-not-found=true
kubectl delete -f k8s/customers-service/ --ignore-not-found=true
kubectl delete -f k8s/discovery-server/ --ignore-not-found=true
kubectl delete -f k8s/config-server/ --ignore-not-found=true
echo ""

# Delete PetClinic namespace
print_message "$YELLOW" "Deleting petclinic namespace..."
kubectl delete namespace petclinic --ignore-not-found=true
echo ""

print_message "$GREEN" "============================================"
print_message "$GREEN" "✓ Cleanup completed successfully!"
print_message "$GREEN" "============================================"
echo ""

print_message "$BLUE" "Verify cleanup:"
echo "  kubectl get all -n petclinic"
echo "  kubectl get all -n kong"
echo ""

