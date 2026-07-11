"""Project name → change_name 翻译功能。

提供中文/英文项目名的 LLM 翻译，输出 kebab-case 格式的 change_name。
"""

import logging
import re
from typing import NoReturn

from app.llm import get_llm_provider

logger = logging.getLogger(__name__)

# kebab-case 正则：小写字母开头，允许小写字母/数字/中横线
_KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

_MAX_RETRIES = 1  # 首次调用 + 1 次重试 = 最多 2 次


def is_valid_kebab_case(name: str) -> bool:
    """检查字符串是否为合法 kebab-case。"""
    return bool(_KEBAB_RE.match(name))


def translate_change_name(project_name: str, provider=None) -> str:
    """将项目名称翻译为 kebab-case change_name。

    流程：
      1. 调用 LLM 翻译
      2. 校验结果格式（kebab-case regex）
      3. 格式非法时重试一次
      4. 重试后仍非法 → 抛 ValueError

    Args:
        project_name: 项目名称（中文/英文等）
        provider: 可选的 LLMProvider 实例，不传则使用全局单例

    Returns:
        合法的 kebab-case change_name

    Raises:
        ValueError: 翻译结果经重试后仍不合法
    """
    if provider is None:
        provider = get_llm_provider()

    system_prompt = (
        "You are a naming assistant. Translate the given project name "
        "into an English kebab-case identifier.\n\n"
        "Rules:\n"
        "- Output ONLY the kebab-case result, nothing else.\n"
        "- Use lowercase letters, digits, and hyphens only.\n"
        "- Separate words with hyphens.\n"
        "- NO spaces, underscores, or special characters.\n"
        "- NO pinyin — always translate to English words.\n\n"
        "Examples:\n"
        '  "旅游助手" → "travel-assistant"\n'
        '  "E-commerce Dashboard" → "e-commerce-dashboard"\n'
        '  "数据分析平台" → "data-analytics-platform"\n'
        '  "用户管理系统" → "user-management-system"'
    )

    last_result = ""
    for attempt in range(_MAX_RETRIES + 1):
        if attempt > 0:
            logger.info("Retrying translation for '%s' (attempt %d)", project_name, attempt + 1)

        result = provider.chat(
            messages=[{"role": "user", "content": project_name}],
            system_prompt=system_prompt,
            temperature=0.1,  # 低温度确保一致性
            max_tokens=128,
        )
        result = result.strip()

        if is_valid_kebab_case(result):
            logger.info(
                "Translated project name '%s' → '%s'",
                project_name, result,
            )
            return result

        last_result = result
        logger.warning(
            "Invalid kebab-case from LLM for '%s': '%s'",
            project_name, result,
        )

    raise ValueError(
        f"翻译结果不合法：'{last_result if last_result else '(empty)'}' "
        f"（项目名：'{project_name}'）"
    )
