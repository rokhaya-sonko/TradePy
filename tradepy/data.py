"""Data structures and caching for OHLCV data."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from tradepy.config import CacheConfig


@dataclass
class OHLCV:
    """Daily OHLCV (Open, High, Low, Close, Volume) bars.
    
    Attributes:
        symbol: Ticker symbol
        dates: Array of dates
        open: Opening prices
        high: High prices
        low: Low prices
        close: Closing prices
        volume: Trading volumes
    """
    symbol: str
    dates: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    
    def __post_init__(self) -> None:
        """Validate OHLCV data consistency."""
        lengths = [
            len(self.dates),
            len(self.open),
            len(self.high),
            len(self.low),
            len(self.close),
            len(self.volume),
        ]
        if len(set(lengths)) != 1:
            raise ValueError("All OHLCV arrays must have the same length")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert OHLCV to pandas DataFrame.
        
        Returns:
            DataFrame with OHLCV data indexed by date
        """
        df = pd.DataFrame({
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
        }, index=pd.to_datetime(self.dates))
        df.index.name = 'date'
        return df
    
    @classmethod
    def from_dataframe(cls, symbol: str, df: pd.DataFrame) -> "OHLCV":
        """Create OHLCV from pandas DataFrame.
        
        Args:
            symbol: Ticker symbol
            df: DataFrame with columns: open, high, low, close, volume
        
        Returns:
            OHLCV instance
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")
        
        return cls(
            symbol=symbol,
            dates=df.index.to_numpy(),
            open=df['open'].to_numpy(),
            high=df['high'].to_numpy(),
            low=df['low'].to_numpy(),
            close=df['close'].to_numpy(),
            volume=df['volume'].to_numpy(),
        )


class DataCache:
    """Local cache for OHLCV data (Parquet preferred, CSV fallback)."""
    
    def __init__(self, config: CacheConfig) -> None:
        """Initialize data cache.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        if config.enabled:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, symbol: str) -> Path:
        """Get cache file path for a symbol.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Path to cache file
        """
        ext = "parquet" if self.config.format == "parquet" else "csv"
        return self.config.cache_dir / f"{symbol}.{ext}"
    
    def save(self, ohlcv: OHLCV) -> None:
        """Save OHLCV data to cache.
        
        Args:
            ohlcv: OHLCV data to save
        """
        if not self.config.enabled:
            return
        
        df = ohlcv.to_dataframe()
        cache_path = self._get_cache_path(ohlcv.symbol)
        
        if self.config.format == "parquet":
            df.to_parquet(cache_path)
        else:
            df.to_csv(cache_path)
    
    def load(self, symbol: str) -> Optional[OHLCV]:
        """Load OHLCV data from cache.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            OHLCV data if cached, None otherwise
        """
        if not self.config.enabled:
            return None
        
        cache_path = self._get_cache_path(symbol)
        if not cache_path.exists():
            return None
        
        try:
            if self.config.format == "parquet":
                df = pd.read_parquet(cache_path)
            else:
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            
            return OHLCV.from_dataframe(symbol, df)
        except Exception:
            # If cache is corrupted, return None
            return None
    
    def clear(self, symbol: Optional[str] = None) -> None:
        """Clear cache for a symbol or all symbols.
        
        Args:
            symbol: Symbol to clear, or None to clear all
        """
        if not self.config.enabled:
            return
        
        if symbol is not None:
            cache_path = self._get_cache_path(symbol)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # Clear all cache files
            for ext in ["parquet", "csv"]:
                for cache_file in self.config.cache_dir.glob(f"*.{ext}"):
                    cache_file.unlink()
