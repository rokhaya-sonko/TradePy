"""Configuration dataclasses for TradePy."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class CacheConfig:
    """Configuration for data caching.
    
    Attributes:
        cache_dir: Directory for storing cached data
        format: Cache format - 'parquet' (preferred) or 'csv' (fallback)
        enabled: Whether caching is enabled
    """
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".tradepy" / "cache")
    format: Literal["parquet", "csv"] = "parquet"
    enabled: bool = True


@dataclass
class Config:
    """Main configuration for TradePy.
    
    Attributes:
        random_seed: Seed for reproducibility (deterministic results)
        cache: Cache configuration
    """
    random_seed: int = 42
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    def __post_init__(self) -> None:
        """Set random seeds for reproducibility."""
        import numpy as np
        import random
        
        np.random.seed(self.random_seed)
        random.seed(self.random_seed)
