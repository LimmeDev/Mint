"""
Configuration module for the Mint AI Framework.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Configuration class for the Mint AI Framework."""

    # Model settings
    model_path: str = os.getenv("MODEL_PATH", "gpt2")
    
    # Cross-platform device detection
    try:
        import torch

        _DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:  # torch not installed or fails to import
        _DEFAULT_DEVICE = "cpu"

    device: str = os.getenv("DEVICE", _DEFAULT_DEVICE)
    
    # API settings
    api_key: Optional[str] = os.getenv("API_KEY")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Generation settings
    max_length: int = int(os.getenv("MAX_LENGTH", "100"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    top_p: float = float(os.getenv("TOP_P", "0.9"))
    
    # Paths
    cache_dir: Path = Path(os.getenv("CACHE_DIR", ".cache"))
    
    def __post_init__(self):
        """Ensure paths exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Create a default configuration instance
config = Config()


def get_config() -> Config:
    """Get the current configuration.
    
    Returns:
        Config: The current configuration instance.
    """
    return config 