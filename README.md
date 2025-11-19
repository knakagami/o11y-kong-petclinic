# Spring PetClinic with Kong API Gateway on Kubernetes

A cloud-native implementation of the Spring PetClinic microservices application, using Kong API Gateway for API management and deployed on Kubernetes (k3s).

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Deployment Details](#deployment-details)
- [Kong Gateway Configuration](#kong-gateway-configuration)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

## 🏗️ Architecture

This project replaces the traditional Spring Cloud Gateway with Kong API Gateway, providing enhanced API management capabilities including rate limiting, authentication, and advanced routing.

```
┌─────────────────────────────────────────────────────────────┐
│                        Kong API Gateway                      │
│                  (NodePort: 32000/32443)                    │
└──────────────┬──────────────┬──────────────┬────────────────┘
               │              │              │
       ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
       │  Customers   │ │  Visits  │ │    Vets    │
       │   Service    │ │  Service │ │  Service   │
       │   (8081)     │ │  (8082)  │ │   (8083)   │
       └──────┬───────┘ └────┬─────┘ └─────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼─────────┐
                    │ Discovery Server │
                    │    (Eureka)      │
                    │     (8761)       │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Config Server   │
                    │     (8888)       │
                    └──────────────────┘
```

### Components

#### Infrastructure Services
- **Config Server** (8888): Centralized configuration management
- **Discovery Server** (8761): Eureka service registry for service discovery
- **Admin Server** (9090): Spring Boot Admin for monitoring

#### Business Services
- **Customers Service** (8081): Manages pet owners and their pets
- **Visits Service** (8082): Manages veterinary visit records
- **Vets Service** (8083): Manages veterinarian information
- **GenAI Service** (8084): AI-powered features (optional)

#### API Gateway
- **Kong Gateway**: API gateway replacing Spring Cloud Gateway
  - Traffic routing and load balancing
  - Rate limiting and throttling
  - CORS handling
  - Request/response transformation
  - Metrics collection (Prometheus)

## 🔧 Prerequisites

### Required Tools
- **Kubernetes**: k3s, k8s, or any Kubernetes cluster (v1.24+)
- **kubectl**: Kubernetes CLI tool
- **Helm**: Package manager for Kubernetes (v3.0+)
- **Git**: Version control

### System Requirements
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **CPU**: 2+ cores
- **Disk**: 10GB free space

### Verify Prerequisites

```bash
# Check Kubernetes
kubectl version --client

# Check Helm
helm version

# Check cluster connection
kubectl cluster-info
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd o11y-kong
```

### 2. Deploy Microservices

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Deploy all Spring PetClinic services
./scripts/deploy-services.sh
```

This script will:
1. Create the `petclinic` namespace
2. Deploy Config Server and wait for it to be ready
3. Deploy Discovery Server (Eureka)
4. Deploy all business services in parallel
5. Deploy Admin Server

### 3. Deploy Kong API Gateway

```bash
# Deploy Kong Gateway with Ingress Controller
./scripts/deploy-kong.sh
```

This script will:
1. Add Kong Helm repository
2. Install Kong using Helm with custom values
3. Apply Kong Ingress resources for routing
4. Configure plugins (CORS, rate limiting, Prometheus)

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n petclinic

# Check services
kubectl get services -n petclinic

# Check Kong pods
kubectl get pods -n kong

# Check ingress resources
kubectl get ingress -n petclinic
```

## 🌐 API Endpoints

### Through Kong Gateway (NodePort: 32000)

All APIs are accessible through Kong Gateway at `http://localhost:32000` (or your node IP).

#### Customers Service

```bash
# List all customers
GET http://localhost:32000/api/customer/owners

# Get customer by ID
GET http://localhost:32000/api/customer/owners/{ownerId}

# Create new customer
POST http://localhost:32000/api/customer/owners
Content-Type: application/json
{
  "firstName": "John",
  "lastName": "Doe",
  "address": "123 Main St",
  "city": "Springfield",
  "telephone": "1234567890"
}

# Search customers by last name
GET http://localhost:32000/api/customer/owners/*/lastname/{lastName}

# Get pet types
GET http://localhost:32000/api/customer/petTypes
```

#### Visits Service

```bash
# Get visits for a pet
GET http://localhost:32000/api/visit/owners/*/pets/{petId}/visits

# Create a new visit
POST http://localhost:32000/api/visit/owners/*/pets/{petId}/visits
Content-Type: application/json
{
  "date": "2024-01-15",
  "description": "Regular checkup"
}
```

#### Vets Service

```bash
# List all veterinarians
GET http://localhost:32000/api/vet/vets
```

#### GenAI Service (Optional)

```bash
# Access GenAI features
GET http://localhost:32000/api/genai/*
```

#### Admin Server

```bash
# Access Spring Boot Admin UI
GET http://localhost:32000/admin
```

### Example curl Commands

```bash
# Get all vets
curl http://localhost:32000/api/vet/vets

# Get all pet types
curl http://localhost:32000/api/customer/petTypes

# Get all owners
curl http://localhost:32000/api/customer/owners

# Create a new owner
curl -X POST http://localhost:32000/api/customer/owners \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Jane",
    "lastName": "Smith",
    "address": "456 Oak Ave",
    "city": "Portland",
    "telephone": "5551234567"
  }'
```

## 📦 Deployment Details

### Namespace

All PetClinic resources are deployed in the `petclinic` namespace, while Kong is deployed in the `kong` namespace.

### Resource Limits

Each service has the following default resource configuration:

```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

### Health Checks

All services include:
- **Liveness Probe**: Ensures pod is alive
- **Readiness Probe**: Ensures pod is ready to accept traffic

Probes use the Spring Boot Actuator `/actuator/health` endpoint.

### Service Dependencies

The deployment follows this order to respect dependencies:
1. Config Server (no dependencies)
2. Discovery Server (depends on Config Server)
3. Business Services (depend on Config Server + Discovery Server)
4. Admin Server (depends on Config Server + Discovery Server)

## 🔐 Kong Gateway Configuration

### Ingress Resources

Kong routes are configured using Kubernetes Ingress resources:

```yaml
/api/customer/* → customers-service:8081
/api/visit/*    → visits-service:8082
/api/vet/*      → vets-service:8083
/api/genai/*    → genai-service:8084
/admin/*        → admin-server:9090
```

### Plugins

The following Kong plugins are configured:

#### Rate Limiting
- Limit: 100 requests per minute per client
- Policy: Local (in-memory)

#### CORS
- Origins: `*` (all origins allowed)
- Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
- Credentials: Enabled

#### Prometheus
- Exposes metrics at Kong's metrics endpoint
- Collects request/response metrics for all services

### Kong Admin API

Access Kong Admin API at `http://localhost:32001`:

```bash
# Check Kong status
curl http://localhost:32001/status

# List all services
curl http://localhost:32001/services

# List all routes
curl http://localhost:32001/routes

# View metrics
curl http://localhost:32001/metrics
```

## 📊 Monitoring and Observability

### Spring Boot Admin

Access the Spring Boot Admin dashboard:

```bash
# Through Kong Gateway
http://localhost:32000/admin

# Direct access (within cluster)
http://admin-server.petclinic.svc.cluster.local:9090
```

### Eureka Dashboard

View registered services in Eureka:

```bash
# Port-forward to access Eureka UI
kubectl port-forward -n petclinic svc/discovery-server 8761:8761

# Open in browser
http://localhost:8761
```

### Kong Metrics

Kong exposes Prometheus metrics:

```bash
# Access metrics endpoint
curl http://localhost:32001/metrics
```

### Service Logs

```bash
# View logs for a specific service
kubectl logs -f deployment/customers-service -n petclinic

# View Kong logs
kubectl logs -f deployment/kong-controller -n kong

# View all logs in namespace
kubectl logs -f -n petclinic --all-containers=true
```

## 🔍 Troubleshooting

### Services Not Starting

```bash
# Check pod status
kubectl get pods -n petclinic

# Describe problematic pod
kubectl describe pod <pod-name> -n petclinic

# Check logs
kubectl logs <pod-name> -n petclinic
```

### Config Server Issues

```bash
# Check Config Server logs
kubectl logs deployment/config-server -n petclinic

# Verify Config Server is accessible
kubectl exec -it deployment/customers-service -n petclinic -- \
  curl http://config-server:8888/actuator/health
```

### Discovery Server Issues

```bash
# Check Eureka logs
kubectl logs deployment/discovery-server -n petclinic

# Port-forward and check UI
kubectl port-forward -n petclinic svc/discovery-server 8761:8761
# Open http://localhost:8761
```

### Kong Gateway Issues

```bash
# Check Kong pod status
kubectl get pods -n kong

# Check Kong logs
kubectl logs -f deployment/kong-controller -n kong

# Verify Kong configuration
kubectl get ingress -n petclinic
kubectl get kongplugin -n petclinic
```

### Network Connectivity

```bash
# Test service-to-service communication
kubectl exec -it deployment/customers-service -n petclinic -- \
  curl http://discovery-server:8761/actuator/health

# Test Kong to backend service
kubectl exec -it -n kong deployment/kong-gateway -- \
  curl http://customers-service.petclinic.svc.cluster.local:8081/actuator/health
```

### Common Issues

1. **Pods in CrashLoopBackOff**
   - Check if dependent services (Config/Discovery) are ready
   - Verify resource limits are not exceeded
   - Check application logs

2. **503 Service Unavailable from Kong**
   - Verify backend services are running
   - Check Ingress configuration
   - Ensure services are registered in Eureka

3. **Slow Startup**
   - Services may take 2-3 minutes to fully start
   - Wait for readiness probes to pass
   - Check resource constraints

## 🧹 Cleanup

To remove all deployed resources:

```bash
# Run cleanup script
./scripts/cleanup.sh

# Or manually delete namespaces
kubectl delete namespace petclinic
kubectl delete namespace kong
```

## 📚 Additional Resources

- [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices)
- [Kong Gateway Documentation](https://docs.konghq.com/)
- [Kong Ingress Controller](https://docs.konghq.com/kubernetes-ingress-controller/)
- [Spring Cloud Documentation](https://spring.io/projects/spring-cloud)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is based on Spring PetClinic, which is licensed under the Apache License 2.0.

## 👥 Authors

- Based on [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices)
- Kong integration and Kubernetes deployment configurations

---

**Note**: This is a demonstration project. For production use, consider:
- Adding authentication and authorization
- Implementing proper secrets management
- Configuring TLS/SSL certificates
- Setting up automated backups
- Implementing proper monitoring and alerting
- Using persistent storage for stateful services

