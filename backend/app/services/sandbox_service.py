import json, shutil, difflib
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings
from app.services.build_service import BuildService
from app.services.runtime_client import RuntimeClient

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MAX_SNAPSHOTS = 10


class SandboxService:

    @staticmethod
    def _project_dir(project_id: str) -> Path:
        return BASE_DIR / "projects" / project_id

    @staticmethod
    def _artifact_dir(project_id: str) -> Path:
        return SandboxService._project_dir(project_id) / "artifacts"

    @staticmethod
    def _sandbox_dir(project_id: str) -> Path:
        return SandboxService._project_dir(project_id) / "sandbox"

    @staticmethod
    def _snapshots_dir(project_id: str) -> Path:
        return SandboxService._project_dir(project_id) / "sandbox_snapshots"

    # ── 基础文件操作 ──────────────────────────────────────────

    @staticmethod
    def init_sandbox(project_id: str, artifact_version: str | None = None) -> dict:
        """从 Artifact 复制源码到沙箱工作区。

        如果 sandbox 目录已存在则跳过复制（保留已有修改）。
        如果指定了 artifact_version，从该版本的 Artifact 复制；
        否则尝试从 artifacts/ 中找最新的版本。
        """
        sandbox_dir = SandboxService._sandbox_dir(project_id)

        # 如果 sandbox 已存在，说明 PM 已经初始化过，直接返回元数据
        if sandbox_dir.exists() and (sandbox_dir / "src").exists():
            return SandboxService._sandbox_meta(project_id)

        # 确定来源 Artifact 版本
        if not artifact_version:
            versions = BuildService.list_artifacts(project_id)
            if not versions:
                raise ValueError("没有可用的 Artifact，请先构建项目")
            artifact_version = versions[-1]["version"]

        artifact_dir = SandboxService._artifact_dir(project_id) / artifact_version
        if not artifact_dir.exists():
            raise FileNotFoundError(f"Artifact {artifact_version} 不存在")

        # 创建 sandbox 目录结构
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        sandbox_src = sandbox_dir / "src"
        if sandbox_src.exists():
            shutil.rmtree(sandbox_src)

        # 尝试从 artifact.tar.gz 解压文件
        tar_path = artifact_dir / "artifact.tar.gz"
        if tar_path.exists():
            import tarfile
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(path=sandbox_dir, filter="data")
        else:
            # 回退：从 Artifact 目录的 src/、requirements.txt、Dockerfile 复制
            artifact_src = artifact_dir / "src"
            if artifact_src.exists():
                shutil.copytree(artifact_src, sandbox_src)
            for fname in ["requirements.txt", "Dockerfile"]:
                src_file = artifact_dir / fname
                dst_file = sandbox_dir / fname
                if src_file.exists() and not dst_file.exists():
                    shutil.copy2(src_file, dst_file)

        # 写入沙箱元信息
        meta = {
            "project_id": project_id,
            "artifact_version": artifact_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_count": 0,
        }
        with open(sandbox_dir / "sandbox.json", "w") as f:
            json.dump(meta, f, indent=2)

        return SandboxService._sandbox_meta(project_id)

    @staticmethod
    def _sandbox_meta(project_id: str) -> dict:
        """返回沙箱元数据。"""
        sandbox_dir = SandboxService._sandbox_dir(project_id)
        meta_path = sandbox_dir / "sandbox.json"
        if not meta_path.exists():
            return {"initialized": False}
        with open(meta_path) as f:
            meta = json.load(f)
        meta["initialized"] = True
        meta["file_count"] = SandboxService._count_files(sandbox_dir / "src")
        meta["modified_file_count"] = SandboxService._count_modified(project_id)
        return meta

    @staticmethod
    def get_sandbox_files(project_id: str) -> list[dict]:
        """递归扫描沙箱工作区的文件树。"""
        sandbox_src = SandboxService._sandbox_dir(project_id) / "src"
        if not sandbox_src.exists():
            return []
        return SandboxService._build_tree(project_id, sandbox_src)

    @staticmethod
    def _build_tree(project_id: str, path: Path, prefix: str = "") -> list[dict]:
        """递归构建文件树，每个节点返回 {name, path, type, children?, modified?}。"""
        items = []
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            rel_path = f"{prefix}/{entry.name}" if prefix else entry.name
            if entry.is_dir():
                children = SandboxService._build_tree(project_id, entry, rel_path)
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "type": "directory",
                    "children": children,
                })
            elif entry.is_file() and not entry.name.startswith("."):
                modified = SandboxService._is_modified(project_id, rel_path)
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "type": "file",
                    "modified": modified,
                })
        return items

    @staticmethod
    def get_file_content(project_id: str, file_path: str) -> str:
        """读取沙箱工作区文件内容。"""
        full_path = SandboxService._sandbox_dir(project_id) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件 {file_path} 不存在")
        if not full_path.is_file():
            raise ValueError(f"{file_path} 不是文件")
        if full_path.suffix in (".pyc", ".pyo"):
            raise ValueError(f"不支持读取二进制文件: {file_path}")
        try:
            return full_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, LookupError):
            raise ValueError(f"文件 {file_path} 不是文本文件")

    @staticmethod
    def save_file(project_id: str, file_path: str, content: str) -> dict:
        """保存文件到沙箱工作区。"""
        full_path = SandboxService._sandbox_dir(project_id) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {
            "path": file_path,
            "saved": True,
            "modified": SandboxService._is_modified(project_id, file_path),
        }

    # ── 修改状态跟踪 ──────────────────────────────────────────

    @staticmethod
    def _original_path(project_id: str) -> Path | None:
        """返回原始 Artifact 的目录路径（不含 src/，如 artifacts/v1/）。"""
        sandbox_dir = SandboxService._sandbox_dir(project_id)
        meta_path = sandbox_dir / "sandbox.json"
        if not meta_path.exists():
            return None
        with open(meta_path) as f:
            meta = json.load(f)
        version = meta.get("artifact_version", "")
        art_dir = SandboxService._artifact_dir(project_id) / version
        return art_dir if art_dir.exists() else None

    @staticmethod
    def _is_modified(project_id: str, rel_path: str) -> bool:
        """检查文件相对于原始 Artifact 是否有修改。
        rel_path 相对于 src/ 目录（由 _count_modified 传入）。
        """
        orig_dir = SandboxService._original_path(project_id)
        if not orig_dir:
            return False
        orig_file = orig_dir / "src" / rel_path
        if not orig_file.exists():
            return True  # 原始不存在 → 新增文件
        # 工作区文件在 sandbox/src/ 下
        work_file = SandboxService._sandbox_dir(project_id) / "src" / rel_path
        if not work_file.exists():
            return False
        try:
            return orig_file.read_text(encoding="utf-8") != work_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return False

    @staticmethod
    def _count_files(directory: Path) -> int:
        """统计目录中非隐藏文件的数量。"""
        if not directory.exists():
            return 0
        count = 0
        for p in directory.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                count += 1
        return count

    @staticmethod
    def _count_modified(project_id: str) -> int:
        """统计已修改的文件数量。"""
        sandbox_src = SandboxService._sandbox_dir(project_id) / "src"
        if not sandbox_src.exists():
            return 0
        count = 0
        for p in sandbox_src.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                rel = p.relative_to(sandbox_src)
                if SandboxService._is_modified(project_id, str(rel)):
                    count += 1
        return count

    # ── 快照管理 ──────────────────────────────────────────────

    @staticmethod
    def create_snapshot(project_id: str, description: str = "") -> dict:
        """创建当前工作区的快照（完整副本）。"""
        sandbox_dir = SandboxService._sandbox_dir(project_id)
        if not sandbox_dir.exists():
            raise FileNotFoundError("沙箱未初始化，请先调用 init")

        snapshots_dir = SandboxService._snapshots_dir(project_id)
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        snapshot_dir = snapshots_dir / timestamp
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
        shutil.copytree(sandbox_dir, snapshot_dir)

        # 写入元数据
        meta = {
            "snapshot_id": timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "description": description,
            "file_count": SandboxService._count_files(snapshot_dir / "src"),
        }
        with open(snapshot_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

        # 自动清理旧快照
        SandboxService._cleanup_old_snapshots(project_id)

        return meta

    @staticmethod
    def get_snapshots(project_id: str) -> list[dict]:
        """列出所有快照。"""
        snapshots_dir = SandboxService._snapshots_dir(project_id)
        if not snapshots_dir.exists():
            return []

        snapshots = []
        for entry in sorted(snapshots_dir.iterdir(), reverse=True):
            if entry.is_dir():
                meta_path = entry / "metadata.json"
                if meta_path.exists():
                    with open(meta_path) as f:
                        snapshots.append(json.load(f))
                else:
                    snapshots.append({
                        "snapshot_id": entry.name,
                        "created_at": "",
                        "description": "",
                    })
        return snapshots

    @staticmethod
    def restore_from_snapshot(project_id: str, snapshot_id: str) -> dict:
        """从快照恢复工作区。"""
        sandbox_dir = SandboxService._sandbox_dir(project_id)
        snapshot_dir = SandboxService._snapshots_dir(project_id) / snapshot_id
        if not snapshot_dir.exists():
            raise FileNotFoundError(f"快照 {snapshot_id} 不存在")

        # 删除当前工作区，从快照完整复制
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir)
        shutil.copytree(snapshot_dir, sandbox_dir)

        meta = {
            "restored_from": snapshot_id,
            "restored_at": datetime.now(timezone.utc).isoformat(),
        }
        return meta

    @staticmethod
    def _cleanup_old_snapshots(project_id: str):
        """保留最近 MAX_SNAPSHOTS 个快照，删除更旧的。"""
        snapshots_dir = SandboxService._snapshots_dir(project_id)
        if not snapshots_dir.exists():
            return
        snapshots = sorted(snapshots_dir.iterdir())
        while len(snapshots) > MAX_SNAPSHOTS:
            oldest = snapshots.pop(0)
            if oldest.is_dir():
                shutil.rmtree(oldest)

    # ── Diff 计算 ─────────────────────────────────────────────

    @staticmethod
    def get_diff(project_id: str, file_path: str) -> dict:
        """计算文件的修改 diff（当前工作区 vs 原始 Artifact）。"""
        orig_dir = SandboxService._original_path(project_id)
        sandbox_dir = SandboxService._sandbox_dir(project_id)

        work_file = sandbox_dir / file_path
        if not work_file.exists():
            raise FileNotFoundError(f"文件 {file_path} 不存在于工作区")

        orig_content = ""
        if orig_dir:
            orig_file = orig_dir / file_path
            if orig_file.exists():
                try:
                    orig_content = orig_file.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    orig_content = ""

        try:
            work_content = work_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            raise ValueError(f"文件 {file_path} 不是文本文件")

        if orig_content == work_content:
            return {"path": file_path, "has_diff": False, "diff": "", "summary": "无修改"}

        diff_lines = list(difflib.unified_diff(
            orig_content.splitlines(keepends=True),
            work_content.splitlines(keepends=True),
            fromfile=f"original/{file_path}",
            tofile=f"modified/{file_path}",
        ))

        # 统计变更
        additions = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        removals = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

        return {
            "path": file_path,
            "has_diff": True,
            "diff": "".join(diff_lines),
            "summary": f"+{additions}/-{removals} 行变更",
            "additions": additions,
            "removals": removals,
        }

    @staticmethod
    def get_original_content(project_id: str, file_path: str) -> str:
        """从原始 Artifact 读取文件的基线版本。"""
        orig_dir = SandboxService._original_path(project_id)
        if not orig_dir:
            return ""
        orig_file = orig_dir / file_path
        if not orig_file.exists():
            raise FileNotFoundError(f"原始 Artifact 中不存在文件 {file_path}")
        try:
            return orig_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            raise ValueError(f"文件 {file_path} 不是文本文件")

    # ── 恢复原始 ──────────────────────────────────────────────

    @staticmethod
    def restore_original(project_id: str, file_path: str | None = None) -> dict:
        """从原始 Artifact 恢复文件到沙箱。

        如果指定了 file_path，只恢复该文件；
        否则恢复整个沙箱工作区（清空 src/ 后重新从 Artifact 复制）。
        """
        sandbox_dir = SandboxService._sandbox_dir(project_id)
        if not sandbox_dir.exists():
            raise FileNotFoundError("沙箱未初始化，请先调用 init")

        if file_path:
            # 恢复单个文件
            full_path = sandbox_dir / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"文件 {file_path} 不存在于工作区")

            orig_content = SandboxService.get_original_content(project_id, file_path)
            full_path.write_text(orig_content, encoding="utf-8")
            return {"path": file_path, "restored": True}

        # 恢复全部：重新从 Artifact 复制 src/
        orig_dir = SandboxService._original_path(project_id)
        if not orig_dir:
            raise FileNotFoundError("找不到原始 Artifact，无法恢复")

        sandbox_src = sandbox_dir / "src"
        if sandbox_src.exists():
            shutil.rmtree(sandbox_src)

        # 优先从 tarball 解压，回退到目录复制
        tar_path = orig_dir / "artifact.tar.gz"
        if tar_path.exists():
            import tarfile
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(path=sandbox_dir, filter="data")
        else:
            artifact_src = orig_dir / "src"
            if artifact_src.exists():
                shutil.copytree(artifact_src, sandbox_src)

        # 恢复顶级文件（如果 tarball 未包含则单独复制）
        for fname in ["requirements.txt", "Dockerfile"]:
            src_file = orig_dir / fname
            dst_file = sandbox_dir / fname
            if src_file.exists() and not dst_file.exists():
                shutil.copy2(src_file, dst_file)

        return {"restored": True, "restored_all": True}

    # ── 重建触发 ──────────────────────────────────────────────

    @staticmethod
    def trigger_rebuild(project_id: str, description: str = "", async_build: bool = False) -> dict:
        """触发重建流程：
        1. 创建快照
        2. 调用 BuildService 从沙箱目录构建
        3. 推送到 runtime

        如果 async_build=True，在后台线程运行构建并返回启动状态；
        否则同步等待构建完成。
        """
        # 1. 创建自动快照
        snapshot = SandboxService.create_snapshot(project_id, description or "重建前自动快照")

        sandbox_dir = SandboxService._sandbox_dir(project_id)

        if async_build:
            # 异步构建：后台线程运行，前端轮询状态
            build_result = BuildService.start_async_build(project_id)
            result = {
                "status": build_result.get("status", "started"),
                "message": build_result.get("message", "构建已启动"),
                "snapshot_id": snapshot["snapshot_id"],
                "async": True,
            }
            return result

        # 2. 同步构建：等待完成
        result = BuildService.build(project_id, source_dir=str(sandbox_dir))

        # 3. 更新沙箱元数据的 artifact_version
        if result.get("status") == "success":
            meta_path = sandbox_dir / "sandbox.json"
            if meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)
                meta["last_rebuild_version"] = result.get("artifact_version", "")
                meta["last_rebuild_at"] = datetime.now(timezone.utc).isoformat()
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)

        result["snapshot_id"] = snapshot["snapshot_id"]
        return result
