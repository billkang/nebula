FROM python:3.12-alpine

# Install system + Python dependencies
RUN apk add --no-cache git
RUN pip install --no-cache-dir pytest==9.1.1 ruff==0.15.20 pytest-cov==7.1.0

# Create non-root user and set up entrypoint
RUN adduser -D nebula
COPY docker/builder/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER nebula
WORKDIR /workspace

ENTRYPOINT ["/entrypoint.sh"]
