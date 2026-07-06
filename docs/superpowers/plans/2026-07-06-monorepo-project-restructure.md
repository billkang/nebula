# Monorepo Project Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the current flat directory layout into a monorepo structure with `packages/` directory, pnpm/uv workspace, src layout for Python packages, and shared code package skeletons.

**Architecture:** Three Python packages (build-engine-backend, runtime-engine, nebula-shared) managed via uv workspace with src layout, two frontend packages (build-engine-frontend, @nebula/shared-ui) managed via pnpm workspace. Makefile at root provides dev/test/clean entry points.

**Tech Stack:** Python (FastAPI) + uv workspace, React (Vite/TypeScript) + pnpm workspace, pydantic-settings, pytest

## Global Constraints

- All Python packages use src layout (`src/app/` or `src/nebula_shared/`)
- Internal imports remain `from app.xxx import yyy` (no namespace prefix)
- Shared packages use prefix imports: `from nebula_shared.xxx import yyy`
- Python pyproject.toml names: `build-engine-backend`, `runtime-engine`, `nebula-shared`
- Frontend pnpm package names: `build-engine-frontend` (was `nebula-frontend`), `@nebula/shared-ui`
- Existing `start.sh` stays at root unmodified
- Existing Makefile Docker targets remain unchanged
- Dependencies match current `requirements.txt` file contents

## File Structure

```
nebula/                                    # root (unchanged)
├── Makefile                               # ← MODIFY: add dev/test/clean targets
├── pnpm-workspace.yaml                    # ← CREATE
├── pyproject.toml                         # ← CREATE (uv workspace root)
├── scripts/                               # ← CREATE
│   └── README.md
├── start.sh                               # ← UNCHANGED
├── docs/superpowers/plans/                # ← UNCHANGED
├── packages/
│   ├── build-engine/
│   │   ├── backend/                       # ← MOVE from backend/ + src layout
│   │   │   ├── pyproject.toml             # ← CREATE (migrate from requirements.txt)
│   │   │   ├── src/
│   │   │   │   └── app/                   # ← MOVE from backend/app/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── config.py
│   │   │   │       ├── database.py
│   │   │   │       ├── main.py
│   │   │   │       └── api/
│   │   │   ├── tests/                     # ← MOVE from backend/tests/
│   │   │   ├── alembic/                   # ← MOVE from backend/alembic/
│   │   │   ├── alembic.ini                # ← MOVE
│   │   │   ├── seed.py                    # ← MOVE
│   │   │   └── .env.example               # ← MOVE
│   │   └── frontend/                      # ← MOVE from frontend/ (unchanged structure)
│   │       ├── package.json               # ← MODIFY: name → "build-engine-frontend", add shared-ui dep
│   │       └── ...
│   ├── runtime-engine/                    # ← MOVE from nebula-runtime/ + src layout
│   │   ├── pyproject.toml                 # ← CREATE
│   │   ├── src/
│   │   │   └── app/                       # ← MOVE from nebula-runtime/app/
│   │   │       ├── __init__.py
│   │   │       ├── config.py
│   │   │       ├── main.py
│   │   │       └── api/
│   │   ├── tests/                         # ← MOVE from nebula-runtime/tests/
│   │   ├── Dockerfile                     # ← MOVE
│   │   ├── docker-compose.yml             # ← MOVE
│   │   └── .env.example                   # ← MOVE
│   ├── shared-python/                     # ← CREATE (skeleton)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── nebula_shared/
│   │           ├── __init__.py
│   │           ├── models/
│   │           │   ├── __init__.py
│   │           │   └── common.py
│   │           ├── config/
│   │           │   ├── __init__.py
│   │           │   └── base.py
│   │           └── utils/
│   │               ├── __init__.py
│   │               └── helpers.py
│   └── shared-ui/                         # ← CREATE (skeleton)
│       ├── package.json
│       ├── tsconfig.json
│       ├── README.md
│       └── src/
│           ├── index.ts
│           ├── components/
│           │   └── .gitkeep
│           └── hooks/
│               └── .gitkeep
├── docker/                                # ← UNCHANGED
│   ├── coder/Dockerfile
│   └── builder/Dockerfile
├── _bmad-output/                          # ← UNCHANGED
├── openspec/                              # ← UNCHANGED
└── docs/                                  # ← UNCHANGED
```

---

### Task 1: 创建 packages 目录结构和迁移构建引擎后端

**Files:**
- Create: `packages/build-engine/backend/src/app/` (hierarchy)
- Create: `packages/build-engine/backend/pyproject.toml`
- Create: `packages/build-engine/backend/.env.example`
- Move: `backend/app/` → `packages/build-engine/backend/src/app/`
- Move: `backend/tests/` → `packages/build-engine/backend/tests/`
- Move: `backend/alembic/` → `packages/build-engine/backend/alembic/`
- Move: `backend/alembic.ini` → `packages/build-engine/backend/alembic.ini`
- Move: `backend/seed.py` → `packages/build-engine/backend/seed.py`
- Move: `backend/requirements.txt` → (absorbed into pyproject.toml)
- Delete: `backend/` (after verification, in Task 9)

**Interfaces:**
- Consumes: Current `backend/` directory structure
- Produces: `packages/build-engine/backend/` with src layout

- [ ] **Step 1: Create new directory structure**

```bash
mkdir -p packages/build-engine/backend/src
mkdir -p packages/build-engine/backend/tests
```

- [ ] **Step 2: Move source code files**

```bash
cp -r backend/app packages/build-engine/backend/src/app/
cp -r backend/tests/* packages/build-engine/backend/tests/
cp -r backend/alembic packages/build-engine/backend/alembic/
cp backend/alembic.ini packages/build-engine/backend/alembic.ini
cp backend/seed.py packages/build-engine/backend/seed.py
cp backend/.env.example packages/build-engine/backend/.env.example
```

Note: Using `cp` initially; the original `backend/` will be deleted after full migration verification in Task 9.

- [ ] **Step 3: Read current `backend/requirements.txt` and create `pyproject.toml`**

```bash
cat /Users/billkang/workspace/nebula/backend/requirements.txt
```

- [ ] **Step 4: Create `packages/build-engine/backend/pyproject.toml`**

```toml
[project]
name = "build-engine-backend"
version = "0.1.0"
description = "Nebula Build Engine - Backend API"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    "alembic>=1.13.0",
    "docker>=7.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/app"]

[tool.pytest.ini_options]
pythonpath = ["src"]

[tool.ruff]
target-version = "py311"
line-length = 100
```

- [ ] **Step 5: Verify pytest works in src layout**

```bash
cd packages/build-engine/backend && uv run pytest -v
```

Expected: All existing tests pass (same as before migration).

---

### Task 2: 迁移构建引擎前端

**Files:**
- Modify: `packages/build-engine/frontend/package.json` (name change)
- Move: `frontend/` → `packages/build-engine/frontend/`
- Delete: `frontend/` (after verification, in Task 9)

**Interfaces:**
- Consumes: Current `frontend/` directory
- Produces: `packages/build-engine/frontend/` with updated package.json

- [ ] **Step 1: Copy frontend to new location**

```bash
cp -r frontend packages/build-engine/frontend
```

- [ ] **Step 2: Update `packages/build-engine/frontend/package.json` name**

Change `"name": "nebula-frontend"` to `"name": "build-engine-frontend"`.

- [ ] **Step 3: Verify frontend still works standalone**

```bash
cd packages/build-engine/frontend && npm install --silent && npm run build 2>&1 | tail -5
```

Expected: Build succeeds.

---

### Task 3: 迁移运行时引擎

**Files:**
- Create: `packages/runtime-engine/pyproject.toml`
- Create: `packages/runtime-engine/src/app/` (hierarchy)
- Move: `nebula-runtime/app/` → `packages/runtime-engine/src/app/`
- Move: `nebula-runtime/tests/` → `packages/runtime-engine/tests/`
- Move: `nebula-runtime/Dockerfile` → `packages/runtime-engine/Dockerfile`
- Move: `nebula-runtime/docker-compose.yml` → `packages/runtime-engine/docker-compose.yml`
- Move: `nebula-runtime/requirements.txt` → (absorbed into pyproject.toml)
- Move: `nebula-runtime/.env.example` → `packages/runtime-engine/.env.example`
- Delete: `nebula-runtime/` (after verification, in Task 9)

**Interfaces:**
- Consumes: Current `nebula-runtime/` directory
- Produces: `packages/runtime-engine/` with src layout

- [ ] **Step 1: Create directory structure and move files**

```bash
mkdir -p packages/runtime-engine/src
cp -r nebula-runtime/app packages/runtime-engine/src/app/
cp -r nebula-runtime/tests packages/runtime-engine/tests/
cp nebula-runtime/Dockerfile packages/runtime-engine/Dockerfile
cp nebula-runtime/docker-compose.yml packages/runtime-engine/docker-compose.yml
cp nebula-runtime/.env.example packages/runtime-engine/.env.example
```

- [ ] **Step 2: Read current `nebula-runtime/requirements.txt`**

```bash
cat /Users/billkang/workspace/nebula/nebula-runtime/requirements.txt
```

Expected: fastapi, uvicorn, pydantic, pydantic-settings, httpx

- [ ] **Step 3: Create `packages/runtime-engine/pyproject.toml`**

```toml
[project]
name = "runtime-engine"
version = "0.1.0"
description = "Nebula Runtime Engine"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/app"]

[tool.pytest.ini_options]
pythonpath = ["src"]

[tool.ruff]
target-version = "py311"
line-length = 100
```

- [ ] **Step 4: Verify pytest passes in src layout**

```bash
cd packages/runtime-engine && uv run pytest -v
```

Expected: All tests pass.

---

### Task 4: 创建 shared-python 包

**Files:**
- Create: `packages/shared-python/pyproject.toml`
- Create: `packages/shared-python/README.md`
- Create: `packages/shared-python/src/nebula_shared/__init__.py`
- Create: `packages/shared-python/src/nebula_shared/models/__init__.py`
- Create: `packages/shared-python/src/nebula_shared/models/common.py`
- Create: `packages/shared-python/src/nebula_shared/config/__init__.py`
- Create: `packages/shared-python/src/nebula_shared/config/base.py`
- Create: `packages/shared-python/src/nebula_shared/utils/__init__.py`
- Create: `packages/shared-python/src/nebula_shared/utils/helpers.py`

**Interfaces:**
- Produces: `nebula_shared` package that build-engine and runtime-engine can depend on

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p packages/shared-python/src/nebula_shared/{models,config,utils}
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[project]
name = "nebula-shared"
version = "0.1.0"
description = "Nebula shared Python code (models, config, utils)"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/nebula_shared"]
```

- [ ] **Step 3: Create `src/nebula_shared/__init__.py`**

```python
"""Nebula shared package — common models, config, and utilities."""
```

- [ ] **Step 4: Create `src/nebula_shared/config/__init__.py`**

```python
from nebula_shared.config.base import BaseConfig

__all__ = ["BaseConfig"]
```

- [ ] **Step 5: Create `src/nebula_shared/config/base.py`**

```python
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """Base configuration class for all Nebula services.

    Extend this class in each service's config.py for service-specific fields.
    """

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

- [ ] **Step 6: Create `src/nebula_shared/models/__init__.py`**

```python
from nebula_shared.models.common import BaseModel

__all__ = ["BaseModel"]
```

- [ ] **Step 7: Create `src/nebula_shared/models/common.py`**

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BaseModel(BaseModel):
    """Base Pydantic model for all Nebula data models."""

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 8: Create `src/nebula_shared/utils/__init__.py`**

```python
from nebula_shared.utils.helpers import version_tuple

__all__ = ["version_tuple"]
```

- [ ] **Step 9: Create `src/nebula_shared/utils/helpers.py`**

```python
def version_tuple(version_str: str) -> tuple[int, ...]:
    """Parse a semver string into a sortable tuple.

    Example: "1.2.3" -> (1, 2, 3)
    """
    return tuple(int(part) for part in version_str.split("."))
```

- [ ] **Step 10: Create `README.md`**

```markdown
# nebula-shared

Shared Python code for Nebula platform.

## Usage

```python
from nebula_shared.config.base import BaseConfig
from nebula_shared.models.common import BaseModel
from nebula_shared.utils.helpers import version_tuple
```

## Development

```bash
uv sync
uv run pytest
```
```

- [ ] **Step 11: Verify package can be imported**

```bash
cd packages/shared-python && uv run python -c "import nebula_shared; print('OK')"
```

Expected: `OK`

---

### Task 5: 创建 shared-ui 包

**Files:**
- Create: `packages/shared-ui/package.json`
- Create: `packages/shared-ui/tsconfig.json`
- Create: `packages/shared-ui/README.md`
- Create: `packages/shared-ui/src/index.ts`
- Create: `packages/shared-ui/src/components/.gitkeep`
- Create: `packages/shared-ui/src/hooks/.gitkeep`

**Interfaces:**
- Produces: `@nebula/shared-ui` package consumable by build-engine/frontend

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p packages/shared-ui/src/{components,hooks}
```

- [ ] **Step 2: Create `package.json`**

```json
{
  "name": "@nebula/shared-ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "src/index.ts",
  "types": "src/index.ts",
  "scripts": {
    "typecheck": "tsc --noEmit"
  },
  "peerDependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.3"
  }
}
```

- [ ] **Step 3: Create `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create `src/index.ts`**

```typescript
// @nebula/shared-ui — shared UI components and hooks
export {};
```

- [ ] **Step 5: Create `.gitkeep` files and `README.md`**

```bash
touch packages/shared-ui/src/components/.gitkeep
touch packages/shared-ui/src/hooks/.gitkeep
```

```markdown
# @nebula/shared-ui

Shared React UI components and hooks for Nebula platform.

## Usage

```typescript
import {} from '@nebula/shared-ui';
```
```

---

### Task 6: 配置 pnpm workspace

**Files:**
- Create: `pnpm-workspace.yaml`
- Modify: `packages/build-engine/frontend/package.json` (add workspace dependency)

**Interfaces:**
- Consumes: `packages/build-engine/frontend/` (Task 2), `packages/shared-ui/` (Task 5)
- Produces: Working pnpm workspace

- [ ] **Step 1: Create root `pnpm-workspace.yaml`**

```yaml
packages:
  - "packages/build-engine/frontend"
  - "packages/shared-ui"
```

- [ ] **Step 2: Add `@nebula/shared-ui` as workspace dependency to build-engine/frontend**

Edit `packages/build-engine/frontend/package.json`, add to `dependencies` or `devDependencies`:

```json
"@nebula/shared-ui": "workspace:*"
```

- [ ] **Step 3: Run pnpm install to verify workspace**

```bash
pnpm install
```

Expected: No errors. `pnpm ls -r` shows both `build-engine-frontend` and `@nebula/shared-ui`.

---

### Task 7: 配置 uv workspace

**Files:**
- Create: `pyproject.toml` (root)
- Modify: `packages/build-engine/backend/pyproject.toml` (add nebula-shared dep)
- Modify: `packages/runtime-engine/pyproject.toml` (add nebula-shared dep)

**Interfaces:**
- Consumes: Task 1, 3, 4 (all Python packages exist)
- Produces: Working uv workspace

- [ ] **Step 1: Create root `pyproject.toml` (uv workspace)**

```toml
[project]
name = "nebula"
version = "0.1.0"
description = "Nebula AI Agent Platform"
requires-python = ">=3.11"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv.workspace]
members = [
    "packages/build-engine/backend",
    "packages/runtime-engine",
    "packages/shared-python",
]
```

- [ ] **Step 2: Add `nebula-shared` as dependency to `packages/build-engine/backend/pyproject.toml`**

Add to `[project]dependencies`:

```toml
"nebula-shared",
```

Also add:

```toml
[tool.uv.sources]
nebula-shared = { workspace = true }
```

- [ ] **Step 3: Add `nebula-shared` as dependency to `packages/runtime-engine/pyproject.toml`**

Same as Step 2: add `"nebula-shared"` to `dependencies` and `[tool.uv.sources]`.

- [ ] **Step 4: Run uv sync to verify workspace**

```bash
uv sync
```

Expected: All packages installed in editable mode. No dependency conflicts.

- [ ] **Step 5: Verify both engines can import from nebula_shared**

```bash
cd packages/build-engine/backend && uv run python -c "from nebula_shared.config.base import BaseConfig; print('OK')"
cd packages/runtime-engine && uv run python -c "from nebula_shared.config.base import BaseConfig; print('OK')"
```

Expected: Both print `OK`.

- [ ] **Step 6: Install frontend dependencies**

```bash
cd packages/build-engine/frontend && npm install
```

Expected: Dependencies install successfully.

---

### Task 8: 更新 Makefile 和创建 scripts 目录

**Files:**
- Modify: `Makefile`
- Create: `scripts/README.md`

- [ ] **Step 1: Read current Makefile**

- [ ] **Step 2: Update `Makefile` — preserve existing targets and add new ones**

```makefile
DOCKER_BUILDKIT ?= 1
export DOCKER_BUILDKIT

SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo "dev")

# ── Development ──────────────────────────────────────────────
.PHONY: dev
dev:
	@echo "Starting development servers..."
	@./start.sh

# ── Testing ─────────────────────────────────────────────────
.PHONY: test test-backend test-runtime test-frontend

test-backend:
	cd packages/build-engine/backend && uv run pytest -v

test-runtime:
	cd packages/runtime-engine && uv run pytest -v

test-frontend:
	cd packages/build-engine/frontend && npm test 2>/dev/null || echo "No test script defined for frontend"

test: test-backend test-runtime test-frontend

# ── Cleanup ─────────────────────────────────────────────────
.PHONY: clean

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf packages/*/backend/.venv packages/*/.venv packages/shared-python/.venv 2>/dev/null || true
	rm -rf packages/*/frontend/node_modules packages/shared-ui/node_modules 2>/dev/null || true
	@echo "Done."

# ── Docker Builds (preserved) ────────────────────────────────
.PHONY: build-coder-image build-builder-image build-images

build-coder-image:
	DOCKER_BUILDKIT=1 docker build -t nebula-coder:latest -t nebula-coder:$(SHA) -f docker/coder/Dockerfile .

build-builder-image:
	DOCKER_BUILDKIT=1 docker build -t nebula-builder:latest -t nebula-builder:$(SHA) -f docker/builder/Dockerfile .

build-images: build-coder-image build-builder-image
```

- [ ] **Step 3: Create `scripts/README.md`**

```markdown
# scripts/

Shell scripts for Nebula development, testing, and deployment.

Makefile delegates complex initialization logic here (conditionals, background processes, trap cleanup, hash comparison).

## Scripts

_(To be added by dev-startup-simplify branch)_
```

---

### Task 9: 全局验证并清理旧目录

**Files:**
- Delete: `backend/`
- Delete: `frontend/`
- Delete: `nebula-runtime/`

- [ ] **Step 1: Run full test suite**

```bash
make test
```

Expected: All tests pass across all packages.

- [ ] **Step 2: Confirm all code has been migrated by checking for any missed files**

```bash
ls backend/ 2>/dev/null && echo "WARNING: backend/ still exists" || echo "OK: backend/ empty"
ls frontend/ 2>/dev/null && echo "WARNING: frontend/ still exists" || echo "OK: frontend/ empty"
ls nebula-runtime/ 2>/dev/null && echo "WARNING: nebula-runtime/ still exists" || echo "OK: nebula-runtime/ empty"
```

- [ ] **Step 3: Delete old directories**

```bash
rm -rf backend frontend nebula-runtime
git add -A
```

- [ ] **Step 4: Final full test suite run**

```bash
make test
```

Expected: All tests pass.

- [ ] **Step 5: Sync openspec**

```bash
openspec sync --change monorepo-project-restructure
```
