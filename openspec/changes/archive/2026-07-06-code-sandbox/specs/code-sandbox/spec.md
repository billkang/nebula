# Code Sandbox Specification

## ADDED Requirements

### Requirement: Monaco Editor integration
The code sandbox SHALL integrate Monaco Editor as the source code editor, supporting syntax highlighting for common languages (Python, JavaScript, TypeScript, JSX, JSON, YAML, Markdown).

#### Scenario: Editor loads with syntax highlighting
- **WHEN** PM opens the code sandbox for a project with Python source code
- **THEN** the editor SHALL display the code with Python syntax highlighting, line numbers, and a monospace font

#### Scenario: Supported file types
- **WHEN** PM opens a `.py`, `.js`, `.tsx`, `.json`, `.yaml`, or `.md` file
- **THEN** the editor SHALL apply the appropriate syntax highlighting for that file type

### Requirement: File tree panel
The code sandbox SHALL display a file tree panel showing the full source directory structure of the project's Artifact, with file icons and folder expansion.

#### Scenario: Display file tree
- **WHEN** PM enters the code sandbox
- **THEN** the left panel SHALL display a file tree with all files and folders from the Artifact's `src/` directory
- **THEN** the first file in the tree SHALL be automatically selected and displayed in the editor

#### Scenario: Navigate file tree
- **WHEN** PM clicks on a file in the file tree
- **THEN** the editor SHALL load and display the selected file's content
- **THEN** the selected file SHALL be visually highlighted in the file tree

#### Scenario: Folder expand/collapse
- **WHEN** PM clicks on a folder in the file tree
- **THEN** the folder SHALL expand to show its children or collapse to hide them

### Requirement: Source code editing
The code sandbox SHALL allow PM to modify file contents directly in the Monaco Editor. Modifications SHALL be tracked as unsaved changes until explicitly saved.

#### Scenario: Edit file content
- **WHEN** PM modifies the content of a file in the editor
- **THEN** the editor SHALL show a visual indicator (dot/badge) on the file's tab or tree entry indicating unsaved changes

#### Scenario: Multiple file edits
- **WHEN** PM edits multiple files
- **THEN** each file with unsaved changes SHALL be visually marked in the file tree
- **THEN** switching between files SHALL preserve each file's unsaved state

### Requirement: Save modifications
PM SHALL be able to save file modifications, writing changes to the sandbox working directory.

#### Scenario: Save single file
- **WHEN** PM clicks "Save" and a file has unsaved changes
- **THEN** the file content SHALL be written to the sandbox working directory
- **THEN** the unsaved indicator SHALL be removed from that file

#### Scenario: Save all files
- **WHEN** PM clicks "Save All" (or uses Ctrl+S / Cmd+S)
- **THEN** all files with unsaved changes SHALL be written to the sandbox working directory
- **THEN** all unsaved indicators SHALL be removed

### Requirement: Working directory management
The sandbox SHALL maintain a working directory for each project's editing session, isolated from the original Artifact files.

#### Scenario: Working directory lifecycle
- **WHEN** PM enters the code sandbox for the first time after a build
- **THEN** the sandbox SHALL copy the Artifact's source files to a sandbox working directory at `projects/<project-id>/sandbox/`
- **WHEN** PM saves changes
- **THEN** files SHALL be written to the sandbox working directory, not the original Artifact

### Requirement: Snapshot before rebuild
Before triggering a rebuild, the sandbox SHALL automatically create a snapshot of the current working state.

#### Scenario: Auto-snapshot on rebuild
- **WHEN** PM clicks "Rebuild" after making modifications
- **THEN** the sandbox SHALL create a timestamped snapshot of the working directory before initiating the build pipeline
- **THEN** the snapshot SHALL be stored at `projects/<project-id>/sandbox_snapshots/<timestamp>/` (outside sandbox dir to avoid test discovery conflicts)

#### Scenario: Snapshot structure
- **WHEN** a snapshot is created
- **THEN** it SHALL contain a full copy of all files from the working directory at that moment
- **THEN** the snapshot SHALL include a metadata file with the timestamp and a brief description

### Requirement: Diff view against original Artifact
The sandbox SHALL provide a diff view comparing modified files against the original Artifact version.

#### Scenario: View diff
- **WHEN** PM clicks "View Diff" on a modified file
- **THEN** the sandbox SHALL display a unified diff showing changes from the original Artifact version to the current working copy
- **THEN** added lines SHALL be highlighted in green and removed lines in red

#### Scenario: Diff for unchanged files
- **WHEN** PM clicks "View Diff" on an unmodified file
- **THEN** the sandbox SHALL display "No changes" message

### Requirement: Restore from Artifact original
PM SHALL be able to restore a file to its original Artifact version, discarding all modifications.

#### Scenario: Restore single file
- **WHEN** PM clicks "Restore Original" on a modified file
- **THEN** the file content SHALL revert to the original Artifact version
- **THEN** the unsaved indicator SHALL be removed

#### Scenario: Restore all files
- **WHEN** PM clicks "Restore All"
- **THEN** all files in the working directory SHALL revert to their original Artifact versions
- **THEN** all unsaved indicators SHALL be removed

### Requirement: Trigger rebuild button
The sandbox SHALL provide a prominent "Rebuild" button that initiates the full build pipeline from the sandbox working directory.

#### Scenario: Rebuild button visible
- **WHEN** PM is in the code sandbox
- **THEN** a "Rebuild" button SHALL be visible in the sandbox interface
- **WHEN** all files are at original state (no modifications)
- **THEN** the Rebuild button SHALL still be visible and functional (forces rebuild with same source)

#### Scenario: Rebuild in progress
- **WHEN** a rebuild is running
- **THEN** the Rebuild button SHALL be disabled and show "Rebuilding..."
- **THEN** the sandbox SHALL display build progress (testing → verifying → packaging → pushing)
- **WHEN** the build completes
- **THEN** the Rebuild button SHALL be re-enabled

### Requirement: Sandbox state persistence
The sandbox SHALL persist PM's editing state across page reloads within the same session.

#### Scenario: Persist unsaved changes
- **WHEN** PM has unsaved changes and refreshes the page
- **THEN** the unsaved changes SHALL be recovered from the working directory
- **THEN** the editor SHALL restore the file selection and scroll position if possible

### Requirement: Build output and diff display
After a rebuild completes, the sandbox SHALL display the build result and allow PM to compare the old and new Artifact versions.

#### Scenario: Rebuild success notification
- **WHEN** a rebuild completes successfully
- **THEN** the sandbox SHALL show "Rebuild successful — Artifact v{n+1} created" with a link to preview in runtime
- **THEN** a "View Diff against v{n}" button SHALL be available

#### Scenario: Rebuild failure
- **WHEN** a rebuild fails
- **THEN** the sandbox SHALL display the build error message
- **THEN** PM SHALL still have access to the working directory to fix the issue and retry
