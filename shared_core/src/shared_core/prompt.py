import yaml
from pathlib import Path
from typing import Any, Union

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
