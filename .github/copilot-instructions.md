# Lokole Project - AI Coding Agent Instructions

## Project Overview

Lokole is an offline-first email system for low-bandwidth regions. It consists of two main components:
- **Email Client** (`opwen_email_client/`): Flask web app running on Raspberry Pi devices, syncs emails daily via compressed Azure blob storage
- **Email Server** (`opwen_email_server/`): Connexion API server on Azure, handles internet email delivery via SendGrid and manages client mailboxes

Key architecture: Client devices batch emails locally (SQLite), compress them (gzip/jsonl), upload to Azure Blobs once daily. Server processes via Celery task queues, delivers via SendGrid, and prepares downloads for clients.

## Development Workflow

### Build & Test
```bash
# Run full CI suite (linting, type checking, tests)
make ci

# Build all containers
make build

# Start services locally (uses Azurite for storage emulation)
make start logs

# Run integration tests (seeds system with test data)
make integration-tests test-emails

# Inspect system state (storage, queues, DB)
make start-devtools  # Access at localhost:10001 (storage), :8882 (DB), :5555 (queues)

# Stop everything
make stop
```

### Service Endpoints
- Email client webapp: http://localhost:5000
- Email server API: http://localhost:8080
- Status page (React): http://localhost:3000
- OpenAPI UI: Add `/ui` to any API endpoint (e.g., `/api/email/upload/<client_id>/ui`)

## Critical Architecture Patterns

### Two-Package Structure
This repo contains TWO Python packages:
- `opwen_email_client`: Installable Flask webapp for Raspberry Pi devices
- `opwen_email_server`: Connexion API server for cloud deployment

Both are built from the same repo but deployed separately. The `setup.py` publishes only the client to PyPI.

### Email Sync Protocol
Emails exchange via **gzipped jsonl files** in Azure Blobs. Schema per line:
```json
{
  "sent_at": "yyyy-mm-dd HH:MM",
  "to": ["email"], "cc": ["email"], "bcc": ["email"],
  "from": "email",
  "subject": "string",
  "body": "html",
  "attachments": [{"filename": "string", "content": "base64", "cid": "string"}]
}
```

Files: `emails.jsonl`, `zattachments.jsonl`, `zzusers.jsonl` (see `AzureSync` in `opwen_email_client/domain/email/sync.py`)

### Task Queue Architecture
Server uses **Celery** with Azure Service Bus (prod) or RabbitMQ (dev). Key queues (see `opwen_email_server/config.py`):
- `register{suffix}`: New client registration
- `inbound{suffix}`: Emails from internet → clients
- `written{suffix}`: Emails from clients → internet
- `send{suffix}`: Actual email delivery

Task chain example: `written_store` → `send_and_index_email` → `send` + `index_sent_email_for_mailbox` + `index_received_email_for_mailbox`

### Dependency Injection
Client uses `opwen_email_client/webapp/ioc.py` for IoC. Key services:
- `email_store`: SQLite-backed email storage (`SqliteEmailStore`)
- `email_sync`: Azure blob sync (`AzureSync`)
- `user_store`: Flask-Login user management

Override via `AppConfig.IOC` for testing.

### Action-Based Server Architecture
Server uses action classes (see `opwen_email_server/actions.py`):
- All actions inherit from `_Action` base class
- Actions are stateless, initialized with dependencies, called with resource IDs
- Examples: `StoreInboundEmails`, `SendOutboundEmails`, `IndexReceivedEmailForMailbox`
- Connexion routes (in `swagger/*.yaml`) map directly to action functions in `integration/connexion.py`

## Configuration Management

### Environment Variables
Both components use `environs` library for config. Key patterns:
- **Client**: Config in `opwen_email_client/webapp/config.py`, reads from `OPWEN_SETTINGS` env file
- **Server**: Config in `opwen_email_server/config.py`, all vars prefixed with `LOKOLE_`
- **Resource suffix**: Use `LOKOLE_RESOURCE_SUFFIX` to namespace Azure resources for parallel deployments

Critical server vars: `LOKOLE_STORAGE_PROVIDER`, `LOKOLE_QUEUE_BROKER_SCHEME`, `LOKOLE_SENDGRID_KEY`

### Docker Compose
- Development: `docker-compose.yml` (base services)
- Extended configs: `docker/docker-compose.{test,tools,setup,prod}.yml`
- Service dependencies: nginx → api/webapp → azurite
- Build targets: `builder` (CI), `runtime` (production) controlled via `BUILD_TARGET` env var

## Testing Conventions

### Test Structure
- Tests mirror source: `tests/opwen_email_client/`, `tests/opwen_email_server/`
- Use `unittest.TestCase`, run via `nose2`
- Integration tests in `docker/integtest/` as bash scripts (see `tests.sh` for sequence)

### CI Script
`docker/app/run-ci.sh` runs:
1. `flake8` (linting)
2. `isort --check-only` (import ordering)
3. `yapf` (formatting, diff mode)
4. `bandit` (security scanning)
5. `mypy` (type checking)
6. `nose2` with coverage

**Always run `make ci` before committing**. The CI is strict on code formatting.

## GitHub Actions CI/CD Workflow

### Three Workflows Overview
The project uses three GitHub Actions workflows (`.github/workflows/`):

1. **CI (`ci.yml`)** - Runs on every pull request
2. **CI Live (`ci-live.yml`)** - Runs on labeled PRs with real Azure resources
3. **CD (`cd.yml`)** - Runs on GitHub releases

### CI Workflow (Pull Requests)
Triggers: PR opened, reopened, or synchronized

**Job: `test-unit`**
- Runs `make ci` (linting, type checking, unit tests)
- Runs `make build verify-build` (builds containers, verifies with dive)
- Uploads coverage to Codecov on success
- Uses `BUILD_TARGET=runtime` for production-like builds
- Skips SendGrid/queue broker for unit tests (empty env vars)

**Job: `test-local`**
- Runs full integration tests with local emulation
- Uses Azurite (local Azure storage) + RabbitMQ (`LOKOLE_QUEUE_BROKER_SCHEME=amqp`)
- Executes `make build start integration-tests`
- Dumps logs via `make status` on failure
- Always tears down with `make stop`

### CI Live Workflow (Azure Integration Tests)
Triggers: PR labeled with `safe to test` (manual gate for security)

**Why it exists**: Tests against real Azure resources (Service Bus, Storage) to catch integration issues that local emulation misses.

**Key differences from local CI**:
- Uses `pull_request_target` (runs in base repo context for secrets access)
- Checks out PR head SHA explicitly for security
- Decrypts secrets via `make github-env` (see "Secrets Management" below)
- Uses Azure Service Bus (`LOKOLE_QUEUE_BROKER_SCHEME=azureservicebus`)
- Real Azure Storage instead of Azurite
- Resource suffix from UUID prevents conflicts (`LOKOLE_RESOURCE_SUFFIX`)
- Longer delays (`TEST_STEP_DELAY=90`) for eventual consistency
- Cleans up Azure resources via `make clean-storage` after tests

**Security model**: Label gate prevents arbitrary code execution with production secrets.

### CD Workflow (Releases)
Triggers: GitHub release created (manual via GitHub UI or API)

**Release process**:
1. Decrypts secrets via `make github-env`
2. Extracts version from Git tag: `${GITHUB_REF##*/}` → `DOCKER_TAG`
3. Builds and tags Docker images with version + `latest`
4. Publishes to Docker Hub (`release-docker` → `deploy-docker`)
5. Publishes client package to PyPI (`release-pypi` → `deploy-pypi`)

**Artifacts produced**:
- `ascoderu/opwenserver_app:$VERSION` (Connexion API server)
- `ascoderu/opwenserver_nginx:$VERSION` (Nginx gateway)
- `ascoderu/opwenwebapp:$VERSION` (Flask client)
- `ascoderu/opwenstatuspage:$VERSION` (React status page)
- PyPI package: `opwen_email_client==$VERSION`

**Manual deployment steps after release**:
```bash
# For Kubernetes (recommended)
make deploy-k8s \
  -e DOCKER_TAG="$VERSION" \
  -e HELM_NAME="lokole" \
  -e LOKOLE_DNS_NAME="lokole.example.com"

# For VM deployment
make deploy \
  -e DOCKER_TAG="$VERSION" \
  -e LOKOLE_DNS_NAME="lokole.example.com"
```

### Secrets Management & Encryption/Decryption

**How secrets are stored and decrypted** (used in `ci-live.yml` and `cd.yml`):

The repository contains `.github.env.gpg` - a GPG-encrypted file with production credentials. Both CI Live and CD workflows decrypt this via `make github-env`:

**Encryption process** (done once, manually):
```bash
# Create .github.env with secrets (not committed)
cat > .github.env << EOF
export AZURE_SUBSCRIPTION_ID=...
export AZURE_SP_APPID=...
export AZURE_SP_PASSWORD=...
export TEST_AZURE_STORAGE_ACCOUNT=...
export TEST_AZURE_STORAGE_KEY=...
export SENDGRID_KEY=...
export CLOUDFLARE_USER=...
export CLOUDFLARE_KEY=...
export GITHUB_AUTH_TOKEN=...
export DOCKER_USERNAME=...
export DOCKER_PASSWORD=...
export PYPI_USERNAME=...
export PYPI_PASSWORD=...
EOF

# Encrypt with passphrase
gpg --symmetric --cipher-algo AES256 --batch --passphrase "$GPG_PASSPHRASE" .github.env

# Commit .github.env.gpg (encrypted), never commit .github.env
git add .github.env.gpg
```

**Decryption process** (automatic in workflows):
The `make github-env` target (see `makefile`) performs three steps:
1. **Decrypt**: `gpg --decrypt --batch --passphrase "$GPG_PASSPHRASE" .github.env.gpg > .github.env`
2. **Generate UUID**: Creates unique `SUFFIX` for resource isolation and appends to `$GITHUB_ENV`
3. **Export vars**: Strips `export ` prefix from `.github.env` and appends all to `$GITHUB_ENV`

This makes all secrets available as environment variables to subsequent workflow steps.

**Security model**:
- `GPG_PASSPHRASE` stored in GitHub Secrets (Settings → Secrets)
- Only workflows with secrets access can decrypt (ci-live uses `pull_request_target`)
- Label gate (`safe to test`) prevents untrusted PR code from accessing secrets
- `.github.env` never committed, only encrypted `.github.env.gpg`

### Local CI Reproduction
To reproduce CI failures locally:
```bash
# Unit tests (fast)
make -e BUILD_TARGET=runtime ci build verify-build

# Integration tests with local emulation
make -e BUILD_TARGET=runtime \
     -e LOKOLE_QUEUE_BROKER_SCHEME=amqp \
     build start integration-tests

# Full cleanup
make stop
```

### Common CI Failure Patterns
- **Formatting errors**: Run `yapf --in-place --recursive opwen_email_server opwen_email_client tests`
- **Import order**: Run `isort opwen_email_server opwen_email_client`
- **Integration test timeout**: Check container logs with `make status`
- **Docker image too large**: `verify-build` uses dive with efficiency rules in `.dive-ci`

## Frontend Assets

### JavaScript Build
- Package manager: `yarn` (NOT npm)
- Grunt builds static assets: `yarn build` or `grunt` (see `Gruntfile.js`)
- Bower dependencies in `package.json` as `@bower_components/*`
- Client JS in `opwen_email_client/webapp/static/js/`
- Lint with: `yarn lint` (uses `standard`)

### Python-Generated Assets
Client generates wvdial configs for USB modems: see `opwen_email_client/webapp/mkwvconf.py` (uses mobile-network-codes data)

## Production Deployment

### Physical Client Setup
`install.py` script installs client on Raspberry Pi/Orange Pi with:
- Nginx + Gunicorn for Flask app
- Modem setup (Huawei E303s-65, E3131, MS2131i-8)
- WvDial for scheduled sync via cellular
- Celery cron for background tasks

Tested on Raspbian Jessie and Armbian Ubuntu Xenial.

### Azure Infrastructure
Setup script (`docker/setup/setup.sh`) provisions:
- 4 Storage Accounts (queues, tables, blobs, client exchange)
- Application Insights for monitoring
- Azure Kubernetes Service OR VM (controlled via `DEPLOY_COMPUTE` env var)
- SendGrid + Cloudflare integration for MX records

Deploy via: `make deploy-k8s` (uses Helm charts in `helm/opwen_cloudserver/`)

## Code Style Specifics

### Type Hints
Server and client use type hints. `mypy` runs in CI, but not all code is fully typed yet. Add hints to new code.

### Security
- Passwords hashed with bcrypt (see `SECURITY_PASSWORD_HASH` in client config)
- Client authentication via `LOKOLE_REGISTRATION_USERNAME/PASSWORD` (basic auth)
- GitHub org team permissions for admin ops (`LOKOLE_REGISTRATION_GITHUB_ORGANIZATION`)

### Error Handling
Actions log via `LogMixin`, return Flask `Response` objects. All Celery tasks use `ignore_result=True` for performance.

## Internationalization

Client supports multiple locales via Flask-BabelEx. To add a language:
```bash
export language=ln  # ISO 639-1 code
pybabel init -i babel.pot -d opwen_email_client/webapp/translations -l "${language}"
# Edit with poedit
pybabel compile -d opwen_email_client/webapp/translations
```

Translations in `opwen_email_client/webapp/translations/`, extracted strings in `babel.pot`.

## Key Files Reference

- `makefile`: All dev/deploy commands
- `docker-compose.yml`: Service definitions
- `opwen_email_client/webapp/config.py`: Client config & Flask setup
- `opwen_email_server/config.py`: Server config & Azure resource naming
- `opwen_email_server/actions.py`: Core server logic
- `opwen_email_client/domain/email/store.py`: Email storage abstraction
- `opwen_email_client/domain/email/sync.py`: Blob sync implementation
- `swagger/*.yaml`: API specifications (OpenAPI 2.0)
## Python Version Upgrade Guide (3.9 → 3.12 Client)

**Completed: February 2026** - Upgraded client to Python 3.12 while maintaining server at Python 3.9.

### Upgrade Summary

**Goal**: Upgrade client (`opwen_email_client`) to Python ≥3.12 for modern Raspbian compatibility while keeping server (`opwen_email_server`) at Python 3.9 to minimize production risk.

**Result**: Successfully achieved mixed Python environment:
- Client (webapp, client containers): Python 3.12.12
- Server (api, worker containers): Python 3.9.25

### Critical Dependency Changes

#### Client Dependencies (requirements-webapp.txt)
```
bcrypt==3.2.2 → 4.0.1           # Python 3.12 compatibility
Pillow==9.2.0 → 10.0.0          # Python 3.12 wheels
SQLAlchemy==1.4.39 → 1.4.53     # Required by Celery 5.3.6[sqlalchemy]
celery[sqlalchemy]==5.2.7 → 5.3.6  # Python 3.12 support
environs==9.5.0 → 11.0.0        # Fixes marshmallow.__version_info__ AttributeError
mkwvconf==0.1.1 → git+https://github.com/ascoderu/mkwvconf.git@dev  # Fixed python_requires syntax
```

#### Server Dependencies (requirements.txt)
```
Pillow==9.2.0 → 10.0.0          # Match client version
environs==9.5.0 → 11.0.0        # Required for shared dependencies
celery==5.2.7 → 5.3.6           # Match client version
kombu==5.2.4 → 5.3.7            # Required by Celery 5.3.6
referencing==0.35.1             # Pin for Python 3.9-3.12 compatibility (0.36+ needs Python 3.13)
jsonschema==4.23.0              # Pin to avoid referencing 0.36+
```

#### Dev Dependencies (requirements-dev.txt)
```
mypy==0.971 → 1.5.0             # Python 3.12 compatibility
pbr==5.11.1                     # Explicit dependency for bandit (was transitive)
```

### Code Changes for Python 3.12

#### 1. Type Hints (opwen_email_server/actions.py)
**Issue**: mypy 1.5.0 enforces no_implicit_optional=True by default.

**Fix**: Add `Optional` type hints for parameters with `None` defaults:
```python
from typing import Optional

# Before:
def __init__(self, ..., email_parser: Callable[[str], dict] = None):
    self._email_parser = email_parser or MimeEmailParser()

# After:
def __init__(self, ..., email_parser: Optional[Callable[[str], dict]] = None):
    self._email_parser = email_parser if email_parser else MimeEmailParser()
```

Changed truthy check from `or` to `if/else` to avoid mypy's truthy-function warning.

#### 2. Pillow 10 Compatibility (opwen_email_server/utils/email_parser.py)
**Issue**: `Image.ANTIALIAS` removed in Pillow 10.0.

**Fix**: Replace with `Image.Resampling.LANCZOS`:
```python
# Before:
image.thumbnail(new_size, Image.ANTIALIAS)

# After:
image.thumbnail(new_size, Image.Resampling.LANCZOS)
```

### Docker Configuration Updates

#### 1. Client Dockerfile (docker/client/Dockerfile)
- Changed `PYTHON_VERSION` ARG from `3.9` to `3.12`
- Added git installation in runtime stage (needed for mkwvconf from GitHub):
  ```dockerfile
  RUN apt-get update \
   && apt-get install -y --no-install-recommends git \
   && rm -rf /var/lib/apt/lists/*
  ```
- Reordered requirements installation: `requirements.txt` before `requirements-webapp.txt` (prevents environs downgrade)

#### 2. Server Dockerfile (docker/app/Dockerfile)
- Removed version pin from `mobile-broadband-provider-info` (version 20201225-1 no longer exists)
- Added hadolint ignore comment:
  ```dockerfile
  # hadolint ignore=DL3008
  RUN apt-get update \
   && apt-get install -y --no-install-recommends mobile-broadband-provider-info \
   && rm -rf /var/lib/apt/lists/*
  ```

#### 3. Docker Compose (docker-compose.yml)
Added Python version build args for client services:
```yaml
webapp:
  build:
    args:
      PYTHON_VERSION: "3.12"

client:
  build:
    args:
      PYTHON_VERSION: "3.12"
```

#### 4. Package Configuration (setup.py)
Added Python version constraint:
```python
python_requires='>=3.12'
```

#### 5. Environment Configuration (.env)
Changed `BUILD_TAG` to PEP 440 compliant version:
```
BUILD_TAG=0.0.0.dev0  # Was: development (invalid for setuptools 80.x)
```

### Common Issues & Solutions

#### Issue: marshmallow.__version_info__ AttributeError
**Symptom**: `AttributeError: module 'marshmallow' has no attribute '__version_info__'`
**Cause**: environs 9.5.0 incompatible with marshmallow 4.x
**Solution**: Upgrade to environs 11.0.0

#### Issue: Celery import error
**Symptom**: `ImportError: cannot import name 'Celery' from 'celery'`
**Cause**: Celery 5.2.7 not fully compatible with Python 3.12
**Solution**: Upgrade to Celery 5.3.6 + kombu 5.3.7

#### Issue: TypeVar 'default' parameter
**Symptom**: `TypeError: __init__() got an unexpected keyword argument 'default'`
**Cause**: referencing 0.36+ uses Python 3.13 TypeVar syntax, incompatible with Python 3.9
**Solution**: Pin referencing==0.35.1 and jsonschema==4.23.0

#### Issue: Invalid version 'development'
**Symptom**: `packaging.version.InvalidVersion: Invalid version: 'development'`
**Cause**: setuptools 80.x (from Python 3.12) strictly validates PEP 440 versions
**Solution**: Use `0.0.0.dev0` instead of arbitrary version strings

#### Issue: mkwvconf installation failure
**Symptom**: `ERROR: Invalid requirement: python_requires='>=2.7.*'`
**Cause**: PyPI version has invalid wildcards in python_requires
**Solution**: Install from GitHub dev branch:
```
mkwvconf @ git+https://github.com/ascoderu/mkwvconf.git@dev
```

### Testing Strategy

#### 1. Local Testing
```bash
# Create Python 3.12 venv
pyenv install 3.12.12
echo "3.12.12" > .python-version
python -m venv venv
source venv/bin/activate
pip install -r requirements-webapp.txt -r requirements.txt -r requirements-dev.txt
```

#### 2. Docker Testing
```bash
# Build and verify Python versions
docker compose build webapp api
docker compose up -d webapp api worker
docker compose exec webapp python --version  # Should show 3.12.12
docker compose exec api python --version     # Should show 3.9.25
```

#### 3. CI Testing with act
```bash
# Install act (GitHub Actions local runner)
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflows locally
./bin/act pull_request -j test-unit    # Lint, type check, unit tests
./bin/act pull_request -j test-local   # Integration tests with Azurite
```

### Known Limitations & Future Work

#### DeprecationWarnings
- `datetime.utcnow()` deprecated in Python 3.12 (use `datetime.now(timezone.utc)`)
- `cached-property` package redundant (use `functools.cached_property`)
- These are non-breaking and can be addressed in future refactoring

#### SQLAlchemy 2.0 Migration
Current: SQLAlchemy 1.4.53 (last 1.x version)
Future: Plan migration to SQLAlchemy 2.0 when refactoring ORM usage

#### ARM64 Testing
Docker builds tested on x86_64 only. Consider testing on ARM64 for Raspberry Pi hardware:
```bash
docker buildx build --platform linux/arm64 ...
```

#### Integration Test Docker Client
The integtest container Docker client compatibility issue remains. Current workaround documented in test scripts.

### Verification Checklist

After completing upgrade:
- [ ] `make ci` passes (linting, type checking, unit tests)
- [ ] `./bin/act pull_request -j test-unit` succeeds
- [ ] Docker images build for both client and server
- [ ] `docker compose exec webapp python --version` shows ≥3.12
- [ ] `docker compose exec api python --version` shows 3.9
- [ ] Services start without import errors
- [ ] Client can import opwen_email_client module
- [ ] Server can import opwen_email_server module

### Rollback Strategy

If issues arise:
1. Revert docker/client/Dockerfile PYTHON_VERSION to 3.9
2. Revert requirements-webapp.txt dependency versions
3. Revert requirements-dev.txt mypy version
4. Rebuild: `docker compose build webapp client`

### References

- Python 3.12 Release Notes: https://docs.python.org/3/whatsnew/3.12.html
- Pillow 10 Migration: https://pillow.readthedocs.io/en/stable/releasenotes/10.0.0.html
- mypy no_implicit_optional: https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-no-implicit-optional
- PEP 440 Version Specifiers: https://peps.python.org/pep-0440/