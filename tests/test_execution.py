"""Tests for execution module."""

from datetime import datetime

import pytest

from tradepy.execution import Order, OrderType, OrderSide, Fill, ExecutionEngine
from tradepy.portfolio import Portfolio, Position


class TestOrder:
    """Tests for Order dataclass."""
    
    def test_create_market_order(self) -> None:
        """Test creating a market order."""
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            shares=100.0,
            order_type=OrderType.MARKET,
        )
        
        assert order.symbol == "TEST"
        assert order.side == OrderSide.BUY
        assert order.shares == 100.0
        assert order.order_type == OrderType.MARKET
    
    def test_create_limit_order(self) -> None:
        """Test creating a limit order."""
        order = Order(
            symbol="TEST",
            side=OrderSide.SELL,
            shares=50.0,
            order_type=OrderType.LIMIT,
            limit_price=105.0,
        )
        
        assert order.limit_price == 105.0
    
    def test_negative_shares_raises_error(self) -> None:
        """Test that negative shares raise error."""
        with pytest.raises(ValueError, match="shares must be positive"):
            Order(
                symbol="TEST",
                side=OrderSide.BUY,
                shares=-100.0,
            )
    
    def test_limit_order_without_price_raises_error(self) -> None:
        """Test that limit order without price raises error."""
        with pytest.raises(ValueError, match="limit_price required"):
            Order(
                symbol="TEST",
                side=OrderSide.BUY,
                shares=100.0,
                order_type=OrderType.LIMIT,
            )


class TestFill:
    """Tests for Fill dataclass."""
    
    def test_create_fill(self) -> None:
        """Test creating a fill."""
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            shares=100.0,
        )
        
        fill = Fill(
            order=order,
            fill_price=50.0,
            fill_shares=100.0,
            timestamp=datetime(2024, 1, 1),
            commission=5.0,
        )
        
        assert fill.fill_price == 50.0
        assert fill.fill_shares == 100.0
        assert fill.commission == 5.0
    
    def test_fill_value(self) -> None:
        """Test fill value calculation."""
        order = Order(symbol="TEST", side=OrderSide.BUY, shares=100.0)
        fill = Fill(
            order=order,
            fill_price=50.0,
            fill_shares=100.0,
            timestamp=datetime(2024, 1, 1),
        )
        
        assert fill.fill_value == 5000.0
    
    def test_total_cost(self) -> None:
        """Test total cost calculation."""
        order = Order(symbol="TEST", side=OrderSide.BUY, shares=100.0)
        fill = Fill(
            order=order,
            fill_price=50.0,
            fill_shares=100.0,
            timestamp=datetime(2024, 1, 1),
            commission=10.0,
        )
        
        assert fill.total_cost == 5010.0


class TestExecutionEngine:
    """Tests for ExecutionEngine."""
    
    def test_initialization(self) -> None:
        """Test execution engine initialization."""
        engine = ExecutionEngine(commission_rate=0.001)
        assert engine.commission_rate == 0.001
        assert len(engine.fills) == 0
    
    def test_execute_market_order(self) -> None:
        """Test executing a market order."""
        engine = ExecutionEngine(commission_rate=0.001)
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            shares=100.0,
        )
        
        fill = engine.execute(order, 50.0, datetime(2024, 1, 1))
        
        assert fill.fill_price == 50.0
        assert fill.fill_shares == 100.0
        assert fill.commission == 5.0  # 50 * 100 * 0.001
        assert len(engine.fills) == 1
    
    def test_execute_buy_limit_order_filled(self) -> None:
        """Test executing a buy limit order that gets filled."""
        engine = ExecutionEngine()
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            shares=100.0,
            order_type=OrderType.LIMIT,
            limit_price=51.0,
        )
        
        # Market price below limit - should fill at limit price
        fill = engine.execute(order, 50.0, datetime(2024, 1, 1))
        
        assert fill.fill_price == 51.0
        assert fill.fill_shares == 100.0
    
    def test_execute_buy_limit_order_not_filled(self) -> None:
        """Test executing a buy limit order that doesn't get filled."""
        engine = ExecutionEngine()
        order = Order(
            symbol="TEST",
            side=OrderSide.BUY,
            shares=100.0,
            order_type=OrderType.LIMIT,
            limit_price=49.0,
        )
        
        # Market price above limit - should not fill
        fill = engine.execute(order, 50.0, datetime(2024, 1, 1))
        
        assert fill.fill_shares == 0.0
    
    def test_execute_sell_limit_order_filled(self) -> None:
        """Test executing a sell limit order that gets filled."""
        engine = ExecutionEngine()
        order = Order(
            symbol="TEST",
            side=OrderSide.SELL,
            shares=100.0,
            order_type=OrderType.LIMIT,
            limit_price=49.0,
        )
        
        # Market price above limit - should fill at limit price
        fill = engine.execute(order, 50.0, datetime(2024, 1, 1))
        
        assert fill.fill_price == 49.0
        assert fill.fill_shares == 100.0
    
    def test_rebalance(self) -> None:
        """Test portfolio rebalancing."""
        engine = ExecutionEngine()
        portfolio = Portfolio(cash=10000.0, positions={})
        target_weights = {"TEST": 0.5}
        current_prices = {"TEST": 100.0}
        
        fills = engine.rebalance(
            portfolio,
            target_weights,
            current_prices,
            datetime(2024, 1, 1),
        )
        
        # Should buy shares to reach 50% weight
        assert len(fills) == 1
        assert fills[0].order.side == OrderSide.BUY
