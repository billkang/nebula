import subprocess
import os
from pathlib import Path

CHANGE_NAME = "mvp-scope-planning"
CHANGE_DIR = f"openspec/changes/{CHANGE_NAME}"
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class DocService:
    @staticmethod
    def get_change_dir() -> str:
        return str(BASE_DIR / CHANGE_DIR)

    @staticmethod
    def generate_docs(req_summary: str | None = None,
                      out_of_scope: list[str] | None = None) -> dict:
        # 将 Agent 对话上下文写入临时文件，供 openspec 指令引用
        context_dir = os.path.join(BASE_DIR, CHANGE_DIR, ".agent_context")
        os.makedirs(context_dir, exist_ok=True)
        context_path = os.path.join(context_dir, "conversation_context.md")
        with open(context_path, "w") as f:
            if req_summary:
                f.write(f"## 需求摘要（来自 Agent 对话）\n\n{req_summary}\n\n")
            if out_of_scope:
                items = "\n".join(f"- {item}" for item in out_of_scope)
                f.write(f"## Out of Scope\n\n{items}\n\n")

        for cmd in ["proposal", "specs", "design", "tasks"]:
            result = subprocess.run(
                ["openspec", "instructions", cmd, "--change", CHANGE_NAME, "--json"],
                capture_output=True, text=True, cwd=BASE_DIR,
            )
            if result.returncode != 0:
                return {"success": False,
                        "message": f"{cmd} 生成失败: {result.stderr}"}

        return {"success": True, "message": "文档生成完成"}

    @staticmethod
    def list_docs() -> list[dict]:
        change_dir = DocService.get_change_dir()
        docs = [
            {"type": "proposal", "path": os.path.join(change_dir, "proposal.md"),
             "exists": os.path.exists(os.path.join(change_dir, "proposal.md"))},
            {"type": "specs", "path": os.path.join(change_dir, "specs"),
             "exists": os.path.isdir(os.path.join(change_dir, "specs"))},
            {"type": "design", "path": os.path.join(change_dir, "design.md"),
             "exists": os.path.exists(os.path.join(change_dir, "design.md"))},
            {"type": "tasks", "path": os.path.join(change_dir, "tasks.md"),
             "exists": os.path.exists(os.path.join(change_dir, "tasks.md"))},
        ]
        return docs

    @staticmethod
    def get_doc(doc_type: str) -> str | None:
        change_dir = DocService.get_change_dir()
        path_map = {
            "proposal": "proposal.md",
            "design": "design.md",
            "tasks": "tasks.md",
        }
        if doc_type in path_map:
            path = os.path.join(change_dir, path_map[doc_type])
            if os.path.isfile(path):
                with open(path) as f:
                    return f.read()
        elif doc_type == "specs":
            specs_dir = os.path.join(change_dir, "specs")
            if os.path.isdir(specs_dir):
                content = ""
                for root, _, fnames in os.walk(specs_dir):
                    for fname in sorted(fnames):
                        if fname.endswith(".md"):
                            filepath = os.path.join(root, fname)
                            with open(filepath) as f:
                                content += f"## {os.path.relpath(filepath, specs_dir)}\n\n{f.read()}\n\n"
                return content
        return None
