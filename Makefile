DOCKER_BUILDKIT ?= 1
export DOCKER_BUILDKIT

.PHONY: build-coder-image build-builder-image build-images

SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo "dev")

build-coder-image:
	DOCKER_BUILDKIT=1 docker build -t nebula-coder:latest -t nebula-coder:$(SHA) -f docker/coder/Dockerfile .

build-builder-image:
	DOCKER_BUILDKIT=1 docker build -t nebula-builder:latest -t nebula-builder:$(SHA) -f docker/builder/Dockerfile .

build-images: build-coder-image build-builder-image
