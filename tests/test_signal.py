"""Tests for signal module."""

from datetime import datetime

import numpy as np
import pytest

from tradepy.data import OHLCV
from tradepy.signal import Signal, SimpleMovingAverageCrossover


class TestSignal:
    """Tests for Signal dataclass."""
    
    def test_create_signal(self) -> None:
        """Test creating a signal."""
        dates = np.array([datetime(2024, 1, i) for i in range(1, 6)])
        values = np.array([0.0, 1.0, 1.0, -1.0, 0.0])
        
        signal = Signal(
            symbol="TEST",
            dates=dates,
            values=values,
        )
        
        assert signal.symbol == "TEST"
        assert len(signal.dates) == 5
        assert signal.values[1] == 1.0
    
    def test_signal_with_strengths(self) -> None:
        """Test signal with strength values."""
        dates = np.array([datetime(2024, 1, i) for i in range(1, 4)])
        values = np.array([1.0, 1.0, -1.0])
        strengths = np.array([0.8, 0.9, 0.7])
        
        signal = Signal(
            symbol="TEST",
            dates=dates,
            values=values,
            strengths=strengths,
        )
        
        assert signal.strengths is not None
        assert len(signal.strengths) == 3
        assert signal.strengths[0] == 0.8
    
    def test_inconsistent_lengths_raises_error(self) -> None:
        """Test that inconsistent lengths raise error."""
        with pytest.raises(ValueError, match="same length"):
            Signal(
                symbol="TEST",
                dates=np.array([datetime(2024, 1, 1)]),
                values=np.array([1.0, -1.0]),  # Different length
            )
    
    def test_to_dataframe(self) -> None:
        """Test conversion to DataFrame."""
        dates = np.array([datetime(2024, 1, i) for i in range(1, 4)])
        values = np.array([1.0, 0.0, -1.0])
        
        signal = Signal(symbol="TEST", dates=dates, values=values)
        df = signal.to_dataframe()
        
        assert len(df) == 3
        assert 'signal' in df.columns
        assert df.index.name == 'date'


class TestSimpleMovingAverageCrossover:
    """Tests for SimpleMovingAverageCrossover."""
    
    def test_initialization(self) -> None:
        """Test signal generator initialization."""
        gen = SimpleMovingAverageCrossover(fast_period=10, slow_period=20)
        assert gen.fast_period == 10
        assert gen.slow_period == 20
    
    def test_invalid_periods_raise_error(self) -> None:
        """Test that invalid periods raise error."""
        with pytest.raises(ValueError, match="fast_period must be less than"):
            SimpleMovingAverageCrossover(fast_period=50, slow_period=20)
    
    def test_generate_signals(self) -> None:
        """Test signal generation."""
        # Create uptrend data
        import pandas as pd
        dates = pd.date_range('2024-01-01', periods=100, freq='D').to_numpy()
        close_prices = np.linspace(100, 200, 100)  # Uptrend
        
        ohlcv = OHLCV(
            symbol="TEST",
            dates=dates,
            open=close_prices - 1,
            high=close_prices + 2,
            low=close_prices - 2,
            close=close_prices,
            volume=np.ones(100) * 1000,
        )
        
        gen = SimpleMovingAverageCrossover(fast_period=10, slow_period=20)
        signal = gen.generate(ohlcv)
        
        assert signal.symbol == "TEST"
        assert len(signal.values) == 100
        # In uptrend, should eventually have long signals
        assert np.any(signal.values > 0)
    
    def test_crossover_detection(self) -> None:
        """Test that crossovers are detected."""
        # Create data with clear crossover
        import pandas as pd
        dates = pd.date_range('2024-01-01', periods=60, freq='D').to_numpy()
        # First half: downtrend, second half: uptrend
        close_prices = np.concatenate([
            np.linspace(100, 80, 30),  # Downtrend
            np.linspace(80, 120, 30),  # Uptrend
        ])
        
        ohlcv = OHLCV(
            symbol="TEST",
            dates=dates,
            open=close_prices - 1,
            high=close_prices + 2,
            low=close_prices - 2,
            close=close_prices,
            volume=np.ones(60) * 1000,
        )
        
        gen = SimpleMovingAverageCrossover(fast_period=5, slow_period=10)
        signal = gen.generate(ohlcv)
        
        # Should have both long and short signals
        assert np.any(signal.values > 0)  # Long signals
        assert np.any(signal.values < 0)  # Short signals
