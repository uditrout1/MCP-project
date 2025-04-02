# AI Legacy Application Modernization - Deployment Guide

This guide provides instructions for deploying the AI Legacy Application Modernization system in various environments, from local development to production SaaS deployment.

## Table of Contents

1. [Local Development Deployment](#local-development-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
   - [AWS Deployment](#aws-deployment)
   - [Azure Deployment](#azure-deployment)
   - [Google Cloud Deployment](#google-cloud-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Environment Variables](#environment-variables)
6. [Security Considerations](#security-considerations)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Scaling Strategies](#scaling-strategies)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Local Development Deployment

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- venv (Python virtual environment)
- Git

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-legacy-modernization.git
   cd ai-legacy-modernization
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the application:
   Open your browser and navigate to `http://localhost:5000`

## Docker Deployment

### Prerequisites

- Docker
- Docker Compose (optional, for multi-container deployment)

### Steps

1. Build the Docker image:
   ```bash
   docker build -t ai-legacy-modernization .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 --env-file .env ai-legacy-modernization
   ```

3. For multi-container deployment with Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    restart: always
```

## Cloud Deployment

### AWS Deployment

#### Using Elastic Beanstalk

1. Install the AWS CLI and EB CLI:
   ```bash
   pip install awscli awsebcli
   ```

2. Initialize EB application:
   ```bash
   eb init -p python-3.10 ai-legacy-modernization
   ```

3. Create an environment:
   ```bash
   eb create ai-legacy-modernization-env
   ```

4. Deploy the application:
   ```bash
   eb deploy
   ```

#### Using ECS (with Docker)

1. Create an ECR repository:
   ```bash
   aws ecr create-repository --repository-name ai-legacy-modernization
   ```

2. Authenticate Docker to ECR:
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
   ```

3. Build and push the Docker image:
   ```bash
   docker build -t <aws-account-id>.dkr.ecr.<region>.amazonaws.com/ai-legacy-modernization:latest .
   docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/ai-legacy-modernization:latest
   ```

4. Create an ECS cluster, task definition, and service using the AWS Console or CLI

### Azure Deployment

#### Using App Service

1. Install the Azure CLI:
   ```bash
   pip install azure-cli
   ```

2. Login to Azure:
   ```bash
   az login
   ```

3. Create a resource group:
   ```bash
   az group create --name ai-legacy-modernization --location eastus
   ```

4. Create an App Service plan:
   ```bash
   az appservice plan create --name ai-legacy-modernization-plan --resource-group ai-legacy-modernization --sku B1 --is-linux
   ```

5. Create a web app:
   ```bash
   az webapp create --name ai-legacy-modernization --resource-group ai-legacy-modernization --plan ai-legacy-modernization-plan --runtime "PYTHON|3.10"
   ```

6. Deploy the application:
   ```bash
   az webapp up --name ai-legacy-modernization --resource-group ai-legacy-modernization
   ```

### Google Cloud Deployment

#### Using App Engine

1. Install the Google Cloud SDK:
   ```bash
   # Follow instructions at https://cloud.google.com/sdk/docs/install
   ```

2. Login to Google Cloud:
   ```bash
   gcloud auth login
   ```

3. Create an app.yaml file:
   ```yaml
   runtime: python310
   entrypoint: python app.py

   env_variables:
     OPENWEATHER_API_KEY: "your_key"
     NEWS_API_KEY: "your_key"
   ```

4. Deploy the application:
   ```bash
   gcloud app deploy
   ```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl
- Helm (optional)

### Steps

1. Create a Kubernetes deployment file (deployment.yaml):
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: ai-legacy-modernization
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: ai-legacy-modernization
     template:
       metadata:
         labels:
           app: ai-legacy-modernization
       spec:
         containers:
         - name: ai-legacy-modernization
           image: your-registry/ai-legacy-modernization:latest
           ports:
           - containerPort: 5000
           env:
           - name: OPENWEATHER_API_KEY
             valueFrom:
               secretKeyRef:
                 name: api-keys
                 key: openweather
           - name: NEWS_API_KEY
             valueFrom:
               secretKeyRef:
                 name: api-keys
                 key: news
   ```

2. Create a service file (service.yaml):
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: ai-legacy-modernization
   spec:
     selector:
       app: ai-legacy-modernization
     ports:
     - port: 80
       targetPort: 5000
     type: LoadBalancer
   ```

3. Create a secret for API keys:
   ```bash
   kubectl create secret generic api-keys \
     --from-literal=openweather=your_openweather_key \
     --from-literal=news=your_news_key
   ```

4. Apply the configuration:
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   ```

## Environment Variables

The application uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port to run the application on | 5000 |
| `OPENWEATHER_API_KEY` | API key for OpenWeather API | demo_key |
| `NEWS_API_KEY` | API key for News API | demo_key |
| `OPENAI_API_KEY` | API key for OpenAI API | None |
| `DEBUG` | Enable debug mode | False |
| `LOG_LEVEL` | Logging level | INFO |

## Security Considerations

### API Keys

- Store API keys in environment variables, not in code
- Use secrets management for production deployments
- Rotate keys regularly

### Authentication

- Implement user authentication for production deployments
- Use OAuth 2.0 or similar for secure authentication
- Implement role-based access control

### Data Protection

- Encrypt sensitive data at rest and in transit
- Implement proper input validation
- Use HTTPS for all communications

### Container Security

- Use minimal base images
- Scan images for vulnerabilities
- Run containers as non-root users

## Monitoring and Logging

### Logging

- Use structured logging
- Configure log levels appropriately
- Consider using a centralized logging solution (ELK, Graylog, etc.)

### Monitoring

- Implement health checks
- Monitor system metrics (CPU, memory, etc.)
- Set up alerts for critical issues

### Tracing

- Implement distributed tracing
- Track request flows across components
- Measure performance metrics

## Scaling Strategies

### Horizontal Scaling

- Deploy multiple instances behind a load balancer
- Use auto-scaling based on metrics
- Implement stateless design for easy scaling

### Vertical Scaling

- Increase resources (CPU, memory) for instances
- Optimize code for better performance
- Use caching to reduce load

### Component Scaling

- Scale components independently based on demand
- Use message queues for asynchronous processing
- Implement circuit breakers for resilience

## Backup and Recovery

### Data Backup

- Regularly backup configuration and data
- Store backups in multiple locations
- Test restoration procedures

### Disaster Recovery

- Create a disaster recovery plan
- Implement automated recovery procedures
- Conduct regular recovery drills

### High Availability

- Deploy across multiple availability zones
- Implement redundancy for critical components
- Use health checks and automatic failover

## Troubleshooting

### Common Issues

- **Application won't start**: Check environment variables and dependencies
- **API calls failing**: Verify API keys and connectivity
- **High resource usage**: Check for memory leaks or inefficient code
- **Slow performance**: Monitor database queries and API response times

### Debugging

- Check application logs
- Use the built-in test suite to verify functionality
- Monitor system metrics for anomalies

### Getting Help

- Consult the documentation
- Check the issue tracker for known issues
- Contact support for assistance

---

This deployment guide provides instructions for deploying the AI Legacy Application Modernization system in various environments. For more detailed information about the system itself, please refer to the main documentation.
