#!/bin/bash
# reef-scope pre-commit hook
# 由 `reef scope setup` 安装到 .git/hooks/pre-commit
# 在 git commit 时自动检查分支范围

set -euo pipefail

# 获取 DeepFlow 插件路径
DEEPFLOW_PLUGIN_ROOT="${DEEPFLOW_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"

# 如果无法获取插件根目录，尝试从 .git 上级查找
if [ -z "$DEEPFLOW_PLUGIN_ROOT" ]; then
  PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$PROJECT_ROOT" ]; then
    # 检查是否在 reef 的安装路径中
    if [ -f "${PROJECT_ROOT}/.deepflow/scope-config.json" ]; then
      DEEPFLOW_PLUGIN_ROOT="$PROJECT_ROOT"
    fi
  fi
fi

# 如果还是找不到 reef 路径，跳过检查
if [ ! -f "${DEEPFLOW_PLUGIN_ROOT}/hooks/reef-scope-gate.sh" ]; then
  exit 0
fi

# 执行门禁检查
bash "${DEEPFLOW_PLUGIN_ROOT}/hooks/reef-scope-gate.sh" "$@"
