FROM nikolaik/python-nodejs:python3.12-nodejs22

RUN pip install --no-cache-dir pytest==9.1.1 ruff==0.15.20 pytest-cov==7.1.0
RUN npm install -g @anthropic-ai/claude-code@2.1.201

# Create non-root user
RUN adduser --disabled-password --gecos "" nebula
USER nebula

WORKDIR /workspace

CMD ["tail", "-f", "/dev/null"]
