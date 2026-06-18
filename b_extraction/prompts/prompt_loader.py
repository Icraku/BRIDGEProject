"""
b_extraction/prompts/prompt_loader.py
============================
Utilities for loading prompt templates and prompt configuration
files used by the extraction pipeline.

Functions
---------
load_prompts(prompt_dir)
    Load all .txt prompt files from a directory.

load_prompt_config(config_path)
    Load the JSON prompt configuration file.
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Default prompt locations

PROMPT_DIR = Path(__file__).parent
PROMPT_CONFIG = PROMPT_DIR / "prompt_config.json"

# ---------------------------------------------------------------------------
# Prompt loading

def load_prompts(prompt_dir: str | Path = PROMPT_DIR) -> dict[str, str]:
    """Load all prompt templates from prompts directory.

    Parameters
    ----------
    prompt_dir : Directory containing .txt prompt files.

    Returns
    -------
    dict[str, str]
        Mapping of prompt name to prompt content.

    Raises
    ------
    FileNotFoundError
        If the prompt directory does not exist OR if it exists but contains no .txt files.
    """
    prompt_dir = Path(prompt_dir)

    if not prompt_dir.is_dir():
        raise FileNotFoundError(f"Prompt directory not found: {prompt_dir}")

    prompts: dict[str, str] = {}
    for file in prompt_dir.glob("*.txt"):
        prompts[file.stem] = file.read_text(encoding="utf-8")

    if not prompts:
        raise FileNotFoundError(
            f"No .txt prompt files found in: {prompt_dir}"
        )

    return prompts


# ---------------------------------------------------------------------------
# Configuration loading

def load_prompt_config(
    config_path: str | Path = PROMPT_CONFIG,
) -> dict:
    """Load prompt configuration from a JSON file.

    Parameters
    ----------
    config_path : Path to the prompt configuration JSON file.

    Returns
    -------
    dict
        Parsed configuration data.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    """
    config_path = Path(config_path)

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Prompt configuration not found: {config_path}"
        )

    return json.loads(config_path.read_text(encoding="utf-8"))