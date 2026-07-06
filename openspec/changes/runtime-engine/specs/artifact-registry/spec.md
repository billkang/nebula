# Artifact Registry Specification

## ADDED Requirements

### Requirement: Artifact version management
The Artifact Registry SHALL store versioned Build Artifacts and support listing, selecting, and deleting versions. Each version SHALL be identified by a semantic version string (e.g., `v1`, `v2`).

#### Scenario: List artifact versions
- **WHEN** client sends `GET /api/v1/registry/artifacts?project_id=proj-abc`
- **THEN** registry returns an array of artifact versions with their metadata: `[{ "version": "v1", "created_at": "...", "status": "ready" }]`

#### Scenario: Get specific artifact version
- **WHEN** client sends `GET /api/v1/registry/artifacts/proj-abc/v1`
- **THEN** registry returns full metadata for that version: `{ "version": "v1", "created_at": "...", "manifest": { ... } }`

#### Scenario: Delete artifact version
- **WHEN** client sends `DELETE /api/v1/registry/artifacts/proj-abc/v1`
- **THEN** registry removes the version's files and returns `{ "status": "deleted" }`

#### Scenario: Version not found
- **WHEN** client requests a non-existent version
- **THEN** registry returns a 404 error

### Requirement: Artifact lifecycle states
Each artifact version SHALL track its lifecycle state: `building` → `ready` → `running` → `archived`.

#### Scenario: State transitions
- **WHEN** build pipeline creates a new artifact version
- **THEN** its status SHALL start as `building`, transition to `ready` on completion, and remain `ready` until loaded by the runtime
- **WHEN** runtime starts the artifact
- **THEN** status SHALL change to `running`

### Requirement: Artifact file structure
The registry SHALL store artifacts on disk following this structure:
```
artifacts/<project-id>/<version>/
  ├── src/                     ← Generated source code
  ├── requirements.txt         ← Dependency declarations
  ├── Dockerfile               ← Runtime image definition
  └── manifest.json            ← Version, entry point, dependencies
```

#### Scenario: Store artifact with correct structure
- **WHEN** build pipeline pushes a completed artifact to the registry
- **THEN** the registry SHALL store files at `artifacts/<project-id>/<version>/` with the mandated structure

### Requirement: Manifest JSON format
The manifest.json file SHALL contain the following fields:
```json
{
  "version": "v1",
  "created_at": "2026-07-06T12:00:00Z",
  "entry": "src/main.py",
  "dependencies": ["fastapi", "sqlalchemy"],
  "platform_version": "0.1.0"
}
```

#### Scenario: Manifest validation
- **WHEN** an artifact version is registered
- **THEN** the registry SHALL validate that manifest.json contains all required fields (version, created_at, entry)

### Requirement: Registry metadata API
The registry SHALL expose an API for platform integration:
- `GET /api/v1/registry/artifacts` — List artifact versions for a project
- `GET /api/v1/registry/artifacts/:project/:version` — Get specific version metadata
- `DELETE /api/v1/registry/artifacts/:project/:version` — Delete a version
- `POST /api/v1/registry/artifacts/:project` — Register a new artifact version (from platform build pipeline)

#### Scenario: Register new artifact
- **WHEN** platform sends `POST /api/v1/registry/artifacts/proj-abc` with artifact payload
- **THEN** registry assigns the next version number, stores files, and returns `{ "version": "v2", "status": "building" }`

#### Scenario: Auto-increment version
- **WHEN** existing versions are `v1` and a new artifact is registered for the same project
- **THEN** registry SHALL assign version `v2`
- **WHEN** versions `v1`, `v2`, `v3` exist and `v2` is deleted
- **THEN** the next registration SHALL assign `v4` (no gap filling)

### Requirement: Version rollback
The registry SHALL support rolling back to a previous artifact version by re-tagging it.

#### Scenario: Rollback to previous version
- **WHEN** PM triggers a rollback to `v1`
- **THEN** runtime loads `v1` instead of the current version, and `v1` status changes to `running`
