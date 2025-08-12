# Multi-Team Docker Compose Setup

This project demonstrates how to manage a multi-team development environment using Docker Compose, where core services are shared across teams while maintaining team-level isolation.

## Structure

- `shared-services.yml`: Defines the core infrastructure (MongoDB, Vector DB, Prometheus, Grafana) that all teams share. It also creates the `shared-net` network.
- `teamA.yml` / `teamB.yml`: Team-specific Docker Compose files. Each defines the team's own application and connects to the `shared-net`.
- `teamA/` / `teamB/`: Directories containing the source code and `Dockerfile` for each team's application.
- `.env.teamA` / `.env.teamB`: Environment files for storing team-specific credentials and configurations.
- `.github/workflows/`: This directory contains the GitHub Actions workflows for automated deployment.
  - `teamA-deploy.yml`: Deploys Team A's application when changes are pushed to the `teamA/` directory.
  - `teamB-deploy.yml`: Deploys Team B's application when changes are pushed to the `teamB/` directory.

## How to Use

### 1. Start the Shared Services

First, bring up the shared infrastructure on your VPS. This only needs to be done once.

```bash
docker compose -f shared-services.yml up -d
```

### 2. GitHub Actions Deployment

The repository is configured with two separate GitHub Actions workflows, one for each team. This allows teams to deploy their applications independently.

- A push to the `main` branch with changes in the `teamA/` directory will trigger the **Build and Deploy Team A** workflow.
- A push to the `main` branch with changes in the `teamB/` directory will trigger the **Build and Deploy Team B** workflow.

Each workflow will:
1.  **Build** the Docker image for the respective team.
2.  **Push** the image to your Docker Hub repository.
3.  **Connect** to your VPS via SSH.
4.  **Pull** the new image and **restart** the service.

To make this work, you need to do the following:

#### A. Configure GitHub Secrets

In your GitHub repository, go to `Settings > Secrets and variables > Actions` and add the following secrets:

- `DOCKERHUB_USERNAME`: Your Docker Hub username.
- `DOCKERHUB_TOKEN`: A Docker Hub access token. You can create one at [hub.docker.com/settings/security](https://hub.docker.com/settings/security).
- `VPS_HOST`: The IP address or hostname of your VPS.
- `VPS_USERNAME`: The username for SSH access to your VPS.
- `VPS_PRIVATE_KEY`: The private SSH key that has access to your VPS.

#### B. Configure Environment on VPS

On your VPS, in the project directory (`/home/overall/vsp/multi/multi-team-dev-deployment`), create a `.env` file with your Docker Hub username:

```
DOCKERHUB_USERNAME=your_dockerhub_username
```

This will allow Docker Compose to pull the correct images from your Docker Hub repository.