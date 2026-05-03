# 04 · Full-Stack React + Node.js on EKS

## Architecture

```
┌─────────────────────────────────────────────┐
│         LoadBalancer (NLB)                  │
└────────────────┬────────────────────────────┘
                 │ port 80
        ┌────────▼────────┐
        │    Frontend     │ (React + NGINX)
        │  2 replicas     │
        └────────┬────────┘
                 │ proxy /api → backend-svc:3001
        ┌────────▼────────┐
        │    Backend      │ (Node.js Express)
        │  2 replicas     │
        └─────────────────┘
```

## Step 1 — Provision Infrastructure

```bash
cd terraform/
terraform init && terraform apply
```

Note the outputs:
- `cluster_name` = fullstack-cluster
- `frontend_ecr_url`
- `backend_ecr_url`

## Step 2 — Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name fullstack-cluster
kubectl get nodes
```

## Step 3 — Build & push images

```bash
ECR_FE=$(terraform -chdir=terraform output -raw frontend_ecr_url)
ECR_BE=$(terraform -chdir=terraform output -raw backend_ecr_url)

aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin $ECR_FE

# Frontend
docker build --build-arg REACT_APP_API_URL=/api -t $ECR_FE:1 frontend/
docker push $ECR_FE:1

# Backend
docker build -t $ECR_BE:1 backend/
docker push $ECR_BE:1
```

## Step 4 — Deploy with Helm

```bash
kubectl create namespace production

helm upgrade --install fullstack ./helm/fullstack \
  --namespace production \
  --set frontend.image.repository=$ECR_FE \
  --set frontend.image.tag=1 \
  --set backend.image.repository=$ECR_BE \
  --set backend.image.tag=1 \
  --wait
```

## Verify

```bash
kubectl get pods -n production
kubectl get svc frontend-svc -n production

# Get load balancer DNS
LB=$(kubectl get svc frontend-svc -n production \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Frontend: http://${LB}"
```

## Rollback

```bash
helm rollback fullstack -n production
# or
helm history fullstack -n production
helm rollback fullstack <REVISION> -n production
```

## Destroy

```bash
helm uninstall fullstack -n production
kubectl delete namespace production
cd terraform/ && terraform destroy
```