"""Tests for accounting module."""

from datetime import datetime

import pytest

from tradepy.accounting import AccountingLedger, PerformanceMetrics
from tradepy.execution import Order, OrderSide, Fill


class TestAccountingLedger:
    """Tests for AccountingLedger."""
    
    def test_initialization(self) -> None:
        """Test ledger initialization."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        assert ledger.initial_capital == 10000.0
        assert len(ledger.fills) == 0
        assert len(ledger.equity_curve) == 0
    
    def test_add_fill(self) -> None:
        """Test adding a fill."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        order = Order(symbol="TEST", side=OrderSide.BUY, shares=100.0)
        fill = Fill(
            order=order,
            fill_price=50.0,
            fill_shares=100.0,
            timestamp=datetime(2024, 1, 1),
        )
        
        ledger.add_fill(fill)
        assert len(ledger.fills) == 1
    
    def test_record_equity(self) -> None:
        """Test recording equity."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        ledger.record_equity(datetime(2024, 1, 1), 10000.0)
        ledger.record_equity(datetime(2024, 1, 2), 10500.0)
        ledger.record_equity(datetime(2024, 1, 3), 11000.0)
        
        assert len(ledger.equity_curve) == 3
        assert ledger.equity_curve[0][1] == 10000.0
        assert ledger.equity_curve[2][1] == 11000.0
    
    def test_get_equity_dataframe(self) -> None:
        """Test getting equity as DataFrame."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        ledger.record_equity(datetime(2024, 1, 1), 10000.0)
        ledger.record_equity(datetime(2024, 1, 2), 10500.0)
        
        df = ledger.get_equity_dataframe()
        assert len(df) == 2
        assert 'equity' in df.columns
        assert df.index.name == 'timestamp'
    
    def test_calculate_returns(self) -> None:
        """Test calculating returns."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        ledger.record_equity(datetime(2024, 1, 1), 10000.0)
        ledger.record_equity(datetime(2024, 1, 2), 10500.0)
        ledger.record_equity(datetime(2024, 1, 3), 11000.0)
        
        returns = ledger.calculate_returns()
        assert len(returns) == 2
        # First return: (10500 - 10000) / 10000 = 0.05
        assert abs(returns.iloc[0] - 0.05) < 1e-6
    
    def test_calculate_metrics_with_data(self) -> None:
        """Test calculating performance metrics."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        # Create simple equity curve with positive returns
        for i in range(10):
            equity = 10000.0 + i * 100
            ledger.record_equity(datetime(2024, 1, i + 1), equity)
        
        metrics = ledger.calculate_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_return > 0  # Should be positive
        assert metrics.win_rate >= 0
    
    def test_calculate_metrics_empty_ledger(self) -> None:
        """Test calculating metrics with empty ledger."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        metrics = ledger.calculate_metrics()
        
        # Should return zero metrics
        assert metrics.total_return == 0.0
        assert metrics.annualized_return == 0.0
        assert metrics.sharpe_ratio == 0.0
    
    def test_calculate_metrics_with_losses(self) -> None:
        """Test calculating metrics with losses."""
        ledger = AccountingLedger(initial_capital=10000.0)
        
        # Create equity curve with losses
        for i in range(10):
            equity = 10000.0 - i * 50
            ledger.record_equity(datetime(2024, 1, i + 1), equity)
        
        metrics = ledger.calculate_metrics()
        
        assert metrics.total_return < 0  # Should be negative
        assert metrics.max_drawdown < 0  # Should have drawdown
