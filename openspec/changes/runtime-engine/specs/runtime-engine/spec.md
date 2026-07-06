# Runtime Engine Specification

## ADDED Requirements

### Requirement: Runtime engine as independent codebase
The nebula-runtime SHALL be a standalone, independently deployable codebase separate from nebula-platform. It SHALL NOT contain any build engine logic (dialogue, document generation, coding dispatch, build pipeline). It SHALL be deployable with a single `docker-compose up` command.

#### Scenario: Standalone deployment
- **WHEN** user runs `docker-compose up` in the nebula-runtime directory
- **THEN** the runtime API starts and is accessible at the configured port

#### Scenario: No build logic
- **WHEN** inspecting the nebula-runtime codebase
- **THEN** there SHALL be no imports or dependencies related to LangGraph agents, OpenSpec document generation, Claude Code dispatch, or project management UI

### Requirement: Artifact loading and application startup
The nebula-runtime SHALL accept a Build Artifact version identifier and load the corresponding Artifact from the Artifact Registry. It SHALL then start the business application defined in the Artifact using the Artifact's Dockerfile.

#### Scenario: Load artifact and start application
- **WHEN** runtime receives a start request with artifact version `v1` for project `proj-abc`
- **THEN** it loads the artifact from `projects/proj-abc/artifacts/v1/`, builds the Docker image from the artifact's Dockerfile, and starts the container

#### Scenario: Artifact not found
- **WHEN** runtime receives a start request with a non-existent artifact version
- **THEN** it SHALL return a 404 error with message "Artifact version not found"

#### Scenario: Docker build failure
- **WHEN** the artifact's Dockerfile fails to build
- **THEN** runtime SHALL return a clear error message including the Docker build log output

### Requirement: Runtime API
The nebula-runtime SHALL expose a REST API for managing artifact lifecycle:
- `POST /api/v1/runtime/start` — Load artifact and start application
- `POST /api/v1/runtime/stop` — Stop the running application
- `GET /api/v1/runtime/status` — Query running status of the application
- `GET /api/v1/runtime/logs` — Stream application logs

#### Scenario: Start application via API
- **WHEN** client sends `POST /api/v1/runtime/start` with `{ "project_id": "proj-abc", "version": "v1" }`
- **THEN** runtime loads the artifact, starts the container, and returns `{ "status": "running", "url": "http://localhost:8080", "container_id": "..." }`

#### Scenario: Query status when running
- **WHEN** client sends `GET /api/v1/runtime/status` and an application is running
- **THEN** runtime returns `{ "status": "running", "project_id": "proj-abc", "version": "v1", "started_at": "..." }`

#### Scenario: Query status when idle
- **WHEN** client sends `GET /api/v1/runtime/status` and no application is running
- **THEN** runtime returns `{ "status": "idle" }`

#### Scenario: Stop running application
- **WHEN** client sends `POST /api/v1/runtime/stop`
- **THEN** runtime stops and removes the running container, and returns `{ "status": "stopped" }`

#### Scenario: Access application logs
- **WHEN** client sends `GET /api/v1/runtime/logs`
- **THEN** runtime returns recent container logs as a text response

### Requirement: Health check
The runtime engine SHALL expose a health check endpoint for monitoring.

#### Scenario: Health check returns healthy
- **WHEN** client sends `GET /health`
- **THEN** runtime returns `{ "status": "ok" }`

### Requirement: One application at a time
The nebula-runtime SHALL run at most one application at a time. Starting a new application SHALL automatically stop the currently running one.

#### Scenario: Start new application replaces running one
- **WHEN** application A is running and client sends start request for application B
- **THEN** runtime stops application A, then starts application B

### Requirement: Container resource limits
The runtime engine SHALL apply resource limits when starting application containers:
- CPU: 1 core limit
- Memory: 512 MB limit
- Network: default bridge, no external access restrictions (v1)

#### Scenario: Container started with resource limits
- **WHEN** runtime starts an application container
- **THEN** the container SHALL be created with `--cpus=1` and `--memory=512m` flags

### Requirement: Platform integration endpoint
The nebula-runtime SHALL expose an endpoint for nebula-platform to push new artifacts:
- `POST /api/v1/runtime/push` — Accept a new artifact version from platform
- `GET /api/v1/runtime/versions` — List available artifact versions on this runtime

#### Scenario: Push artifact from platform
- **WHEN** platform sends `POST /api/v1/runtime/push` with artifact payload
- **THEN** runtime stores the artifact in its local registry and returns the assigned version ID

#### Scenario: List available versions
- **WHEN** client sends `GET /api/v1/runtime/versions`
- **THEN** runtime returns a list of all stored artifact versions with their metadata

### Requirement: Runtime configuration via environment
The nebula-runtime SHALL be configurable via environment variables:
- `RUNTIME_PORT` — API server port (default: 8001)
- `ARTIFACTS_DIR` — Artifact storage directory (default: `./artifacts`)
- `PLATFORM_URL` — Upstream nebula-platform URL (optional, for status reporting)

#### Scenario: Default configuration
- **WHEN** runtime starts without any environment variables set
- **THEN** it SHALL use `RUNTIME_PORT=8001` and `ARTIFACTS_DIR=./artifacts`

#### Scenario: Custom configuration
- **WHEN** runtime starts with `RUNTIME_PORT=9000` and `ARTIFACTS_DIR=/data/artifacts`
- **THEN** the API SHALL listen on port 9000 and store artifacts in `/data/artifacts`
