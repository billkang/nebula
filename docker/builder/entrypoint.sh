#!/bin/sh
# Runs inside the build container: install deps -> test -> package
# Note: intentionally NOT using set -e; pytest exit code 5 (no tests)
# must be handled explicitly as a non-fatal result.

PROJECT_DIR="${1:-/workspace}"
cd "$PROJECT_DIR"

echo "=== Installing dependencies ==="
if [ -f requirements.txt ]; then
    pip install --no-cache-dir -r requirements.txt
fi

echo "=== Running tests ==="
python -m pytest --tb=short -q 2>&1
RC=$?
if [ $RC -ne 0 ] && [ $RC -ne 5 ]; then
    echo "TESTS_FAILED (exit code: $RC)"
    exit 1
fi
echo "=== Tests passed (exit code: $RC) ==="

echo "=== Packaging artifact ==="
ARTIFACT_DIR="$PROJECT_DIR/artifacts"
mkdir -p "$ARTIFACT_DIR"

VERSION="${VERSION:-${2:-v1}}"
MANIFEST="$ARTIFACT_DIR/manifest.json"

cat > "$MANIFEST" <<MEOF
{
  "version": "$VERSION",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "entry": "src/main.py",
  "dependencies": []
}
MEOF

if [ -f requirements.txt ]; then
    python3 -c "
import json
with open('$MANIFEST') as f:
    m = json.load(f)
with open('requirements.txt') as f:
    m['dependencies'] = [l.strip() for l in f if l.strip() and not l.startswith('#')]
with open('$MANIFEST', 'w') as f:
    json.dump(m, f, indent=2)
"
fi

tar czf "$ARTIFACT_DIR/artifact.tar.gz" \
    -C "$PROJECT_DIR" src requirements.txt Dockerfile manifest.json 2>/dev/null || \
tar czf "$ARTIFACT_DIR/artifact.tar.gz" \
    -C "$PROJECT_DIR" src requirements.txt Dockerfile manifest.json

echo "BUILD_SUCCESS"
