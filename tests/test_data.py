"""Tests for data module."""

from datetime import datetime
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import pytest

from tradepy.config import CacheConfig
from tradepy.data import OHLCV, DataCache


class TestOHLCV:
    """Tests for OHLCV dataclass."""
    
    def test_create_ohlcv(self) -> None:
        """Test creating OHLCV data."""
        dates = np.array([datetime(2024, 1, i) for i in range(1, 6)])
        ohlcv = OHLCV(
            symbol="TEST",
            dates=dates,
            open=np.array([100.0, 101.0, 102.0, 103.0, 104.0]),
            high=np.array([105.0, 106.0, 107.0, 108.0, 109.0]),
            low=np.array([99.0, 100.0, 101.0, 102.0, 103.0]),
            close=np.array([104.0, 105.0, 106.0, 107.0, 108.0]),
            volume=np.array([1000, 1100, 1200, 1300, 1400]),
        )
        
        assert ohlcv.symbol == "TEST"
        assert len(ohlcv.dates) == 5
        assert ohlcv.close[0] == 104.0
    
    def test_inconsistent_lengths_raises_error(self) -> None:
        """Test that inconsistent array lengths raise error."""
        with pytest.raises(ValueError, match="same length"):
            OHLCV(
                symbol="TEST",
                dates=np.array([datetime(2024, 1, 1)]),
                open=np.array([100.0]),
                high=np.array([105.0]),
                low=np.array([99.0]),
                close=np.array([104.0, 105.0]),  # Different length
                volume=np.array([1000]),
            )
    
    def test_to_dataframe(self) -> None:
        """Test conversion to DataFrame."""
        dates = np.array([datetime(2024, 1, i) for i in range(1, 4)])
        ohlcv = OHLCV(
            symbol="TEST",
            dates=dates,
            open=np.array([100.0, 101.0, 102.0]),
            high=np.array([105.0, 106.0, 107.0]),
            low=np.array([99.0, 100.0, 101.0]),
            close=np.array([104.0, 105.0, 106.0]),
            volume=np.array([1000, 1100, 1200]),
        )
        
        df = ohlcv.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'open' in df.columns
        assert 'close' in df.columns
        assert df.index.name == 'date'
    
    def test_from_dataframe(self) -> None:
        """Test creation from DataFrame."""
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [104.0, 105.0, 106.0],
            'volume': [1000, 1100, 1200],
        }, index=pd.date_range('2024-01-01', periods=3))
        
        ohlcv = OHLCV.from_dataframe("TEST", df)
        assert ohlcv.symbol == "TEST"
        assert len(ohlcv.dates) == 3
        assert ohlcv.close[0] == 104.0
    
    def test_from_dataframe_missing_columns(self) -> None:
        """Test that missing columns raise error."""
        df = pd.DataFrame({
            'open': [100.0],
            'close': [104.0],
        })
        
        with pytest.raises(ValueError, match="missing required columns"):
            OHLCV.from_dataframe("TEST", df)


class TestDataCache:
    """Tests for DataCache."""
    
    def test_cache_disabled(self) -> None:
        """Test cache with disabled configuration."""
        config = CacheConfig(enabled=False)
        cache = DataCache(config)
        
        dates = np.array([datetime(2024, 1, 1)])
        ohlcv = OHLCV(
            symbol="TEST",
            dates=dates,
            open=np.array([100.0]),
            high=np.array([105.0]),
            low=np.array([99.0]),
            close=np.array([104.0]),
            volume=np.array([1000]),
        )
        
        cache.save(ohlcv)
        loaded = cache.load("TEST")
        assert loaded is None
    
    def test_parquet_cache(self) -> None:
        """Test Parquet cache format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CacheConfig(
                cache_dir=Path(tmpdir),
                format="parquet",
                enabled=True,
            )
            cache = DataCache(config)
            
            dates = np.array([datetime(2024, 1, i) for i in range(1, 4)])
            ohlcv = OHLCV(
                symbol="TEST",
                dates=dates,
                open=np.array([100.0, 101.0, 102.0]),
                high=np.array([105.0, 106.0, 107.0]),
                low=np.array([99.0, 100.0, 101.0]),
                close=np.array([104.0, 105.0, 106.0]),
                volume=np.array([1000, 1100, 1200]),
            )
            
            cache.save(ohlcv)
            loaded = cache.load("TEST")
            
            assert loaded is not None
            assert loaded.symbol == "TEST"
            assert len(loaded.dates) == 3
            np.testing.assert_array_almost_equal(loaded.close, ohlcv.close)
    
    def test_csv_cache(self) -> None:
        """Test CSV cache format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CacheConfig(
                cache_dir=Path(tmpdir),
                format="csv",
                enabled=True,
            )
            cache = DataCache(config)
            
            dates = np.array([datetime(2024, 1, i) for i in range(1, 4)])
            ohlcv = OHLCV(
                symbol="TEST",
                dates=dates,
                open=np.array([100.0, 101.0, 102.0]),
                high=np.array([105.0, 106.0, 107.0]),
                low=np.array([99.0, 100.0, 101.0]),
                close=np.array([104.0, 105.0, 106.0]),
                volume=np.array([1000, 1100, 1200]),
            )
            
            cache.save(ohlcv)
            loaded = cache.load("TEST")
            
            assert loaded is not None
            assert loaded.symbol == "TEST"
            assert len(loaded.dates) == 3
    
    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CacheConfig(cache_dir=Path(tmpdir), enabled=True)
            cache = DataCache(config)
            
            dates = np.array([datetime(2024, 1, 1)])
            ohlcv = OHLCV(
                symbol="TEST",
                dates=dates,
                open=np.array([100.0]),
                high=np.array([105.0]),
                low=np.array([99.0]),
                close=np.array([104.0]),
                volume=np.array([1000]),
            )
            
            cache.save(ohlcv)
            assert cache.load("TEST") is not None
            
            cache.clear("TEST")
            assert cache.load("TEST") is None
