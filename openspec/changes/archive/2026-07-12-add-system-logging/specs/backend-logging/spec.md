## ADDED Requirements

### Requirement: System log initialization on startup
The build-engine backend SHALL initialize logging configuration at application startup, before any request is processed. The initialization SHALL configure log level, output format, file handler with rotation, and console handler. Runtime-engine is out of scope for this change.

#### Scenario: Logging initialized at startup
- **WHEN** the FastAPI application starts
- **THEN** the logging system SHALL be configured with the specified LOG_LEVEL, file handler, and console handler
- **AND** all application modules using `logging.getLogger(__name__)` SHALL produce log output

#### Scenario: Existing loggers produce output after initialization
- **WHEN** any module calls `logger.info()`, `logger.warning()`, or `logger.error()`
- **THEN** the log message SHALL be written to both the log file and console (stderr)

### Requirement: Log level configuration via environment variable
The system SHALL read `LOG_LEVEL` from environment, defaulting to `INFO`. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

#### Scenario: Default log level
- **WHEN** `LOG_LEVEL` is not set in environment
- **THEN** the system SHALL use `INFO` as the default log level

#### Scenario: Custom log level
- **WHEN** `LOG_LEVEL=DEBUG` is set in environment
- **THEN** the system SHALL output `DEBUG` level and above messages

### Requirement: Log directory configuration via environment variable
The system SHALL read `LOG_DIR` from environment, defaulting to `./logs`. Log files SHALL be written to this directory.

#### Scenario: Default log directory
- **WHEN** `LOG_DIR` is not set in environment
- **THEN** the system SHALL create and write logs to `./logs` relative to the application working directory

#### Scenario: Custom log directory
- **WHEN** `LOG_DIR=/var/log/nebula` is set in environment
- **THEN** the system SHALL create and write logs to `/var/log/nebula`

### Requirement: Rotating file handler
Log files SHALL rotate daily at midnight (`TimedRotatingFileHandler` with `when='midnight'`). Log files SHALL be retained for 30 days. File name format: `nebula-{YYYY-MM-DD}.log`.

#### Scenario: Daily log rotation
- **WHEN** the system clock passes midnight
- **THEN** a new log file `nebula-{new-date}.log` SHALL be created
- **AND** the previous day's log file SHALL NOT be modified further

#### Scenario: Log retention
- **WHEN** a log file is older than 30 days
- **THEN** the system SHALL automatically delete it

### Requirement: Log format
Log messages SHALL follow the format: `2026-07-12 14:30:00,123 | INFO | module_name | message` with optional traceback for exceptions.

#### Scenario: Normal log message format
- **WHEN** a log message is written at INFO level
- **THEN** the output SHALL include: timestamp, log level, logger name, and the message text

#### Scenario: Exception log format
- **WHEN** `logger.exception()` or an exception is logged
- **THEN** the output SHALL include the full traceback after the message line

### Requirement: Request logging middleware
The build-engine backend SHALL add an ASGI middleware that logs every HTTP request, including SSE streaming requests. The middleware SHALL write a single log entry when the response completes (stream finished or connection closed), so that the final status code and total duration are known. At `INFO` level, the middleware SHALL log: HTTP method, request path, status code, duration (ms), client IP, and user ID (if authenticated). At `DEBUG` level, it SHALL additionally log request body and response body.

#### Scenario: Request logged at INFO level
- **WHEN** any HTTP request is processed by the application
- **THEN** a log entry SHALL be written at INFO level containing method, path, status code, duration, and client IP

#### Scenario: Authenticated request includes user ID
- **WHEN** an authenticated user sends a request
- **THEN** the log entry SHALL include the user ID

#### Scenario: DEBUG level logs request body
- **WHEN** `LOG_LEVEL=DEBUG` and a request is processed
- **THEN** the log entry SHALL additionally include the request body and response body (truncated to 10KB)

### Requirement: Exception logging in error handlers
The build-engine backend's global exception handlers SHALL log the full exception with traceback before returning error responses.

#### Scenario: Validation error logged
- **WHEN** a `RequestValidationError` is raised
- **THEN** the exception SHALL be logged before returning the error response

#### Scenario: Unhandled exception logged
- **WHEN** an unhandled exception occurs in any route handler
- **THEN** the full traceback SHALL be logged before returning a 500 response

### Requirement: Business stage logging utility
The system SHALL provide a business logging helper (`biz_logger`) that produces structured log entries for major business stages. Entries SHALL use the format `[BIZ] [STAGE] [STEP] | metadata` to enable easy filtering and stage identification in log files.

#### Scenario: Business stage start
- **WHEN** a major business stage begins (project creation, SDD generation, code generation)
- **THEN** a log entry SHALL be written at INFO level with `[BIZ] [STAGE_NAME] START` and metadata (project_id, username, etc.)

#### Scenario: Business step within stage
- **WHEN** a sub-step within a business stage is executed
- **THEN** a log entry SHALL be written with `[BIZ] [STAGE_NAME] [STEP_NAME]` and relevant metadata

#### Scenario: Business stage end with status
- **WHEN** a business stage completes (success or failure)
- **THEN** a log entry SHALL be written with `[BIZ] [STAGE_NAME] END status=ok|failed` and duration

### Requirement: Project creation stage logging
The project creation flow SHALL log each major step with stage marker `CREATE_PROJECT`.

#### Scenario: Project creation steps logged
- **WHEN** a project is being created via `ProjectService.create_project()`
- **THEN** the following SHALL be logged with `[BIZ] [CREATE_PROJECT]`:
  - `START` with project name and username
  - `[translate-name]` step with result
  - `[db-record]` step with project_id
  - `[fs-init]` step with directory path
  - `END status=ok` or `END status=failed` with error reason

### Requirement: SDD document generation stage logging
The SDD document generation flow SHALL log each major step with stage marker `SPEC_GEN`.

#### Scenario: SDD generation steps logged
- **WHEN** `DocService.generate_docs()` is called
- **THEN** the following SHALL be logged with `[BIZ] [SPEC_GEN]`:
  - `START` with project_id
  - `[write-context]` step
  - `[create-change]` step with change name
  - `[proposal]`, `[specs]`, `[design]`, `[tasks]` steps for each artifact
  - `END status=ok` or `END status=failed`

### Requirement: Code generation stage logging
The code generation/build flow SHALL log each major step with stage marker `CODE_GEN`.

#### Scenario: Code generation steps logged
- **WHEN** `BuildService.build()` is executed
- **THEN** the following SHALL be logged with `[BIZ] [CODE_GEN]`:
  - `START` with project_id
  - `[container-build]` step
  - `[verify-artifacts]` step with file list
  - `[push-runtime]` step
  - `END status=ok` or `END status=failed` with artifact version

### Requirement: Agent phase transition logging
The agent conversation flow SHALL log phase transitions with stage marker `AGENT_PHASE`.

#### Scenario: Agent phase transitions logged
- **WHEN** the chat agent transitions between phases (greeting → collecting → clarifying → confirming → generating)
- **THEN** a log entry SHALL be written with `[BIZ] [AGENT_PHASE] [transition] from=old_phase to=new_phase`
- **AND** the session_id SHALL be included in metadata

### Requirement: Per-project independent log file
Each project SHALL have its own independent log file in `projects/{username}-{change_name}/logs/{change_name}.log`. This log file SHALL capture all business stage logs (`[BIZ]` entries) for that project's complete lifecycle.

#### Scenario: Project log file created on project creation
- **WHEN** a project is successfully created in `ProjectService.create_project()`
- **THEN** a per-project log file SHALL be created at `projects/{username}-{change_name}/logs/{change_name}.log`
- **AND** the file SHALL use the same daily rotation and 30-day retention as the system log

#### Scenario: Business stages written to project log
- **WHEN** any `[BIZ]` stage log is written for a project (CREATE_PROJECT, SPEC_GEN, CODE_GEN, AGENT_PHASE)
- **THEN** the log entry SHALL appear in both the system log (`nebula-{date}.log`) and the project-specific log (`{change_name}.log`)
- **AND** the project log SHALL only contain entries for its own project
