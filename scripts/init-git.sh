#!/bin/bash

# Initialize Git repository and prepare for GitHub push
# This script helps set up the local Git repository

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
print_message "$BLUE" "Git Repository Initialization"
print_message "$BLUE" "============================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_message "$RED" "✗ Git is not installed. Please install Git first."
    exit 1
fi

# Check if already a git repository
if [ -d ".git" ]; then
    print_message "$YELLOW" "⚠ This directory is already a Git repository."
    read -p "Do you want to reinitialize? (yes/no): " -r
    echo ""
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        rm -rf .git
        print_message "$YELLOW" "Removed existing .git directory"
    else
        print_message "$YELLOW" "Keeping existing repository. Exiting."
        exit 0
    fi
fi

# Initialize git repository
print_message "$YELLOW" "Initializing Git repository..."
git init
print_message "$GREEN" "✓ Git repository initialized"
echo ""

# Set default branch to main
print_message "$YELLOW" "Setting default branch to 'main'..."
git branch -M main
print_message "$GREEN" "✓ Default branch set to 'main'"
echo ""

# Make scripts executable
print_message "$YELLOW" "Making scripts executable..."
chmod +x scripts/*.sh
git update-index --chmod=+x scripts/*.sh
print_message "$GREEN" "✓ Scripts are now executable"
echo ""

# Add all files
print_message "$YELLOW" "Adding files to Git..."
git add .
print_message "$GREEN" "✓ Files added to staging area"
echo ""

# Show status
print_message "$BLUE" "Git Status:"
git status
echo ""

# Create initial commit
print_message "$YELLOW" "Creating initial commit..."
git commit -m "Initial commit: Spring PetClinic with Kong API Gateway on Kubernetes

- Add Kubernetes manifests for all microservices
- Add Kong Gateway Helm configuration
- Add deployment automation scripts
- Add comprehensive documentation
"
print_message "$GREEN" "✓ Initial commit created"
echo ""

print_message "$GREEN" "============================================"
print_message "$GREEN" "✓ Git repository initialized successfully!"
print_message "$GREEN" "============================================"
echo ""

print_message "$YELLOW" "Next steps:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   Go to: https://github.com/new"
echo ""
echo "2. Set the remote repository URL:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
echo ""
echo "   Or with SSH:"
echo "   git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git"
echo ""
echo "3. Push to GitHub:"
echo "   git push -u origin main"
echo ""

print_message "$BLUE" "Useful Git commands:"
echo "  - Check status:        git status"
echo "  - View commit history: git log --oneline"
echo "  - View remotes:        git remote -v"
echo "  - Push changes:        git push"
echo ""

print_message "$GREEN" "Happy coding! 🚀"
echo ""

