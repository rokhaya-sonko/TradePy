"""Portfolio management module.

This module handles portfolio construction, position sizing,
and weight allocation based on signals.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from tradepy.signal import Signal

# Constants
NEUTRAL_SIGNAL = 0.0


@dataclass
class Position:
    """Portfolio position.
    
    Attributes:
        symbol: Ticker symbol
        shares: Number of shares
        entry_price: Entry price per share
        current_price: Current market price per share
    """
    symbol: str
    shares: float
    entry_price: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        """Current market value of position."""
        return self.shares * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Cost basis of position."""
        return self.shares * self.entry_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        return self.market_value - self.cost_basis


@dataclass
class Portfolio:
    """Portfolio state.
    
    Attributes:
        cash: Available cash
        positions: Dictionary of symbol -> Position
    """
    cash: float
    positions: Dict[str, Position]
    
    @property
    def market_value(self) -> float:
        """Total portfolio market value."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    @property
    def equity(self) -> float:
        """Total portfolio equity (alias for market_value)."""
        return self.market_value


class PortfolioManager(ABC):
    """Base class for portfolio managers."""
    
    @abstractmethod
    def update(
        self,
        portfolio: Portfolio,
        signal: Signal,
        current_prices: Dict[str, float],
    ) -> Dict[str, float]:
        """Update portfolio based on signals.
        
        Args:
            portfolio: Current portfolio state
            signal: Trading signal
            current_prices: Current market prices
        
        Returns:
            Dictionary of symbol -> target weight
        """
        pass


class EqualWeightPortfolio(PortfolioManager):
    """Equal weight portfolio manager.
    
    Allocates equal weight to all positions with positive signals.
    """
    
    def __init__(self, max_positions: int = 10) -> None:
        """Initialize equal weight portfolio manager.
        
        Args:
            max_positions: Maximum number of positions
        """
        self.max_positions = max_positions
    
    def update(
        self,
        portfolio: Portfolio,
        signal: Signal,
        current_prices: Dict[str, float],
    ) -> Dict[str, float]:
        """Calculate equal weights for active signals.
        
        Args:
            portfolio: Current portfolio state
            signal: Trading signal
            current_prices: Current market prices
        
        Returns:
            Dictionary of symbol -> target weight
        """
        # Get latest signal value
        latest_signal = signal.values[-1] if len(signal.values) > 0 else NEUTRAL_SIGNAL
        
        weights: Dict[str, float] = {}
        
        if latest_signal > 0:
            # Long signal - allocate equal weight
            weights[signal.symbol] = 1.0 / self.max_positions
        elif latest_signal < 0:
            # Short signal - zero weight (close position)
            weights[signal.symbol] = 0.0
        else:
            # Neutral - maintain current weight or zero
            weights[signal.symbol] = 0.0
        
        return weights
