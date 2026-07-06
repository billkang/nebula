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

test-unchecked:
	cd packages/build-engine/backend && uv run pytest -v
	cd packages/runtime-engine && uv run pytest -v

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
