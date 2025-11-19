# Contributing to Spring PetClinic Kong Gateway

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Test your changes thoroughly
6. Commit your changes with clear commit messages
7. Push to your fork
8. Submit a pull request

## Development Setup

### Prerequisites

- Kubernetes cluster (k3s recommended)
- kubectl
- Helm 3
- Git

### Local Development

```bash
# Clone the repository
git clone <your-fork-url>
cd o11y-kong

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Test your changes
./scripts/deploy-services.sh
./scripts/deploy-kong.sh
```

## Code Style

- Use clear, descriptive variable names
- Add comments for complex logic
- Follow YAML best practices for Kubernetes manifests
- Keep shell scripts POSIX-compliant where possible

## Kubernetes Manifests

- Use proper indentation (2 spaces)
- Include resource limits and requests
- Add appropriate labels and annotations
- Include health checks (liveness and readiness probes)

## Shell Scripts

- Start with `#!/bin/bash`
- Use `set -e` to exit on error
- Add helpful error messages
- Include usage documentation

## Testing

Before submitting a pull request:

1. Deploy to a test cluster
2. Verify all services start correctly
3. Test Kong Gateway routing
4. Test API endpoints through Kong
5. Check logs for errors

```bash
# Deploy and test
./scripts/deploy-services.sh
./scripts/deploy-kong.sh

# Verify deployment
kubectl get pods -n petclinic
kubectl get pods -n kong

# Test API endpoints
curl http://localhost:32000/api/vet/vets
curl http://localhost:32000/api/customer/owners
```

## Commit Messages

Use clear, descriptive commit messages:

```
Add rate limiting plugin to Kong configuration

- Configure 100 requests per minute limit
- Apply to all services globally
- Update documentation
```

## Pull Request Process

1. Update documentation for any changed functionality
2. Add or update tests as needed
3. Ensure all CI checks pass
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

## Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Configuration change

## Testing
Describe how you tested your changes

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tested on Kubernetes cluster
- [ ] All services deploy successfully
- [ ] API endpoints work through Kong
```

## Reporting Issues

When reporting issues, please include:

- Description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (k3s version, OS, etc.)
- Relevant logs

## Questions?

Feel free to open an issue for questions or discussion.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (Apache License 2.0).

