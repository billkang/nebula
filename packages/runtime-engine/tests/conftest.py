import shutil
from pathlib import Path

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def clean_artifacts():
    """Clean the artifacts directory before each test for isolation."""
    artifacts_dir = Path(settings.artifacts_dir)
    if artifacts_dir.exists():
        for item in artifacts_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
    yield
