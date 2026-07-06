"""SandboxService 单元测试"""
from unittest.mock import patch, MagicMock
import json, os, shutil
from pathlib import Path

import pytest

from app.services.sandbox_service import SandboxService
from app.services.build_service import BuildService

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def clean_sandbox_and_artifacts():
    """每次测试前清理 sandbox 和 artifacts 目录。"""
    projects_dir = BASE_DIR / "projects"
    if projects_dir.exists():
        for proj_dir in projects_dir.iterdir():
            if proj_dir.is_dir():
                # 清理 sandbox 和 artifacts
                for sub in ["sandbox", "sandbox_snapshots", "artifacts"]:
                    p = proj_dir / sub
                    if p.exists():
                        shutil.rmtree(p)
    yield


def _create_test_artifact(project_id: str, version: str = "v1"):
    """创建一个测试用的 Artifact。"""
    artifact_dir = BASE_DIR / "projects" / project_id / "artifacts" / version
    src_dir = artifact_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # 创建一些测试源文件
    (src_dir / "main.py").write_text("print('hello world')\n", encoding="utf-8")
    (src_dir / "utils.py").write_text("def helper():\n    return 42\n", encoding="utf-8")
    (src_dir / "models").mkdir(exist_ok=True)
    (src_dir / "models" / "user.py").write_text("class User:\n    pass\n", encoding="utf-8")

    # 顶级文件
    (artifact_dir / "requirements.txt").write_text("fastapi==0.100.0\n", encoding="utf-8")
    (artifact_dir / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")

    # manifest
    manifest = {
        "version": version,
        "created_at": "2026-07-06T00:00:00Z",
        "entry": "src/main.py",
        "dependencies": ["fastapi==0.100.0"],
    }
    with open(artifact_dir / "manifest.json", "w") as f:
        json.dump(manifest, f)

    return artifact_dir


class TestInitSandbox:
    def test_init_sandbox_creates_workspace(self):
        """init_sandbox 从 Artifact 复制源码到沙箱工作区。"""
        project_id = "test-init"
        _create_test_artifact(project_id)
        result = SandboxService.init_sandbox(project_id)

        assert result["initialized"] is True
        assert result["file_count"] == 3  # main.py, utils.py, models/user.py
        sandbox_dir = BASE_DIR / "projects" / project_id / "sandbox"
        assert (sandbox_dir / "src" / "main.py").exists()
        assert (sandbox_dir / "src" / "utils.py").exists()
        assert (sandbox_dir / "src" / "models" / "user.py").exists()
        assert (sandbox_dir / "requirements.txt").exists()
        assert (sandbox_dir / "Dockerfile").exists()

    def test_init_sandbox_with_specific_version(self):
        """可以指定从特定 Artifact 版本初始化。"""
        project_id = "test-init-v"
        _create_test_artifact(project_id, "v1")
        _create_test_artifact(project_id, "v2")
        # 修改 v2 的 main.py
        v2_src = BASE_DIR / "projects" / project_id / "artifacts" / "v2" / "src"
        (v2_src / "main.py").write_text("print('v2')\n", encoding="utf-8")

        result = SandboxService.init_sandbox(project_id, "v1")
        sandbox_dir = BASE_DIR / "projects" / project_id / "sandbox"
        content = (sandbox_dir / "src" / "main.py").read_text()
        assert "hello" in content  # v1 的内容

    def test_init_sandbox_idempotent(self):
        """已初始化的沙箱再次 init 不会覆盖已有修改。"""
        project_id = "test-idempotent"
        _create_test_artifact(project_id)

        # 第一次初始化
        SandboxService.init_sandbox(project_id)
        sandbox_dir = BASE_DIR / "projects" / project_id / "sandbox"

        # 修改文件
        (sandbox_dir / "src" / "main.py").write_text("# modified\n", encoding="utf-8")

        # 第二次 init 应保留修改
        SandboxService.init_sandbox(project_id)
        assert (sandbox_dir / "src" / "main.py").read_text() == "# modified\n"

    def test_init_sandbox_no_artifact(self):
        """没有 Artifact 时抛出 ValueError。"""
        with pytest.raises(ValueError, match="没有可用的 Artifact"):
            SandboxService.init_sandbox("nonexistent-project")


class TestGetSandboxFiles:
    def test_get_sandbox_files_returns_tree(self):
        """文件树返回所有文件。"""
        project_id = "test-tree"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        files = SandboxService.get_sandbox_files(project_id)
        assert len(files) > 0

        # 找到 src/main.py
        paths = _flatten_paths(files)
        assert "main.py" in paths
        assert "utils.py" in paths
        # models 应该是目录
        models = next((f for f in files if f["name"] == "models"), None)
        assert models is not None
        assert models["type"] == "directory"

    def test_get_sandbox_files_not_initialized(self):
        """未初始化时返回空列表。"""
        files = SandboxService.get_sandbox_files("no-init")
        assert files == []


class TestFileContent:
    def test_get_file_content(self):
        """读取工作区文件内容。"""
        project_id = "test-read"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        content = SandboxService.get_file_content(project_id, "src/main.py")
        assert "print" in content

    def test_get_file_nonexistent(self):
        """读取不存在的文件抛出 FileNotFoundError。"""
        project_id = "test-read-none"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        with pytest.raises(FileNotFoundError):
            SandboxService.get_file_content(project_id, "src/nonexistent.py")

    def test_save_file(self):
        """保存文件到工作区。"""
        project_id = "test-save"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        SandboxService.save_file(project_id, "src/main.py", "# modified content\n")
        content = SandboxService.get_file_content(project_id, "src/main.py")
        assert content == "# modified content\n"


class TestDiffAndModifications:
    def test_is_modified_after_edit(self):
        """修改文件后 is_modified 返回 True。"""
        project_id = "test-diff"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        # 初始不应有修改
        assert SandboxService._count_modified(project_id) == 0

        # 修改文件
        SandboxService.save_file(project_id, "src/main.py", "# changed\n")
        assert SandboxService._count_modified(project_id) == 1

    def test_get_diff_shows_changes(self):
        """get_diff 返回行级别的修改。"""
        project_id = "test-diff-show"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        SandboxService.save_file(project_id, "src/main.py",
                                  "print('modified')\nprint('new line')\n")

        diff = SandboxService.get_diff(project_id, "src/main.py")
        assert diff["has_diff"] is True
        assert diff["additions"] >= 1
        assert "summary" in diff

    def test_get_diff_no_changes(self):
        """未修改的文件 diff 显示无修改。"""
        project_id = "test-diff-none"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        diff = SandboxService.get_diff(project_id, "src/main.py")
        assert diff["has_diff"] is False


class TestSnapshots:
    def test_create_snapshot(self):
        """创建快照保存当前工作区状态。"""
        project_id = "test-snap"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        # 修改并保存
        SandboxService.save_file(project_id, "src/main.py", "# snapshot test\n")

        # 创建快照
        snap = SandboxService.create_snapshot(project_id, "测试快照")
        assert snap["snapshot_id"] is not None
        assert snap["description"] == "测试快照"

    def test_restore_snapshot(self):
        """从快照恢复工作区。"""
        project_id = "test-restore"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        # 修改并保存
        SandboxService.save_file(project_id, "src/main.py", "# modified\n")

        # 创建快照
        snap = SandboxService.create_snapshot(project_id, "修改后")

        # 再次修改
        SandboxService.save_file(project_id, "src/main.py", "# further modified\n")

        # 从快照恢复
        SandboxService.restore_from_snapshot(project_id, snap["snapshot_id"])

        content = SandboxService.get_file_content(project_id, "src/main.py")
        assert content == "# modified\n"

    def test_get_snapshots(self):
        """get_snapshots 列出所有快照。"""
        project_id = "test-list-snaps"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        SandboxService.create_snapshot(project_id, "快照1")
        SandboxService.create_snapshot(project_id, "快照2")

        snaps = SandboxService.get_snapshots(project_id)
        assert len(snaps) == 2


class TestRestoreOriginal:
    def test_restore_original_single_file(self):
        """恢复单个文件到原始 Artifact 版本。"""
        project_id = "test-restore-single"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        # 修改文件
        SandboxService.save_file(project_id, "src/main.py", "# modified\n")
        assert "modified" in SandboxService.get_file_content(project_id, "src/main.py")

        # 恢复单个文件
        SandboxService.restore_original(project_id, "src/main.py")
        content = SandboxService.get_file_content(project_id, "src/main.py")
        assert "hello" in content  # 回到原始内容

    def test_restore_original_all_files(self):
        """恢复全部文件到原始 Artifact 版本。"""
        project_id = "test-restore-all"
        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        # 修改多个文件
        SandboxService.save_file(project_id, "src/main.py", "# modified\n")
        SandboxService.save_file(project_id, "src/utils.py", "# modified utils\n")

        # 恢复全部
        SandboxService.restore_original(project_id)
        main_content = SandboxService.get_file_content(project_id, "src/main.py")
        utils_content = SandboxService.get_file_content(project_id, "src/utils.py")
        assert "hello" in main_content
        assert "def helper" in utils_content


class TestRebuild:
    @pytest.fixture(autouse=True)
    def cleanup_build_state(self):
        """每次测试清理 build state。"""
        from app.services.build_service import _build_states
        _build_states.clear()

    def test_trigger_rebuild_creates_snapshot(self):
        """trigger_rebuild 会自动创建快照。"""
        project_id = "test-rebuild"
        # 创建足够的 Artifact 文件结构以便测试通过
        project_dir = BASE_DIR / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        (project_dir / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (project_dir / "requirements.txt").write_text("\n", encoding="utf-8")
        (project_dir / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")

        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        # 修改文件
        SandboxService.save_file(project_id, "src/main.py", "# rebuild test\n")

        # 触发重建
        result = SandboxService.trigger_rebuild(project_id, "测试重建")

        # 应创建了快照
        assert "snapshot_id" in result
        snaps = SandboxService.get_snapshots(project_id)
        assert len(snaps) >= 1

        # 清理
        shutil.rmtree(project_dir)

    def test_rebuild_works_without_modification(self):
        """没有修改时重建也应该正常进行（含测试）。"""
        project_id = "test-rebuild-no-change"
        project_dir = BASE_DIR / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        (project_dir / "src" / "main.py").write_text("print('test')\n", encoding="utf-8")
        # 添加测试文件，让 pytest 能通过
        tests_dir = project_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / "test_main.py").write_text(
            "def test_placeholder():\n    assert True\n", encoding="utf-8"
        )
        (project_dir / "requirements.txt").write_text("pytest\n", encoding="utf-8")
        (project_dir / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")

        _create_test_artifact(project_id)
        SandboxService.init_sandbox(project_id)

        # 在沙箱中添加测试文件，让构建管道的 pytest 能通过
        sandbox_dir = BASE_DIR / "projects" / project_id / "sandbox"
        test_dir = sandbox_dir / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "__init__.py").write_text("", encoding="utf-8")
        (test_dir / "test_sandbox.py").write_text(
            "def test_placeholder():\n    assert True\n", encoding="utf-8"
        )

        from app.services.coder_backend import BuildResult
        mock_backend = MagicMock()
        mock_backend.execute_build.return_value = BuildResult(
            status="success",
            artifact_path=str(sandbox_dir / "artifacts" / "v2" / "artifact.tar.gz"),
            version="v2",
            message="mock build completed",
        )
        with patch("app.services.build_service.create_backend", return_value=mock_backend):
            result = SandboxService.trigger_rebuild(project_id)
        assert "snapshot_id" in result
        assert result.get("status") == "success" or result.get("status") == "testing"

        shutil.rmtree(project_dir)


def _flatten_paths(files: list[dict]) -> list[str]:
    """展平文件树节点为路径列表。"""
    paths = []
    for f in files:
        if f["type"] == "file":
            paths.append(f["name"])
        if "children" in f:
            paths.extend(_flatten_paths(f["children"]))
    return paths
