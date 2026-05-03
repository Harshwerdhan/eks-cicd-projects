# 03 · Multi-Environment Pipeline for Microservices

## Environment strategy

| Workspace | Cluster | Nodes | Replicas |
|-----------|---------|-------|----------|
| dev       | microservices-dev     | t3.small  × 1 | 1 per service |
| staging   | microservices-staging | t3.medium × 2 | 2 per service |
| prod      | microservices-prod    | t3.large  × 3 | 3 per service |

## Step 1 — Provision all environments

```bash
cd terraform/

terraform init

# Create and apply each workspace
for ENV in dev staging prod; do
  terraform workspace new $ENV 2>/dev/null || terraform workspace select $ENV
  terraform apply -auto-approve
done
```

## Step 2 — Verify clusters

```bash
for ENV in dev staging prod; do
  aws eks update-kubeconfig --region us-east-1 --name microservices-$ENV
  kubectl get nodes --context arn:aws:eks:us-east-1:$(aws sts get-caller-identity --query Account --output text):cluster/microservices-$ENV
done
```

## Step 3 — Create namespaces

```bash
for ENV in dev staging prod; do
  aws eks update-kubeconfig --region us-east-1 --name microservices-$ENV
  kubectl create namespace $ENV
done
```

## Step 4 — Manual first deploy to dev

```bash
cd ..
ECR_GW=$(terraform -chdir=terraform output -json ecr_urls | jq -r '."api-gateway"')
ECR_US=$(terraform -chdir=terraform output -json ecr_urls | jq -r '."user-service"')
ECR_OS=$(terraform -chdir=terraform output -json ecr_urls | jq -r '."order-service"')

REGION=us-east-1
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_GW

docker build -t $ECR_GW:1 services/api-gateway/   && docker push $ECR_GW:1
docker build -t $ECR_US:1 services/user-service/  && docker push $ECR_US:1
docker build -t $ECR_OS:1 services/order-service/ && docker push $ECR_OS:1

sed -i "s|API_GATEWAY_IMAGE|$ECR_GW:1|g"  k8s/base/api-gateway-deployment.yaml
sed -i "s|USER_SERVICE_IMAGE|$ECR_US:1|g" k8s/base/user-service-deployment.yaml
sed -i "s|ORDER_SERVICE_IMAGE|$ECR_OS:1|g" k8s/base/order-service-deployment.yaml

aws eks update-kubeconfig --region $REGION --name microservices-dev
kubectl apply -k k8s/overlays/dev/
kubectl rollout status deployment -n dev --timeout=300s
```

## Jenkins promotion flow

```
push to develop  →  auto-deploy dev
push to main     →  auto-deploy dev → integration tests → auto-deploy staging
manual trigger   →  approval gate  → deploy prod
```

## Rollback

```bash
# Per service
kubectl rollout undo deployment/api-gateway -n prod

# All services
for svc in api-gateway user-service order-service; do
  kubectl rollout undo deployment/$svc -n prod
done
```

## Destroy

```bash
cd terraform/
for ENV in dev staging prod; do
  terraform workspace select $ENV
  terraform destroy -auto-approve
done
```