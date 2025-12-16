"""Tests for portfolio module."""

from datetime import datetime

import numpy as np
import pytest

from tradepy.portfolio import Position, Portfolio, EqualWeightPortfolio
from tradepy.signal import Signal


class TestPosition:
    """Tests for Position dataclass."""
    
    def test_create_position(self) -> None:
        """Test creating a position."""
        pos = Position(
            symbol="TEST",
            shares=100.0,
            entry_price=50.0,
            current_price=55.0,
        )
        
        assert pos.symbol == "TEST"
        assert pos.shares == 100.0
        assert pos.entry_price == 50.0
        assert pos.current_price == 55.0
    
    def test_market_value(self) -> None:
        """Test market value calculation."""
        pos = Position(
            symbol="TEST",
            shares=100.0,
            entry_price=50.0,
            current_price=55.0,
        )
        
        assert pos.market_value == 5500.0
    
    def test_cost_basis(self) -> None:
        """Test cost basis calculation."""
        pos = Position(
            symbol="TEST",
            shares=100.0,
            entry_price=50.0,
            current_price=55.0,
        )
        
        assert pos.cost_basis == 5000.0
    
    def test_unrealized_pnl(self) -> None:
        """Test unrealized P&L calculation."""
        pos = Position(
            symbol="TEST",
            shares=100.0,
            entry_price=50.0,
            current_price=55.0,
        )
        
        assert pos.unrealized_pnl == 500.0


class TestPortfolio:
    """Tests for Portfolio dataclass."""
    
    def test_create_portfolio(self) -> None:
        """Test creating a portfolio."""
        portfolio = Portfolio(
            cash=10000.0,
            positions={},
        )
        
        assert portfolio.cash == 10000.0
        assert len(portfolio.positions) == 0
    
    def test_market_value_with_positions(self) -> None:
        """Test market value with positions."""
        pos1 = Position("TEST1", 100.0, 50.0, 55.0)
        pos2 = Position("TEST2", 50.0, 100.0, 110.0)
        
        portfolio = Portfolio(
            cash=5000.0,
            positions={"TEST1": pos1, "TEST2": pos2},
        )
        
        # Cash + (100 * 55) + (50 * 110) = 5000 + 5500 + 5500 = 16000
        assert portfolio.market_value == 16000.0
    
    def test_equity_equals_market_value(self) -> None:
        """Test that equity equals market value."""
        portfolio = Portfolio(cash=10000.0, positions={})
        assert portfolio.equity == portfolio.market_value


class TestEqualWeightPortfolio:
    """Tests for EqualWeightPortfolio."""
    
    def test_initialization(self) -> None:
        """Test portfolio manager initialization."""
        pm = EqualWeightPortfolio(max_positions=5)
        assert pm.max_positions == 5
    
    def test_long_signal_allocation(self) -> None:
        """Test allocation for long signal."""
        pm = EqualWeightPortfolio(max_positions=10)
        portfolio = Portfolio(cash=10000.0, positions={})
        
        dates = np.array([datetime(2024, 1, 1)])
        signal = Signal(
            symbol="TEST",
            dates=dates,
            values=np.array([1.0]),  # Long signal
        )
        
        weights = pm.update(portfolio, signal, {"TEST": 100.0})
        
        assert "TEST" in weights
        assert weights["TEST"] == 0.1  # 1/10
    
    def test_short_signal_allocation(self) -> None:
        """Test allocation for short signal."""
        pm = EqualWeightPortfolio(max_positions=10)
        portfolio = Portfolio(cash=10000.0, positions={})
        
        dates = np.array([datetime(2024, 1, 1)])
        signal = Signal(
            symbol="TEST",
            dates=dates,
            values=np.array([-1.0]),  # Short signal
        )
        
        weights = pm.update(portfolio, signal, {"TEST": 100.0})
        
        assert weights["TEST"] == 0.0
    
    def test_neutral_signal_allocation(self) -> None:
        """Test allocation for neutral signal."""
        pm = EqualWeightPortfolio(max_positions=10)
        portfolio = Portfolio(cash=10000.0, positions={})
        
        dates = np.array([datetime(2024, 1, 1)])
        signal = Signal(
            symbol="TEST",
            dates=dates,
            values=np.array([0.0]),  # Neutral signal
        )
        
        weights = pm.update(portfolio, signal, {"TEST": 100.0})
        
        assert weights["TEST"] == 0.0
