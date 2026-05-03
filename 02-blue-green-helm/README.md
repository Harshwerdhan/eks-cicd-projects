# 02 · Blue-Green Deployment on EKS with Helm

## How it works

```
                    ┌─────────────────────────────┐
Traffic ──────────► │  nodeapp-active (Service)   │
                    │  selector: slot=blue (live) │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐     ┌─────────────────────┐
                    │  nodeapp-blue  (Deployment) │     │ nodeapp-green (stby)│
                    │  3 replicas — LIVE          │     │ 1 replica — WARM    │
                    └─────────────────────────────┘     └─────────────────────┘
```

Traffic switch = patch `activeSlot` in the shared Service selector. Zero downtime.

## Step 1 — Provision

```bash
cd terraform/
terraform init && terraform apply
```

## Step 2 — Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name blue-green-cluster
kubectl create namespace production
```

## Step 3 — First deploy (blue)

```bash
ECR=$(terraform -chdir=terraform output -raw ecr_repository_url)

cd app/ && docker build -t $ECR:1 . && docker push $ECR:1 && cd ..

helm upgrade --install nodeapp-blue ./charts/nodeapp \
  --namespace production \
  --set slot=blue \
  --set activeSlot=blue \
  --set image.repository=$ECR \
  --set image.tag=1 \
  --wait
```

## Rollback strategies

### Instant (< 30 seconds) — switch selector back

```bash
helm upgrade nodeapp-green ./charts/nodeapp \
  --namespace production \
  --reuse-values \
  --set activeSlot=blue
```

### Helm history rollback

```bash
helm history nodeapp-green -n production
helm rollback nodeapp-green <REVISION> -n production
```

### Automated post-deploy health check

```bash
LB=$(kubectl get svc nodeapp-active -n production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
for i in $(seq 1 10); do
  curl -sf http://$LB/health && sleep 10 || \
    (helm upgrade nodeapp-green ./charts/nodeapp --reuse-values --set activeSlot=blue -n production && exit 1)
done
```

## Destroy

```bash
helm uninstall nodeapp-blue nodeapp-green -n production
cd terraform/ && terraform destroy
```