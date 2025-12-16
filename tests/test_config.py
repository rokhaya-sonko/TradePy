"""Tests for configuration module."""

import random
from pathlib import Path

import numpy as np
import pytest

from tradepy.config import CacheConfig, Config


class TestCacheConfig:
    """Tests for CacheConfig."""
    
    def test_default_values(self) -> None:
        """Test default cache configuration."""
        config = CacheConfig()
        assert config.cache_dir == Path.home() / ".tradepy" / "cache"
        assert config.format == "parquet"
        assert config.enabled is True
    
    def test_custom_values(self) -> None:
        """Test custom cache configuration."""
        cache_dir = Path("/tmp/test_cache")
        config = CacheConfig(
            cache_dir=cache_dir,
            format="csv",
            enabled=False,
        )
        assert config.cache_dir == cache_dir
        assert config.format == "csv"
        assert config.enabled is False


class TestConfig:
    """Tests for Config."""
    
    def test_default_values(self) -> None:
        """Test default configuration."""
        config = Config()
        assert config.random_seed == 42
        assert isinstance(config.cache, CacheConfig)
    
    def test_deterministic_seed(self) -> None:
        """Test that random seed is set deterministically."""
        # Create config with specific seed
        config1 = Config(random_seed=123)
        val1_np = np.random.rand()
        val1_py = random.random()
        
        # Reset and create config with same seed
        config2 = Config(random_seed=123)
        val2_np = np.random.rand()
        val2_py = random.random()
        
        # Values should be the same
        assert val1_np == val2_np
        assert val1_py == val2_py
    
    def test_custom_cache_config(self) -> None:
        """Test config with custom cache."""
        cache = CacheConfig(format="csv")
        config = Config(cache=cache)
        assert config.cache.format == "csv"
