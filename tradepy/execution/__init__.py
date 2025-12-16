"""Execution module.

This module handles order creation, execution, and management.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from tradepy.portfolio import Portfolio, Position


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Trading order.
    
    Attributes:
        symbol: Ticker symbol
        side: Order side (buy/sell)
        shares: Number of shares
        order_type: Order type (market/limit)
        limit_price: Limit price (for limit orders)
        timestamp: Order timestamp
    """
    symbol: str
    side: OrderSide
    shares: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validate order."""
        if self.shares <= 0:
            raise ValueError("shares must be positive")
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price required for limit orders")


@dataclass
class Fill:
    """Order fill/execution.
    
    Attributes:
        order: Original order
        fill_price: Execution price
        fill_shares: Executed shares
        timestamp: Fill timestamp
        commission: Commission paid
    """
    order: Order
    fill_price: float
    fill_shares: float
    timestamp: datetime
    commission: float = 0.0
    
    @property
    def fill_value(self) -> float:
        """Total fill value (excluding commission)."""
        return self.fill_price * self.fill_shares
    
    @property
    def total_cost(self) -> float:
        """Total cost including commission."""
        return self.fill_value + self.commission


class ExecutionEngine:
    """Order execution engine.
    
    Executes orders against market prices with optional commission.
    """
    
    def __init__(self, commission_rate: float = 0.0) -> None:
        """Initialize execution engine.
        
        Args:
            commission_rate: Commission rate (e.g., 0.001 for 0.1%)
        """
        self.commission_rate = commission_rate
        self.fills: List[Fill] = []
    
    def execute(
        self,
        order: Order,
        market_price: float,
        timestamp: datetime,
    ) -> Fill:
        """Execute an order.
        
        Args:
            order: Order to execute
            market_price: Current market price
            timestamp: Execution timestamp
        
        Returns:
            Fill representing the execution
        """
        # Determine fill price based on order type
        if order.order_type == OrderType.MARKET:
            fill_price = market_price
        else:
            # For limit orders, check if limit price is met
            if order.side == OrderSide.BUY and market_price <= order.limit_price:
                fill_price = order.limit_price
            elif order.side == OrderSide.SELL and market_price >= order.limit_price:
                fill_price = order.limit_price
            else:
                # Limit not met, no fill
                fill_price = market_price
                fill_shares = 0.0
                commission = 0.0
                fill = Fill(
                    order=order,
                    fill_price=fill_price,
                    fill_shares=fill_shares,
                    timestamp=timestamp,
                    commission=commission,
                )
                self.fills.append(fill)
                return fill
        
        fill_shares = order.shares
        commission = fill_price * fill_shares * self.commission_rate
        
        fill = Fill(
            order=order,
            fill_price=fill_price,
            fill_shares=fill_shares,
            timestamp=timestamp,
            commission=commission,
        )
        
        self.fills.append(fill)
        return fill
    
    def rebalance(
        self,
        portfolio: Portfolio,
        target_weights: Dict[str, float],
        current_prices: Dict[str, float],
        timestamp: datetime,
    ) -> List[Fill]:
        """Rebalance portfolio to target weights.
        
        Args:
            portfolio: Current portfolio
            target_weights: Target weights by symbol
            current_prices: Current market prices
            timestamp: Execution timestamp
        
        Returns:
            List of fills from rebalancing
        """
        fills: List[Fill] = []
        total_value = portfolio.market_value
        
        for symbol, target_weight in target_weights.items():
            target_value = total_value * target_weight
            current_shares = portfolio.positions.get(symbol, Position(symbol, 0, 0, 0)).shares
            current_price = current_prices.get(symbol, 0)
            
            if current_price <= 0:
                continue
            
            target_shares = target_value / current_price
            delta_shares = target_shares - current_shares
            
            if abs(delta_shares) > 1e-6:  # Avoid tiny trades
                order = Order(
                    symbol=symbol,
                    side=OrderSide.BUY if delta_shares > 0 else OrderSide.SELL,
                    shares=abs(delta_shares),
                    order_type=OrderType.MARKET,
                    timestamp=timestamp,
                )
                fill = self.execute(order, current_price, timestamp)
                fills.append(fill)
        
        return fills
