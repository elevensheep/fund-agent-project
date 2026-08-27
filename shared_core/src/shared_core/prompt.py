import json
import re
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .logger import logger

def load_prompt(file_path: Union[Path, str], key: Union[str, None] = None, default: Any = "") -> Any:
    """
    Load a prompt or template from a YAML file.
    
    Args:
        file_path: Path to the YAML file.
        key: If provided, returns the value for this specific key from the loaded YAML dict.
             If None, returns the entire loaded YAML object.
        default: Default value to return if loading fails or key is missing.
             
    Returns:
        The loaded prompt/template, or the default value on error.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)
            
        if key is not None:
            if isinstance(prompt_data, dict):
                return prompt_data.get(key, default)
            return default
            
        return prompt_data if prompt_data is not None else default
    except Exception as e:
        logger.warning("prompt.load_failed", path=str(file_path), error=str(e))
        return default


def extract_text_from_llm_message(content: Any) -> str:
    """
    LangChain AIMessage / response content에서 순수 텍스트 문자열을 안전하게 추출합니다.
    (str, list of dicts, list of objects 등 모든 SDK 형식 대응)
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(str(part["text"]))
            elif hasattr(part, "text"):
                text_parts.append(str(getattr(part, "text", "")))
            else:
                text_parts.append(str(part))
        return "\n".join(text_parts)
    return str(content) if content is not None else ""


def extract_json_from_llm_response(text: Union[str, Any]) -> Optional[Dict[str, Any]]:
    """
    LLM 응답 텍스트에서 ```json ... ``` 블록 또는 최외곽 { ... } JSON 객체를 안전하게 추출하여 dict로 파싱합니다.
    """
    if not text:
        return None
    raw_str = extract_text_from_llm_message(text)
    if not raw_str:
        return None

    # 1. ```json ... ``` 코드 블록 탐색
    json_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_str, re.IGNORECASE)
    for block in reversed(json_blocks):
        try:
            return json.loads(block)
        except Exception:
            continue

    # 2. 최외곽 { ... } 탐색
    brace_matches = re.findall(r"(\{[\s\S]*?\})", raw_str)
    for block in reversed(brace_matches):
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict) and len(parsed) > 0:
                return parsed
        except Exception:
            continue

    return None

