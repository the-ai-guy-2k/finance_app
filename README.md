# Financial Nebula Node — MVP

Behavior-aware financial operational intelligence.

## Quick Start

1. **Setup:**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure:**
   - Ensure `config.json` exists with your settings
   - Place your OpenAI API key file at the path specified in `config.json`
   - Default: `C:\Users\tim\Desktop\openai_key_for_financial_app.txt`

3. **Run:**
   ```powershell
   python app.py
   ```
   Then open: http://127.0.0.1:5000

## Features

- Receipt image upload (PNG, JPG, JPEG, WebP)
- Manual transaction entry
- CSV transaction upload
- Transaction normalization
- Behavioral insight generation via OpenAI
- Simple goal correlation
- Local JSON persistence

## Configuration

See `config.json` for:
- Flask secret key
- OpenAI API key file path
- OpenAI model selection
- Upload folder location
- Upload file size limits

## Logs

Application logs are written to `logs/app.log` with timestamped entries.

Error categories: CONFIG_ERROR, API_KEY_ERROR, FILE_UPLOAD_ERROR, CSV_PARSE_ERROR, OPENAI_API_ERROR, STORAGE_ERROR, VALIDATION_ERROR

## Testing

```powershell
pytest -v
```

## Docker

This project is containerized with support for local development and automated Docker Hub publishing.

### Local Development with Docker

Build the image locally:
```powershell
docker build -t finance_app_for_aws:local .
```

Run the container with a mounted config file and OpenAI key:
```powershell
docker run --rm -p 5000:5000 `
  -v "%cd%\config.docker.json:/app/config.json" `
  -v "C:\Users\tim\Desktop\openai_key_for_financial_app.txt:/run/secrets/openai_key.txt" `
  finance_app_for_aws:local
```

Then open: http://127.0.0.1:5000

### Automated Docker Hub Publishing (CI/CD)

Two workflows provide a single CI/CD story for SPE-01:

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI** | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Push, pull request | Syntax, imports, pytest, Docker build validation (no push) |
| **Docker Publish** | [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml) | Push to `deployable`, manual dispatch | Test, build, push to Docker Hub |

| Item | Value |
|------|-------|
| **Purpose** | Build and push the Financial App image for AWS SPE-01 Terraform deployment |
| **Docker Hub image** | `taig2k/finance_app_for_aws` |
| **Tags pushed** | `latest`, `<commit-sha>` |
| **Publish triggers** | Push to `deployable`, manual `workflow_dispatch` |
| **Required GitHub secrets** | `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` |

**Publish workflow behavior (`docker-publish.yml`):**

1. Validates `requirements.txt` exists
2. Runs existing pytest suite
3. Builds the Docker image with Buildx
4. Pushes `taig2k/finance_app_for_aws:latest` and `taig2k/finance_app_for_aws:<commit-sha>` to Docker Hub

**SPE-01 relationship:** Terraform artifact [`terraform/spe-01/`](terraform/spe-01/) pulls `taig2k/finance_app_for_aws:latest` onto EC2 at bootstrap. Publish to Docker Hub from `deployable` before running SPE-01 `terraform apply`.

**Release branch:** `deployable` is the protected branch for tested, publishable work. Feature branches merge to `deployable` after CI passes.

Credentials are stored only as GitHub Actions secrets — never hardcoded in workflows or the repository.

See [DOCKER_USAGE.md](docs/DOCKER_USAGE.md) for local Docker usage and troubleshooting.

## Docs

- [PCAP.md](docs/PCAP.md) - Project architecture
- [LOCAL_TESTING.md](docs/LOCAL_TESTING.md) - Testing workflows
- [GOVERNANCE.md](docs/GOVERNANCE.md) - Branch governance

## Tech Stack

- Python 3.12+
- Flask
- OpenAI API
- Local JSON storage
