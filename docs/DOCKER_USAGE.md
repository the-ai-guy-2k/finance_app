# Docker Usage for Financial App

This document explains how to build, run, and pull the Financial App from Docker.

## Docker Hub Image

The Financial App is published to Docker Hub for SPE-01 AWS deployment:

```
taig2k/finance_app_for_aws
```

### Pull the latest image from Docker Hub

```powershell
docker pull taig2k/finance_app_for_aws:latest
```

### Pull a specific version by commit SHA

```powershell
docker pull taig2k/finance_app_for_aws:<commit-sha>
```

## What Docker Adds

- Consistent local runtime environment for the Flask application
- Isolation from host Python installations
- Support for mounting configuration and secret files at runtime
- Automated publishing to Docker Hub on `main` branch merges (see CI/CD below)
- Easy portability across machines and SPE-01 EC2 bootstrap

## Build the image locally

From the repository root:

```powershell
docker build -t finance_app_for_aws:local .
```

## Run the container locally

### Run without OpenAI configured

This starts the app with no mounted config or API key. It is useful to confirm the container runs and responds on port 5000.

```powershell
docker run --rm -p 5000:5000 finance_app_for_aws:local
```

### Run with mounted config and API key

Mount a local Docker-friendly config file and the OpenAI key file into the container.

```powershell
docker run --rm -p 5000:5000 `
  -v "%cd%\config.docker.json:/app/config.json" `
  -v "C:\Users\tim\Desktop\openai_key_for_financial_app.txt:/run/secrets/openai_key.txt" `
  finance_app_for_aws:local
```

Then open:

```
http://127.0.0.1:5000
```

## Docker Hub Image Tags

- **`latest`**: Most recent image published from `deployable`
- **Commit SHA**: Immutable tag per published commit (`taig2k/finance_app_for_aws:<commit-sha>`)

Example:

```powershell
docker run -p 5000:5000 taig2k/finance_app_for_aws:latest
```

## CI/CD Publishing Behavior

Two GitHub Actions workflows share responsibility:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Push, pull request | Syntax check, imports, pytest, local Docker build (no push) |
| [`.github/workflows/docker-publish.yml`](../.github/workflows/docker-publish.yml) | Push to `deployable`, manual dispatch | Test, build, push to Docker Hub |

- **Feature branches / PRs**: CI validates code and Docker build only — no Docker Hub push
- **`main` branch**: `docker-publish.yml` runs tests, builds, and pushes `latest` + commit SHA tags

**Release branch:** `deployable` — feature branches run CI only; merges to `deployable` trigger Docker Hub publish.

## Config file and secret handling

- Do not bake `config.json` or any API key file into the Docker image
- Mount `config.docker.json` to `/app/config.json` inside the container
- **Preferred:** set `OPENAI_API_KEY` at runtime (Docker `-e`, AWS user-data/Terraform)
- **Fallback:** mount the key file to `/run/secrets/openai_key.txt` and point `openai.api_key_file` in mounted config to that path
- Other supported env vars: `CONFIG_FILE`, `OPENAI_API_KEY_FILE`

### Example `config.docker.json`

Use the provided `config.docker.example.json` as a starting point, or mount your own config with the API key path set to `/run/secrets/openai_key.txt`.

## Troubleshooting

- If the app still fails to start, check the container logs for configuration or API key errors
- If the app cannot bind, confirm the container exposes port `5000` and the host port is available
- Do not commit mounted secret file paths or API keys to source control
- Check Docker Hub repo for available images and tags: `https://hub.docker.com/r/taig2k/finance_app_for_aws`

## Why secrets are not baked into images

- Docker images are often shared across environments; embedding secrets would risk accidental exposure
- Use mounts or environment variables so credentials remain on the host and are injected only at runtime
- This keeps the image reusable and secure across all users and environments
