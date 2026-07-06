import subprocess, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

MAX_RETRIES = 2
RETRY_DELAY_S = 5

# dict-based 状态存储，按 project_id 隔离
_exec_states: dict[str, dict] = {}


class ExecutorService:

    @staticmethod
    def _state(project_id: str) -> dict:
        if project_id not in _exec_states:
            _exec_states[project_id] = {"status": "idle", "message": None}
        return _exec_states[project_id]

    @staticmethod
    def check_prerequisites() -> tuple[bool, str]:
        """检查 Claude Code 是否可用"""
        try:
            result = subprocess.run(["claude", "--version"],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Claude Code CLI 无响应"
        except FileNotFoundError:
            return False, "未找到 Claude Code CLI，请安装：npm install -g @anthropic-ai/claude-code"
        except subprocess.TimeoutExpired:
            return False, "Claude Code 检查超时"

    @staticmethod
    def get_status(project_id: str) -> dict:
        st = ExecutorService._state(project_id)
        return {"status": st["status"], "message": st["message"]}

    @staticmethod
    def execute(project_id: str) -> dict:
        st = ExecutorService._state(project_id)
        available, msg = ExecutorService.check_prerequisites()
        if not available:
            st["status"] = "failed"
            st["message"] = msg
            return ExecutorService.get_status(project_id)

        project_dir = BASE_DIR / "projects" / project_id / "src"
        project_dir.mkdir(parents=True, exist_ok=True)

        st["status"] = "running"
        st["message"] = "编码执行中..."

        instruction = "请根据 specs 和 tasks 实现功能代码。"

        last_error = ""
        for attempt in range(1, MAX_RETRIES + 2):  # 首次 + MAX_RETRIES 次重试
            try:
                result = subprocess.run(
                    ["claude", "code", "--prompt", instruction],
                    capture_output=True, text=True,
                    cwd=str(project_dir), timeout=3600,
                )
                if result.returncode == 0:
                    st["status"] = "success"
                    st["message"] = "编码执行完成"
                    return ExecutorService.get_status(project_id)

                last_error = result.stderr[:500]
                if attempt < MAX_RETRIES + 1:
                    st["message"] = f"编码执行失败，{RETRY_DELAY_S}秒后重试 ({attempt}/{MAX_RETRIES})..."
                    time.sleep(RETRY_DELAY_S)
                else:
                    st["message"] = f"编码执行失败 (已重试{MAX_RETRIES}次): {last_error}"
            except subprocess.TimeoutExpired:
                last_error = "编码执行超时（超过1小时）"
                if attempt < MAX_RETRIES + 1:
                    st["message"] = f"编码执行超时，{RETRY_DELAY_S}秒后重试 ({attempt}/{MAX_RETRIES})..."
                    time.sleep(RETRY_DELAY_S)
                else:
                    st["message"] = last_error

        st["status"] = "failed"
        return ExecutorService.get_status(project_id)
