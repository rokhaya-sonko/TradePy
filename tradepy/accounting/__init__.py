"""Accounting module.

This module tracks profit/loss, returns, and performance metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

from tradepy.execution import Fill

# Constants
TRADING_DAYS_PER_YEAR = 252.0  # Standard number of trading days in a year


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics.
    
    Attributes:
        total_return: Total return (%)
        annualized_return: Annualized return (%)
        sharpe_ratio: Sharpe ratio
        max_drawdown: Maximum drawdown (%)
        win_rate: Win rate (%)
        profit_factor: Profit factor
    """
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float


@dataclass
class AccountingLedger:
    """Accounting ledger for tracking P&L and returns.
    
    Attributes:
        initial_capital: Starting capital
        fills: List of executed fills
        equity_curve: List of (timestamp, equity) tuples
    """
    initial_capital: float
    fills: List[Fill] = field(default_factory=list)
    equity_curve: List[tuple[datetime, float]] = field(default_factory=list)
    
    def add_fill(self, fill: Fill) -> None:
        """Record a fill in the ledger.
        
        Args:
            fill: Executed fill
        """
        self.fills.append(fill)
    
    def record_equity(self, timestamp: datetime, equity: float) -> None:
        """Record equity at a point in time.
        
        Args:
            timestamp: Time of recording
            equity: Portfolio equity value
        """
        self.equity_curve.append((timestamp, equity))
    
    def get_equity_dataframe(self) -> pd.DataFrame:
        """Get equity curve as DataFrame.
        
        Returns:
            DataFrame with timestamp index and equity values
        """
        if not self.equity_curve:
            return pd.DataFrame(columns=['equity'])
        
        timestamps, equities = zip(*self.equity_curve)
        df = pd.DataFrame({'equity': equities}, index=pd.to_datetime(timestamps))
        df.index.name = 'timestamp'
        return df
    
    def calculate_returns(self) -> pd.Series:
        """Calculate period returns.
        
        Returns:
            Series of period returns
        """
        df = self.get_equity_dataframe()
        if len(df) < 2:
            return pd.Series(dtype=float)
        
        returns = df['equity'].pct_change().dropna()
        return returns
    
    def calculate_metrics(self, risk_free_rate: float = 0.0) -> PerformanceMetrics:
        """Calculate performance metrics.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio
        
        Returns:
            Performance metrics
        """
        df = self.get_equity_dataframe()
        if len(df) < 2:
            return PerformanceMetrics(
                total_return=0.0,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
            )
        
        returns = self.calculate_returns()
        
        # Total return
        total_return = (df['equity'].iloc[-1] / self.initial_capital - 1.0) * 100
        
        # Annualized return (assuming daily data)
        days = len(df)
        years = days / TRADING_DAYS_PER_YEAR
        annualized_return = ((df['equity'].iloc[-1] / self.initial_capital) ** (1.0 / years) - 1.0) * 100 if years > 0 else 0.0
        
        # Sharpe ratio (assuming daily returns)
        daily_rf = (1 + risk_free_rate) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0
        excess_returns = returns - daily_rf
        sharpe_ratio = np.sqrt(TRADING_DAYS_PER_YEAR) * excess_returns.mean() / excess_returns.std() if len(excess_returns) > 0 and excess_returns.std() > 0 else 0.0
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Win rate
        wins = (returns > 0).sum()
        total_trades = len(returns)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        
        # Profit factor
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        profit_factor = gains / losses if losses > 0 else 0.0
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
        )
