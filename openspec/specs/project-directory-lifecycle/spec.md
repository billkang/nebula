# project-directory-lifecycle Specification

## Purpose

管理用户项目在文件系统中的目录生命周期 — 项目创建时自动初始化 openspec 工作区，项目删除时清理磁盘残留。

## ADDED Requirements

### Requirement: Project directory created on project creation

When a new project is created via `POST /projects`, the system SHALL create the corresponding file system directory.

- **Directory path**: `projects/{username}-{change_name}/`
- **change_name**: derived by LLM translation of the project name (Chinese → English kebab-case)
- **openspec init**: After creating the directory, run `openspec init --tools none` in it to initialize the openspec workspace structure

#### Scenario: Successful project creation creates directory

- **WHEN** user creates a project with name = "旅游助手"
- **THEN** the system translates name to change_name = "travel-assistant", username = "billkang"
- **AND** creates directory `projects/billkang-travel-assistant/`
- **AND** the directory contains `openspec/` with `changes/archive/` and `specs/` subdirectories

#### Scenario: Directory already exists

- **WHEN** user creates a project whose computed directory path already exists
- **THEN** the system SHALL raise an error and not create a duplicate project record
- **AND** the error message SHALL indicate the conflict

#### Scenario: Database creation succeeds but directory creation fails

- **WHEN** database record is created but filesystem mkdir fails (e.g., permission error)
- **THEN** the system SHALL roll back the database creation
- **AND** return a 500 error with an appropriate message

### Requirement: Change name generation via LLM

The system SHALL use an LLM to translate the project name (Chinese or any language) into an English kebab-case identifier suitable for filesystem paths and openspec change names.

- **Translation rules**: output SHALL be lowercase, words separated by hyphens, no spaces or special characters
- **Pinyin is NOT allowed**: "旅游助手" → "travel-assistant", NOT "lv-you-zhu-shou"
- **Consistency**: same project name SHALL produce the same change_name (deterministic with same LLM model/temperature)
- **Storage**: the generated change_name SHALL be stored in the DB `projects.change_name` column
- **DB only stores change_name**: without the "{username}-" prefix

#### Scenario: Chinese project name translated correctly

- **WHEN** project name = "旅游助手"
- **THEN** change_name = "travel-assistant"

#### Scenario: English project name pass-through

- **WHEN** project name = "E-commerce Dashboard"
- **THEN** change_name = "e-commerce-dashboard"

#### Scenario: LLM translation fails

- **WHEN** the LLM call fails or returns an invalid format
- **THEN** the system SHALL return a 500 error
- **AND** not create the project record in DB

### Requirement: Project directory deleted on project deletion

When a project is deleted via `DELETE /projects/{id}`, the system SHALL remove the corresponding file system directory.

- **Directory path**: `projects/{username}-{change_name}/`
- **Cleanup**: recursive removal of the entire project directory tree
- **Partial failure**: if deletion fails (e.g., permission error), log the error but do NOT block the DB deletion — the project record in DB is the source of truth

#### Scenario: Successful deletion removes directory

- **WHEN** user deletes a project with directory `projects/billkang-travel-assistant/`
- **THEN** the directory SHALL be removed from the filesystem
- **AND** the DB record SHALL be deleted

#### Scenario: Directory already deleted or missing

- **WHEN** directory does not exist at deletion time
- **THEN** the system SHALL still delete the DB record successfully
- **AND** return success with a log warning

### Requirement: Project model uses auto-increment integer id

The `projects` table SHALL use an auto-increment integer as the primary key, replacing UUID.

- **Column type**: `Integer`, auto-increment, primary key
- **Existing UUID-based projects**: handle migration if any exist (this is a new platform, no migration needed)
- **New columns**: `change_name VARCHAR(255) NOT NULL`

#### Scenario: Create project returns auto-increment id

- **WHEN** a new project is created
- **THEN** the project SHALL have id = 1, 2, 3, ... (sequential)
- **AND** the response SHALL include both `id` (integer) and `change_name`
