# 01 · Flask App CI/CD on EKS

## Architecture

```
GitHub → Jenkins → ECR → EKS (production namespace)
                          └─ flask-app Deployment (3 replicas)
                          └─ flask-app-svc (LoadBalancer → NLB)
```

## Prerequisites

- AWS CLI configured
- Terraform >= 1.7
- kubectl, Docker installed on Jenkins agent

## Step 1 — Provision Infrastructure

```bash
cd terraform/
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Note the outputs:
```
cluster_name        = "flask-eks-cluster"
ecr_repository_url  = "123456789.dkr.ecr.us-east-1.amazonaws.com/flask-eks-flask-app"
configure_kubectl   = "aws eks update-kubeconfig ..."
```

## Step 2 — Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name flask-eks-cluster
kubectl get nodes
```

## Step 3 — Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

## Step 4 — Manual first deploy (optional, Jenkins handles subsequent)

```bash
ECR_URL=$(terraform -chdir=terraform output -raw ecr_repository_url)

# Build & push
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin $ECR_URL

cd app/
docker build -t $ECR_URL:1 .
docker push $ECR_URL:1

# Deploy
cd ../
sed -i "s|IMAGE_PLACEHOLDER|$ECR_URL:1|g" k8s/deployment.yaml
kubectl apply -f k8s/
kubectl rollout status deployment/flask-app -n production
```

## Step 5 — Configure Jenkins

1. Install plugins: Pipeline, Docker Pipeline, AWS Steps, Kubernetes CLI
2. Add credentials:
   - ID `ecr-registry-url` → type: Secret text → value: your ECR registry URL
   - AWS credentials with ECR + EKS access
3. Create Pipeline job pointing to this repo
4. Push to trigger

## Verify Deployment

```bash
kubectl get pods -n production
kubectl get svc flask-app-svc -n production
```

## Rollback

```bash
# Immediate rollback
kubectl rollout undo deployment/flask-app -n production

# Rollback to specific revision
kubectl rollout history deployment/flask-app -n production
kubectl rollout undo deployment/flask-app -n production --to-revision=2
```

## Destroy

```bash
kubectl delete -f k8s/
cd terraform/ && terraform destroy
```