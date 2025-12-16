"""
TradePy - A clean, minimal-dependency Python library for quantitative trading.

This library follows a strict separation of concerns:
- Signal: Generate trading signals from market data
- Portfolio: Manage portfolio positions and weights
- Execution: Execute trades and manage orders
- Accounting: Track P&L, returns, and accounting
- Analytics: Analyze and visualize performance
"""

__version__ = "0.1.0"

from tradepy.config import Config
from tradepy.data import OHLCV

__all__ = [
    "Config",
    "OHLCV",
]
