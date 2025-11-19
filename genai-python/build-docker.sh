#!/bin/bash

# Build Docker image for GenAI Python Service
# This script builds the Docker image locally for deployment to k3s

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$BLUE" "============================================"
print_message "$BLUE" "GenAI Python Service - Docker Build"
print_message "$BLUE" "============================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Docker image settings
IMAGE_NAME="genai-python"
IMAGE_TAG="${1:-latest}"
VERSION_TAG="v1.0.0"

print_message "$YELLOW" "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# Build the Docker image
print_message "$BLUE" "Step 1: Building Docker image..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

if [ $? -eq 0 ]; then
    print_message "$GREEN" "✓ Docker image built successfully"
else
    print_message "$RED" "✗ Docker build failed"
    exit 1
fi

echo ""

# Tag with version
print_message "$BLUE" "Step 2: Tagging image with version ${VERSION_TAG}..."
docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${IMAGE_NAME}:${VERSION_TAG}"

if [ $? -eq 0 ]; then
    print_message "$GREEN" "✓ Image tagged successfully"
else
    print_message "$RED" "✗ Image tagging failed"
    exit 1
fi

echo ""

# Display image information
print_message "$GREEN" "============================================"
print_message "$GREEN" "Build Complete!"
print_message "$GREEN" "============================================"
echo ""

print_message "$BLUE" "Docker images created:"
docker images | grep "${IMAGE_NAME}"

echo ""
print_message "$YELLOW" "Next steps:"
echo "1. Test the image locally:"
echo "   docker run -p 8085:8084 -e OPENAI_API_KEY=your-key ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "2. For k3s deployment, import the image:"
echo "   sudo k3s ctr images import <(docker save ${IMAGE_NAME}:${IMAGE_TAG})"
echo "   OR"
echo "   docker save ${IMAGE_NAME}:${IMAGE_TAG} | sudo k3s ctr images import -"
echo ""
echo "3. Deploy to Kubernetes:"
echo "   kubectl apply -f ../k8s/genai-python/"
echo ""

print_message "$GREEN" "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
print_message "$GREEN" "Version: ${VERSION_TAG}"
echo ""

