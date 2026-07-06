# Rebuild Pipeline Specification

## ADDED Requirements

### Requirement: Rebuild from sandbox working directory
The build pipeline SHALL support rebuilding from the sandbox working directory instead of the original generated source directory, producing a new Artifact version.

#### Scenario: Rebuild creates new version
- **WHEN** PM triggers a rebuild from the code sandbox
- **THEN** the pipeline SHALL use `projects/<project-id>/sandbox/` as the source directory
- **THEN** the pipeline SHALL run the full build process (dependency verification → tests → integrity check → packaging)
- **THEN** a new Artifact version SHALL be created with an auto-incremented version number

### Requirement: Version auto-increment for sandbox rebuilds
Sandbox rebuilds SHALL produce new Artifact versions distinct from the original build versions, using the same auto-increment scheme.

#### Scenario: Version increment
- **WHEN** the original Artifact is `v1` and PM triggers a sandbox rebuild
- **THEN** the resulting Artifact SHALL be `v2`
- **WHEN** PM triggers another sandbox rebuild
- **THEN** the resulting Artifact SHALL be `v3`

### Requirement: Test execution on sandbox code
The rebuild pipeline SHALL run the same test suite on sandbox-modified code as on originally generated code.

#### Scenario: Run tests on modified code
- **WHEN** a sandbox rebuild is triggered
- **THEN** the pipeline SHALL run `pytest` on the sandbox working directory
- **WHEN** tests pass
- **THEN** the pipeline SHALL proceed to packaging
- **WHEN** tests fail
- **THEN** the pipeline SHALL return the test failure output and abort the build

### Requirement: Artifact integrity check on sandbox code
The rebuild pipeline SHALL verify that the sandbox working directory contains all required files before packaging.

#### Scenario: Integrity check passes
- **WHEN** all required files exist in the sandbox working directory
- **THEN** the pipeline SHALL proceed to packaging

#### Scenario: Integrity check fails
- **WHEN** PM deleted `requirements.txt` or `Dockerfile` from the sandbox
- **THEN** the pipeline SHALL return a clear error message listing the missing files

### Requirement: Auto-push to runtime after rebuild
After a successful sandbox rebuild, the new Artifact SHALL be automatically pushed to nebula-runtime for preview.

#### Scenario: Push after rebuild
- **WHEN** a sandbox rebuild completes successfully
- **THEN** the platform SHALL automatically push the new Artifact to nebula-runtime via `POST /api/v1/runtime/push`
- **THEN** the sandbox SHALL display a "Preview in Runtime" button that links to the running application

#### Scenario: Runtime unavailable
- **WHEN** a sandbox rebuild completes but nebula-runtime is not available
- **THEN** the Artifact SHALL still be created and stored in the registry
- **THEN** the sandbox SHALL display a warning: "Runtime not available — artifact saved locally"
- **THEN** the PM SHALL still be able to download the Artifact manually

### Requirement: Snapshot-based rollback
PM SHALL be able to roll back to any previous sandbox snapshot from the current editing session.

#### Scenario: Rollback to snapshot
- **WHEN** PM opens the snapshot history panel
- **THEN** the sandbox SHALL list all snapshots with timestamps
- **WHEN** PM selects a snapshot and clicks "Restore"
- **THEN** the sandbox SHALL restore all files in the working directory to the snapshot's state
- **THEN** the editor SHALL reload with the restored file contents

### Requirement: Platform integration for sandbox rebuild
The sandbox rebuild SHALL reuse the existing build pipeline infrastructure (`build_service.py`) with modified parameters.

#### Scenario: Reuse build service
- **WHEN** a sandbox rebuild is triggered
- **THEN** the build pipeline SHALL call the same `BuildService.build()` method used by the original pipeline
- **THEN** the source directory parameter SHALL point to the sandbox working directory instead of the original src

### Requirement: Build cancellation
PM SHALL be able to cancel an in-progress sandbox rebuild.

#### Scenario: Cancel rebuild
- **WHEN** a rebuild is in progress (e.g., running tests)
- **THEN** the sandbox SHALL display a "Cancel" button
- **WHEN** PM clicks "Cancel"
- **THEN** the build process SHALL be terminated
- **THEN** the sandbox SHALL return to editing mode
- **THEN** no new Artifact version SHALL be created
