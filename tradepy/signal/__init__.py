"""Signal generation module.

This module contains base classes and implementations for generating
trading signals from market data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from tradepy.data import OHLCV


@dataclass
class Signal:
    """Trading signal output.
    
    Attributes:
        symbol: Ticker symbol
        dates: Array of dates
        values: Signal values (typically -1 for short, 0 for neutral, 1 for long)
        strengths: Optional signal strengths (0.0 to 1.0)
    """
    symbol: str
    dates: np.ndarray
    values: np.ndarray
    strengths: Optional[np.ndarray] = None
    
    def __post_init__(self) -> None:
        """Validate signal data."""
        if len(self.dates) != len(self.values):
            raise ValueError("dates and values must have the same length")
        if self.strengths is not None and len(self.strengths) != len(self.values):
            raise ValueError("strengths must have the same length as values")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert signal to pandas DataFrame.
        
        Returns:
            DataFrame with signal data indexed by date
        """
        data = {'signal': self.values}
        if self.strengths is not None:
            data['strength'] = self.strengths
        
        df = pd.DataFrame(data, index=pd.to_datetime(self.dates))
        df.index.name = 'date'
        return df


class SignalGenerator(ABC):
    """Base class for signal generators."""
    
    @abstractmethod
    def generate(self, ohlcv: OHLCV) -> Signal:
        """Generate trading signals from OHLCV data.
        
        Args:
            ohlcv: OHLCV market data
        
        Returns:
            Generated trading signals
        """
        pass


class SimpleMovingAverageCrossover(SignalGenerator):
    """Simple Moving Average Crossover signal generator.
    
    Generates buy signals when fast MA crosses above slow MA,
    and sell signals when fast MA crosses below slow MA.
    """
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50) -> None:
        """Initialize SMA crossover generator.
        
        Args:
            fast_period: Fast moving average period
            slow_period: Slow moving average period
        """
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")
        
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate(self, ohlcv: OHLCV) -> Signal:
        """Generate SMA crossover signals.
        
        Args:
            ohlcv: OHLCV market data
        
        Returns:
            Trading signals (-1, 0, 1)
        """
        df = ohlcv.to_dataframe()
        
        # Calculate moving averages
        fast_ma = df['close'].rolling(window=self.fast_period).mean()
        slow_ma = df['close'].rolling(window=self.slow_period).mean()
        
        # Generate signals
        signals = np.zeros(len(df))
        signals[fast_ma > slow_ma] = 1.0  # Long
        signals[fast_ma < slow_ma] = -1.0  # Short
        
        return Signal(
            symbol=ohlcv.symbol,
            dates=ohlcv.dates,
            values=signals,
        )
