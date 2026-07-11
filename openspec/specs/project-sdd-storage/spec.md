# project-sdd-storage Specification

## Purpose

用户项目的 SDD 文档从其专属的 openspec 工作区中生成和读取，不再与星云平台自身的 openspec 混用。

## ADDED Requirements

### Requirement: DocService runs openspec CLI in project workspace

`DocService.generate_docs()` SHALL run the openspec CLI from the project's own openspec workspace directory (`projects/{username}-{change_name}/`), not from the backend root.

- **Project workspace**: `projects/{username}-{change_name}/`
- **Change name**: `{username}-{change_name}` (e.g., `billkang-travel-assistant`)
- **CWD**: the project directory (`projects/{username}-{change_name}/`), where `openspec init` has been run
- **Change creation**: before running instructions, create the change via `openspec new change <change-name>` if it doesn't exist
- **Instructions**: run `openspec instructions <artifact> --change <change-name> --json` for each artifact (proposal, specs, design, tasks)
- **Output location**: artifacts written to `projects/{username}-{change_name}/openspec/changes/{change-name}/`
- **No copy step**: SDD stays in openspec workspace, no separate sdd/ directory needed

#### Scenario: Generate docs for first requirement

- **WHEN** user confirms requirements for their first project requirement
- **THEN** the system creates change `openspec new change billkang-travel-assistant-init` in the project workspace
- **AND** runs `openspec instructions proposal --change billkang-travel-assistant-init --json`
- **AND** writes proposal/specs/design/tasks to `projects/billkang-travel-assistant/openspec/changes/billkang-travel-assistant-init/`

#### Scenario: Generate docs for subsequent requirement

- **WHEN** user confirms requirements for a subsequent feature (e.g., "add user login")
- **THEN** the system creates a NEW change `openspec new change billkang-travel-assistant-add-login`
- **AND** the previous change `billkang-travel-assistant-init` remains archived in the workspace

#### Scenario: openspec CLI fails

- **WHEN** `openspec new change` or `openspec instructions` returns non-zero exit code
- **THEN** `generate_docs()` SHALL return `{"success": false, "message": "...失败: {stderr}"}`
- **AND** not create partial output

### Requirement: conversation_context.md written to project root

`DocService.generate_docs()` SHALL write `conversation_context.md` to the project root directory (`projects/{username}-{change_name}/`), not to `.agent_context/`.

- **Path**: `projects/{username}-{change_name}/conversation_context.md`
- **Content sections**: `## 需求摘要（来自 Agent 对话）` with `req_summary`, `## Out of Scope` with `out_of_scope` items
- **Overwrite**: SHALL overwrite any existing file (latest conversation is the source of truth)
- **Not stored in DB**: conversation_context is a transient derived artifact, not persisted in the database

#### Scenario: Write conversation context

- **WHEN** `generate_docs()` is called with req_summary and out_of_scope
- **THEN** file `projects/billkang-travel-assistant/conversation_context.md` is created/overwritten
- **AND** contains the req_summary under `## 需求摘要` header
- **AND** contains out_of_scope items as a bullet list under `## Out of Scope` header

#### Scenario: No out_of_scope provided

- **WHEN** `out_of_scope` is None or empty
- **THEN** the `## Out of Scope` section SHALL be omitted from the file

### Requirement: DocService supports multi-change listing

`DocService.list_docs(project_id)` SHALL list all changes in the project's openspec workspace, not just the latest one.

- **Change enumeration**: list directories under `projects/{username}-{change_name}/openspec/changes/`
- **Exclude**: skip `archive/` directory
- **Status per change**: for each change, report which artifacts (proposal/specs/design/tasks) exist
- **Return format**: list of `{change_name, artifacts: [{type, exists}]}`

#### Scenario: List docs for project with one change

- **WHEN** project has one change `billkang-travel-assistant-init` with proposal and design complete
- **THEN** `list_docs()` returns:
  ```json
  [
    {
      "change": "billkang-travel-assistant-init",
      "artifacts": [
        {"type": "proposal", "exists": true},
        {"type": "specs", "exists": true},
        {"type": "design", "exists": true},
        {"type": "tasks", "exists": false}
      ]
    }
  ]
  ```

#### Scenario: List docs for project with multiple changes

- **WHEN** project has two changes
- **THEN** `list_docs()` returns both changes with their respective artifact statuses

### Requirement: DocService reads SDD from project workspace

`DocService.get_doc(project_id, doc_type)` SHALL read SDD content from the project's openspec workspace.

- **Change discovery**: use the latest (most recently created) change to read from
- **Path resolution**: `projects/{username}-{change_name}/openspec/changes/{latest-change}/`
- **Artifact mapping**: "proposal" → `proposal.md`, "design" → `design.md`, "tasks" → `tasks.md`, "specs" → `specs/` directory
- **Specs reading**: walk `specs/` dir and concat all `.md` files with subdirectory headers
- **Not found**: return None if artifact file doesn't exist

#### Scenario: Get proposal content

- **WHEN** `get_doc(project_id, "proposal")` is called and proposal.md exists
- **THEN** returns the full content of the proposal.md file

#### Scenario: Get content for non-existent document

- **WHEN** `get_doc(project_id, "tasks")` is called and tasks.md doesn't exist
- **THEN** returns None
