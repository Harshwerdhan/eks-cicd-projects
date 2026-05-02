# eks-cicd-projects

A monorepo of five production-ready DevOps project templates for deploying
containerized applications to AWS EKS using Terraform, Jenkins, Docker, and
Kubernetes.

## What's inside

| # | Project | Stack |
|---|---------|-------|
| 01 | Flask app CI/CD on EKS | Python · Flask · ECR · Jenkins · K8s |
| 02 | Blue-Green deployment | Node.js · Helm · Jenkins · EKS |
| 03 | Multi-environment pipeline | Microservices · Kustomize · Terraform workspaces |
| 04 | Full-stack React + Node | React · Express · Helm · Parallel CI |
| 05 | HA auto-scaling | HPA · Cluster Autoscaler · PDB · Spot nodes |

## Common tools across all projects
- **Terraform** — VPC, EKS, ECR, IAM provisioning
- **Jenkins** — build, test, push, deploy pipelines
- **Docker** — multi-stage, non-root, minimal images
- **Kubernetes** — deployments, services, probes, RBAC

## Getting started
Each project folder is self-contained with its own `README.md`,
Terraform config, Jenkinsfile, and Kubernetes manifests.
Clone the repo and navigate to the scenario you need.
