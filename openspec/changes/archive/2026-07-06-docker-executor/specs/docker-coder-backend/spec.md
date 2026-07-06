## ADDED Requirements

### Requirement: Coding container lifecycle management

The `DockerCoderBackend` SHALL manage the full lifecycle of a coding container: pull or build image, create container, start container, wait for completion, collect logs, and remove container.

#### Scenario: Start coding container
- **WHEN** `execute_coding` is called
- **THEN** the system SHALL create and start a Docker container from the configured coder image, mounting the project directory as a volume

#### Scenario: Stop and clean up coding container
- **WHEN** coding completes (success, failure, or cancellation)
- **THEN** the system SHALL stop the container and remove it, preserving the mounted volume contents on the host

#### Scenario: Coding container fails to start
- **WHEN** the configured coder image is not found and cannot be pulled
- **THEN** the system SHALL return a `CodingResult` with `status="failed"` and a descriptive error message

### Requirement: Build container lifecycle management

The `DockerCoderBackend` SHALL manage the full lifecycle of a build container: create container from builder image, run tests, package artifact, collect exit code and logs, and remove container.

#### Scenario: Successful build pipeline
- **WHEN** `execute_build` is called with a project directory containing valid Python source code
- **THEN** the system SHALL start a build container, run `pip install -r requirements.txt`, execute `pytest`, and upon success package the source into `artifact.tar.gz` with `manifest.json` in the configured output directory on the shared volume

#### Scenario: Build test failure
- **WHEN** `execute_build` is called and `pytest` fails
- **THEN** the system SHALL return a `BuildResult` with `status="failed"` and include test failure details from the container's stdout/stderr

#### Scenario: Build container output structure
- **WHEN** a build completes successfully
- **THEN** the shared volume output directory SHALL contain:
  - `artifact.tar.gz`: compressed archive of the source code
  - `manifest.json`: metadata including version, creation timestamp, test results summary

### Requirement: Pre-installed Claude Code in coder image

The coder Docker image SHALL have Claude Code CLI (`@anthropic-ai/claude-code`) pre-installed via npm, along with Python development tools (`ruff`, `pytest`, `pytest-cov`).

#### Scenario: Verify coder image contents
- **WHEN** the coder image is built or pulled
- **THEN** it SHALL contain: `claude` CLI command in PATH, `python3`, `pip`, `pytest`, `ruff`, and a configured working directory at `/workspace`

### Requirement: Project directory sharing via volume mounts

The `DockerCoderBackend` SHALL use Docker volume mounts to share the host project directory with both coding and build containers. The mount path SHALL be consistent (`/workspace`) across both containers.

#### Scenario: Coder container mounts project directory
- **WHEN** a coding container is started
- **THEN** the host project directory SHALL be mounted at `/workspace` inside the container with read-write access

#### Scenario: Build container mounts project directory as input
- **WHEN** a build container is started
- **THEN** the host project directory SHALL be mounted at `/workspace` inside the container with read-only access to the source, and a writable subdirectory at `/workspace/artifacts/` for build output

### Requirement: Configurable resource limits

The `DockerCoderBackend` SHALL apply configurable CPU and memory limits to both coding and build containers, with separate defaults for each container type.

#### Scenario: Coding container resource limits
- **WHEN** a coding container is started
- **THEN** it SHALL be limited to the configured CPU count (default: 2) and memory (default: 2GB), overridable via environment variables `CODER_CPU_LIMIT` and `CODER_MEMORY_LIMIT`

#### Scenario: Build container resource limits
- **WHEN** a build container is started
- **THEN** it SHALL be limited to the configured CPU count (default: 1) and memory (default: 512MB), overridable via environment variables `BUILDER_CPU_LIMIT` and `BUILDER_MEMORY_LIMIT`

### Requirement: Configurable image names

The system SHALL allow configuring Docker image names/tags for both the coder and builder images via application configuration.

#### Scenario: Custom coder image tag
- **WHEN** `CODER_IMAGE=nebula-coder:v2` is configured
- **THEN** the DockerCoderBackend SHALL use `nebula-coder:v2` instead of the default image name when starting coding containers

#### Scenario: Default image names
- **WHEN** no custom image names are configured
- **THEN** the system SHALL use `nebula-coder:latest` for coding containers and `nebula-builder:latest` for build containers

### Requirement: Claude Code authorization injection

The system SHALL pass the host machine's Claude Code authorization (API key or session token) into the coding container via environment variable, enabling Claude Code to operate inside the container without additional login steps.

#### Scenario: ANTHROPIC_API_KEY passed to coding container
- **WHEN** a coding container is started and `ANTHROPIC_API_KEY` environment variable is set on the host
- **THEN** the DockerCoderBackend SHALL pass `ANTHROPIC_API_KEY` to the coding container as an environment variable

#### Scenario: Fallback to Claude Code config directory mount
- **WHEN** `ANTHROPIC_API_KEY` is not set on the host
- **THEN** the system SHALL attempt to mount `~/.claude/` from the host into the container's equivalent path to provide existing Claude Code authorization

### Requirement: Container log capture for diagnostics

The `DockerCoderBackend` SHALL capture container stdout/stderr logs and include them in error reporting for debugging purposes.

#### Scenario: Failed coding returns container logs
- **WHEN** a coding container exits with a non-zero exit code
- **THEN** the `CodingResult` SHALL include the last 50 lines (configurable via settings) of container stdout/stderr in the `error` field

#### Scenario: Build failure captures test output
- **WHEN** a build container exits due to test failure
- **THEN** the `BuildResult` SHALL include `pytest` output from the container's stdout in the `error` or `test_output` field

### Requirement: Builder image uses alpine base

The builder Docker image SHALL use `python:3.12-alpine` as its base for minimal size, installing only necessary dependencies at build time.

#### Scenario: Builder image is lightweight
- **WHEN** the builder image is built
- **THEN** its base SHALL be `python:3.12-alpine`, and it SHALL NOT pre-install any Python packages (dependencies installed per-project via `pip install -r requirements.txt`)

### Requirement: Two containers use separate lifecycle tracking

The `DockerCoderBackend` SHALL track coding and build container lifecycles independently, such that a build can proceed after coding completes without requiring the coding container to remain running.

#### Scenario: Build runs after coding container is removed
- **WHEN** coding completes and the coding container has been removed
- **THEN** the system SHALL be able to start a new build container using the shared volume contents, without the coding container running
