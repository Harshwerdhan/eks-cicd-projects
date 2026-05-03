# 05 · High Availability with HPA & Cluster Autoscaler

## Architecture

```
┌────────────────────────────────────────────────────┐
│  HPA watches CPU/Memory → scales Pods (3 to 20)    │
└────────────────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │   Pod Anti-Affinity             │
        │   Spread across nodes for HA    │
        └────────────────┬────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│  Cluster Autoscaler watches node utilization       │
│  Adds nodes (On-Demand + Spot) when needed         │
│  Removes underutilized nodes (10m scale-down delay)│
└────────────────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │   2x General (t3.medium)        │
        │   +1x Spot (t3.large)           │
        │   Min: 2, Max: 10 nodes         │
        └────────────────────────────────┘
```

## Step 1 — Provision Infrastructure

```bash
cd terraform/
terraform init && terraform apply
```

Note the output:
- `cluster_autoscaler_role_arn` — use this for IRSA

## Step 2 — Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name ha-cluster
kubectl get nodes
```

## Step 3 — Deploy Cluster Autoscaler

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CA_ROLE_ARN=$(terraform -chdir=terraform output -raw cluster_autoscaler_role_arn)

sed -i "s|ACCOUNT_ID|$ACCOUNT_ID|g" k8s/cluster-autoscaler.yaml
sed -i "s|role-arn|$CA_ROLE_ARN|g" k8s/cluster-autoscaler.yaml

kubectl apply -f k8s/cluster-autoscaler.yaml
kubectl logs -f deployment/cluster-autoscaler -n kube-system
```

## Step 4 — Deploy App

```bash
ECR=$(terraform -chdir=terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin $ECR

docker build -t $ECR:1 app/
docker push $ECR:1

sed -i "s|IMAGE_PLACEHOLDER|$ECR:1|g" k8s/deployment.yaml

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

## Step 5 — Verify Setup

```bash
# HPA status
kubectl get hpa -n production
kubectl describe hpa ha-app-hpa -n production

# PDB status
kubectl get pdb -n production

# Pod distribution
kubectl get pods -n production -o wide

# Node count
kubectl get nodes
```

## Load Testing

```bash
# Generate load to trigger HPA
LB=$(kubectl get svc ha-app-svc -n production \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Run load test
curl -X POST http://$LB/work \
  -H "Content-Type: application/json" \
  -d '{"duration": 30}'

# Monitor HPA
watch -n 2 "kubectl get hpa -n production"

# Watch node scaling
watch -n 5 "kubectl get nodes"

# Cluster Autoscaler logs
kubectl logs -f deployment/cluster-autoscaler -n kube-system | grep -E "scale|node"
```

## Tuning HPA

Edit the HPA thresholds:
```bash
kubectl edit hpa ha-app-hpa -n production
# Change: averageUtilization: 70 (CPU) or 80 (Memory)
```

## Scale-down behavior

The HPA waits 10 minutes after a scale-up before scaling down, and waits 10 minutes 
for a node to be unneeded before the Cluster Autoscaler removes it. Adjust in:
- `k8s/hpa.yaml`: `scaleDown.stabilizationWindowSeconds`
- `k8s/cluster-autoscaler.yaml`: `--scale-down-delay-after-add`, `--scale-down-unneeded-time`

## PodDisruptionBudget

The PDB ensures at least 2 pods stay running during:
- Node drains
- Cluster Autoscaler node removal
- Voluntary disruptions

Edit: `kubectl edit pdb ha-app-pdb -n production`

## Rollback

```bash
kubectl rollout undo deployment/ha-app -n production
```

## Destroy

```bash
helm uninstall ha-app -n production 2>/dev/null || kubectl delete -f k8s/
kubectl delete namespace production
cd terraform/ && terraform destroy
```