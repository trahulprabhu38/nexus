# Jenkins Setup Guide for Nexus Platform

This guide will help you set up Jenkins to build Docker images for all Nexus services.

## Prerequisites

- Jenkins server (v2.400+)
- Docker installed on Jenkins server
- kubectl access to your Kubernetes cluster
- Docker Hub account

## 1. Jenkins Installation

### Option A: Using Docker

```bash
# Create Jenkins volume
docker volume create jenkins_home

# Run Jenkins container
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

### Option B: Using Kubernetes

```bash
# Apply Jenkins deployment
kubectl apply -f https://raw.githubusercontent.com/jenkins-ci/kubernetes-operator/master/deploy/all-in-one-v1alpha2.yaml
```

## 2. Initial Jenkins Setup

1. Get the initial admin password:
```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

2. Access Jenkins at `http://localhost:8080`

3. Install suggested plugins

4. Create admin user

## 3. Required Jenkins Plugins

Install these plugins via: **Manage Jenkins** → **Plugins** → **Available plugins**

1. **Docker Pipeline** - For Docker build/push commands
2. **Kubernetes CLI** - For kubectl commands
3. **Pipeline** - For Jenkinsfile support
4. **Git** - For source code checkout
5. **Credentials Binding** - For managing secrets
6. **Blue Ocean** (Optional) - For better UI

## 4. Configure Jenkins Credentials

### 4.1 Docker Hub Credentials

1. Go to: **Manage Jenkins** → **Credentials** → **System** → **Global credentials**
2. Click **Add Credentials**
3. Configure:
   - **Kind**: Username with password
   - **Username**: `trahulprabhu38` (or your Docker Hub username)
   - **Password**: Your Docker Hub password or access token
   - **ID**: `dockerhub-credentials`
   - **Description**: Docker Hub credentials

### 4.2 Kubernetes Config (if deploying to K8s)

1. Get your kubeconfig:
```bash
cat ~/.kube/config
```

2. In Jenkins:
   - **Kind**: Secret file
   - **File**: Upload your kubeconfig
   - **ID**: `kubeconfig`
   - **Description**: Kubernetes config

Or use kubectl directly if Jenkins is running in the same cluster.

## 5. Configure Jenkins Pipeline

### 5.1 Create New Pipeline Job

1. Click **New Item**
2. Enter name: `Nexus-Build-Pipeline`
3. Select **Pipeline**
4. Click **OK**

### 5.2 Configure Pipeline

1. **General**:
   - ✅ This project is parameterized
   - Add the boolean parameters (they're defined in the Jenkinsfile)

2. **Pipeline**:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your Git repository URL
   - **Credentials**: Add if private repo
   - **Branch**: `*/main`
   - **Script Path**: `Jenkinsfile`

3. Click **Save**

### 5.3 Configure Webhook (Optional)

For automatic builds on git push:

1. In your Git repository settings:
   - Add webhook: `http://your-jenkins-url:8080/github-webhook/`
   - Content type: `application/json`
   - Events: Push events

2. In Jenkins job:
   - ✅ GitHub hook trigger for GITScm polling

## 6. Jenkins Server Configuration

### 6.1 Install Docker on Jenkins Agent

If Jenkins can't access Docker:

```bash
# Enter Jenkins container
docker exec -it -u root jenkins bash

# Install Docker CLI
apt-get update
apt-get install -y docker.io

# Add jenkins user to docker group
usermod -aG docker jenkins

# Restart Jenkins
exit
docker restart jenkins
```

### 6.2 Install kubectl on Jenkins

```bash
# Enter Jenkins container
docker exec -it -u root jenkins bash

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

## 7. Running the Pipeline

### 7.1 First Build

1. Go to your pipeline job
2. Click **Build with Parameters**
3. Select which services to build:
   - ✅ BUILD_SQL_QUERY_GEN
   - ✅ BUILD_INTENT_AGENT
   - ✅ BUILD_SQL_VALIDATOR
   - ✅ BUILD_COLUMN_PRUNING
   - ✅ BUILD_FRONTEND
   - ✅ PUSH_TO_REGISTRY
   - ☐ DEPLOY_TO_K8S (enable if you want to deploy)
4. Select **TAG_VERSION**: `latest` or `v1`
5. Click **Build**

### 7.2 Monitor Build

1. Click on the build number
2. Click **Console Output** to see live logs
3. Or use **Blue Ocean** for visual pipeline view

## 8. Pipeline Stages Explained

### Stage 1: Checkout
- Pulls code from Git repository
- Shows current commit hash

### Stage 2: Environment Setup
- Configures Docker image tags
- Sets build metadata

### Stage 3: Build Docker Images (Parallel)
- Builds all selected service images in parallel
- Tags with version and build number
- Each service builds independently

### Stage 4: Run Tests (Parallel)
- Runs unit tests for services
- Performs security scans
- Can be extended with integration tests

### Stage 5: Push to Registry
- Authenticates with Docker Hub
- Pushes all images in parallel
- Tags both with version and build number

### Stage 6: Deploy to Kubernetes (Optional)
- Updates K8s deployments with new images
- Waits for rollout to complete
- Can be extended with blue-green or canary deployments

### Stage 7: Verify Deployment (Optional)
- Checks deployment status
- Verifies pods are running
- Shows service endpoints

## 9. Customizing the Pipeline

### 9.1 Change Docker Registry

Edit `Jenkinsfile`:

```groovy
environment {
    DOCKER_REGISTRY = 'your-registry.com'
    DOCKER_USERNAME = 'your-username'
}
```

### 9.2 Add Slack Notifications

Install **Slack Notification Plugin**, then add to `post` section:

```groovy
post {
    success {
        slackSend(
            color: 'good',
            message: "Build ${env.BUILD_NUMBER} succeeded"
        )
    }
    failure {
        slackSend(
            color: 'danger',
            message: "Build ${env.BUILD_NUMBER} failed"
        )
    }
}
```

### 9.3 Add Email Notifications

Add to `post` section:

```groovy
post {
    always {
        emailext(
            subject: "Build ${env.BUILD_NUMBER} - ${currentBuild.result}",
            body: "Check console output at ${env.BUILD_URL}",
            to: 'your-email@example.com'
        )
    }
}
```

## 10. Multi-Branch Pipeline (Advanced)

For feature branch support:

1. Create **New Item** → **Multibranch Pipeline**
2. Configure:
   - **Branch Sources**: Git
   - **Repository URL**: Your repo
   - **Discover branches**: All branches
   - **Script Path**: `Jenkinsfile`

This will automatically create pipelines for each branch.

## 11. Troubleshooting

### Docker permission denied

```bash
docker exec -it -u root jenkins bash
usermod -aG docker jenkins
exit
docker restart jenkins
```

### kubectl not found

```bash
docker exec -it -u root jenkins bash
curl -LO "https://dl.k8s.io/release/stable.txt"
curl -LO "https://dl.k8s.io/release/$(cat stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
mv kubectl /usr/local/bin/
```

### Build fails with "docker login"

Check that credentials ID matches:
- In Jenkinsfile: `DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'`
- In Jenkins credentials: ID must be `dockerhub-credentials`

### Kubernetes deployment fails

1. Check if kubectl is configured:
```bash
kubectl get nodes
```

2. Check if deployments exist:
```bash
kubectl get deployments -n default
```

3. Verify service names in Jenkinsfile match your K8s deployment names

## 12. Best Practices

1. **Use build tags**: Always tag with build number for traceability
2. **Parallel builds**: Leverage parallel stages for faster builds
3. **Clean workspace**: Use `cleanWs()` in post actions
4. **Resource limits**: Set memory limits for Docker builds
5. **Secrets management**: Never hardcode credentials
6. **Build caching**: Use Docker layer caching for faster builds
7. **Test before deploy**: Always run tests before deploying

## 13. Performance Optimization

### 13.1 Docker Layer Caching

Add to Dockerfile:

```dockerfile
# Cache dependencies separately
COPY requirements.txt .
RUN pip install -r requirements.txt

# Then copy code
COPY . .
```

### 13.2 Parallel Builds

The Jenkinsfile already uses parallel builds. To optimize further:

```groovy
parallel(
    'Build 1': {
        // ...
    },
    'Build 2': {
        // ...
    },
    failFast: true  // Stop all if one fails
)
```

### 13.3 Jenkins Agent Labels

For distributed builds, use agent labels:

```groovy
agent {
    label 'docker && linux'
}
```

## 14. Security Considerations

1. **Scan images**: Use Trivy or Clair for vulnerability scanning
2. **Sign images**: Use Docker Content Trust
3. **Limit permissions**: Use service accounts with minimal permissions
4. **Rotate secrets**: Regularly rotate Docker Hub tokens
5. **Network isolation**: Use private networks for builds

## 15. Monitoring Jenkins

### 15.1 Prometheus Metrics

Install **Prometheus Plugin** in Jenkins:

1. Go to **Manage Jenkins** → **Plugins**
2. Install **Prometheus metrics plugin**
3. Access metrics at: `http://jenkins:8080/prometheus`

### 15.2 Add to Prometheus Config

```yaml
scrape_configs:
  - job_name: 'jenkins'
    static_configs:
      - targets: ['jenkins:8080']
    metrics_path: /prometheus
```

## 16. CI/CD Flow Diagram

```
Git Push → Webhook → Jenkins
                ↓
         Checkout Code
                ↓
    Build All Services (Parallel)
         ↙   ↓   ↘
    SQL   Intent  Validator  ...
         ↘   ↓   ↙
         Run Tests (Parallel)
                ↓
    Push to Docker Hub (Parallel)
                ↓
    Deploy to Kubernetes (Optional)
                ↓
         Verify Deployment
                ↓
    Send Notifications
```

## 17. Next Steps

1. Set up staging and production environments
2. Implement blue-green deployments
3. Add integration tests
4. Set up automatic rollbacks on failure
5. Implement canary deployments
6. Add performance testing
7. Set up log aggregation

## Support Resources

- Jenkins Documentation: https://www.jenkins.io/doc/
- Docker Documentation: https://docs.docker.com/
- Kubernetes Documentation: https://kubernetes.io/docs/
- Pipeline Syntax: https://www.jenkins.io/doc/book/pipeline/syntax/
