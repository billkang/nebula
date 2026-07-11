import subprocess
import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class DocService:
    """项目级 SDD 文档服务。

    每个项目在 projects/{username}-{change_name}/ 下有专属 openspec 工作区：
      - openspec/                     — openspec 工作区（openspec init 初始化）
      - openspec/changes/{change}/    — 每个需求的 SDD 文档
      - conversation_context.md       — Agent 对话上下文
    """

    @staticmethod
    def _get_project_info(project_id: int, db: Session) -> tuple[str, str]:
        """查询 project_id 对应的 username 和 change_name。"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.change_name:
            raise ValueError(f"Project {project_id} not found or missing change_name")
        user = db.query(User).filter(User.id == project.owner_id).first()
        if not user:
            raise ValueError(f"Owner not found for project {project_id}")
        return user.username, project.change_name

    @staticmethod
    def get_project_dir(project_id: int, db: Session) -> str:
        """返回项目目录路径 projects/{username}-{change_name}/。"""
        username, change_name = DocService._get_project_info(project_id, db)
        return str(BASE_DIR / "projects" / f"{username}-{change_name}")

    @staticmethod
    def list_docs(project_id: int, db: Session) -> list[dict]:
        """列出项目 openspec 工作区中的所有 change 及其 artifact 状态。"""
        project_dir = Path(DocService.get_project_dir(project_id, db))
        changes_dir = project_dir / "openspec" / "changes"
        if not changes_dir.exists():
            return []

        result = []
        for change_dir in sorted(changes_dir.iterdir()):
            if not change_dir.is_dir() or change_dir.name == "archive":
                continue
            artifacts = [
                {"type": "proposal", "exists": (change_dir / "proposal.md").is_file()},
                {"type": "specs", "exists": (change_dir / "specs").is_dir()},
                {"type": "design", "exists": (change_dir / "design.md").is_file()},
                {"type": "tasks", "exists": (change_dir / "tasks.md").is_file()},
            ]
            result.append({"change": change_dir.name, "artifacts": artifacts})
        return result

    @staticmethod
    def generate_docs(project_id: int, db: Session,
                      req_summary: str | None = None,
                      out_of_scope: list[str] | None = None) -> dict:
        """生成 SDD 文档到项目 openspec 工作区。

        流程：
          1. 写入 conversation_context.md 到项目根目录
          2. 创建/使用 openspec change
          3. 运行 openspec instructions 生成各 artifact
        """
        username, change_name = DocService._get_project_info(project_id, db)
        project_dir = Path(DocService.get_project_dir(project_id, db))
        change_name_full = f"{username}-{change_name}-init"

        # 1. 写入对话上下文到项目根目录
        context_path = project_dir / "conversation_context.md"
        with open(context_path, "w", encoding="utf-8") as f:
            if req_summary:
                f.write(f"## 需求摘要（来自 Agent 对话）\n\n{req_summary}\n\n")
            if out_of_scope:
                items = "\n".join(f"- {item}" for item in out_of_scope)
                f.write(f"## Out of Scope\n\n{items}\n\n")

        # 2. 确保 change 存在
        changes_dir = project_dir / "openspec" / "changes"
        change_dir = changes_dir / change_name_full
        if not change_dir.exists():
            result = subprocess.run(
                ["openspec", "new", "change", change_name_full],
                capture_output=True, text=True, cwd=str(project_dir),
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                return {"success": False,
                        "message": f"创建 openspec change 失败: {stderr}"}

        # 3. 为每个 artifact 运行 openspec instructions
        for cmd in ["proposal", "specs", "design", "tasks"]:
            result = subprocess.run(
                ["openspec", "instructions", cmd, "--change", change_name_full, "--json"],
                capture_output=True, text=True, cwd=str(project_dir),
            )
            if result.returncode != 0:
                return {"success": False,
                        "message": f"{cmd} 生成失败: {result.stderr.strip()}"}

        return {"success": True, "message": "文档生成完成"}

    @staticmethod
    def get_doc(project_id: int, doc_type: str, db: Session) -> str | None:
        """从项目 openspec 工作区读取指定类型的 SDD 文档内容。"""
        project_dir = Path(DocService.get_project_dir(project_id, db))
        # 找到最新的 change
        changes_dir = project_dir / "openspec" / "changes"
        if not changes_dir.exists():
            return None
        changes = sorted(
            [d for d in changes_dir.iterdir() if d.is_dir() and d.name != "archive"],
            reverse=True,
        )
        if not changes:
            return None
        latest_change = changes[0]

        path_map = {
            "proposal": "proposal.md",
            "design": "design.md",
            "tasks": "tasks.md",
        }
        if doc_type in path_map:
            path = latest_change / path_map[doc_type]
            if path.is_file():
                return path.read_text(encoding="utf-8")
        elif doc_type == "specs":
            specs_dir = latest_change / "specs"
            if specs_dir.is_dir():
                content = ""
                for fname in sorted(specs_dir.iterdir()):
                    if fname.suffix == ".md":
                        content += f"## {fname.stem}\n\n{fname.read_text(encoding='utf-8')}\n\n"
                return content
        return None
