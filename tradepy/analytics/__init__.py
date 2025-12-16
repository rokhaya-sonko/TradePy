"""Analytics module.

This module provides visualization and analysis tools for portfolio performance.
"""

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tradepy.accounting import AccountingLedger, PerformanceMetrics
from tradepy.data import OHLCV
from tradepy.signal import Signal


class Analytics:
    """Analytics and visualization for trading strategies."""
    
    @staticmethod
    def plot_ohlcv(ohlcv: OHLCV, title: Optional[str] = None) -> go.Figure:
        """Plot OHLCV candlestick chart.
        
        Args:
            ohlcv: OHLCV data
            title: Chart title
        
        Returns:
            Plotly figure
        """
        df = ohlcv.to_dataframe()
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(title or f"{ohlcv.symbol} Price", "Volume"),
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC',
            ),
            row=1, col=1,
        )
        
        # Volume bar chart
        fig.add_trace(
            go.Bar(x=df.index, y=df['volume'], name='Volume', marker_color='lightblue'),
            row=2, col=1,
        )
        
        fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=600,
            showlegend=True,
        )
        
        return fig
    
    @staticmethod
    def plot_signals(ohlcv: OHLCV, signal: Signal, title: Optional[str] = None) -> go.Figure:
        """Plot OHLCV with signals overlaid.
        
        Args:
            ohlcv: OHLCV data
            signal: Trading signals
            title: Chart title
        
        Returns:
            Plotly figure
        """
        df = ohlcv.to_dataframe()
        sig_df = signal.to_dataframe()
        
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC',
            )
        )
        
        # Buy signals
        buy_dates = sig_df[sig_df['signal'] > 0].index
        buy_prices = df.loc[buy_dates, 'close']
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                name='Buy',
                marker=dict(color='green', size=10, symbol='triangle-up'),
            )
        )
        
        # Sell signals
        sell_dates = sig_df[sig_df['signal'] < 0].index
        sell_prices = df.loc[sell_dates, 'close']
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                name='Sell',
                marker=dict(color='red', size=10, symbol='triangle-down'),
            )
        )
        
        fig.update_layout(
            title=title or f"{ohlcv.symbol} with Signals",
            xaxis_title='Date',
            yaxis_title='Price',
            xaxis_rangeslider_visible=False,
            height=500,
        )
        
        return fig
    
    @staticmethod
    def plot_equity_curve(ledger: AccountingLedger, title: Optional[str] = None) -> go.Figure:
        """Plot equity curve.
        
        Args:
            ledger: Accounting ledger
            title: Chart title
        
        Returns:
            Plotly figure
        """
        df = ledger.get_equity_dataframe()
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['equity'],
                mode='lines',
                name='Equity',
                line=dict(color='blue', width=2),
            )
        )
        
        # Add initial capital line
        fig.add_hline(
            y=ledger.initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="Initial Capital",
        )
        
        fig.update_layout(
            title=title or "Equity Curve",
            xaxis_title='Date',
            yaxis_title='Equity ($)',
            height=400,
        )
        
        return fig
    
    @staticmethod
    def plot_returns_distribution(ledger: AccountingLedger, title: Optional[str] = None) -> go.Figure:
        """Plot returns distribution histogram.
        
        Args:
            ledger: Accounting ledger
            title: Chart title
        
        Returns:
            Plotly figure
        """
        returns = ledger.calculate_returns() * 100  # Convert to percentage
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Histogram(
                x=returns,
                nbinsx=50,
                name='Returns',
                marker_color='lightblue',
            )
        )
        
        fig.update_layout(
            title=title or "Returns Distribution",
            xaxis_title='Return (%)',
            yaxis_title='Frequency',
            height=400,
        )
        
        return fig
    
    @staticmethod
    def create_performance_report(
        ledger: AccountingLedger,
        metrics: PerformanceMetrics,
    ) -> str:
        """Create a text performance report.
        
        Args:
            ledger: Accounting ledger
            metrics: Performance metrics
        
        Returns:
            Formatted performance report
        """
        report = f"""
Performance Report
==================

Initial Capital: ${ledger.initial_capital:,.2f}
Final Equity: ${ledger.equity_curve[-1][1] if ledger.equity_curve else ledger.initial_capital:,.2f}

Returns
-------
Total Return: {metrics.total_return:.2f}%
Annualized Return: {metrics.annualized_return:.2f}%

Risk Metrics
------------
Sharpe Ratio: {metrics.sharpe_ratio:.2f}
Maximum Drawdown: {metrics.max_drawdown:.2f}%

Trading Metrics
---------------
Win Rate: {metrics.win_rate:.2f}%
Profit Factor: {metrics.profit_factor:.2f}
Total Trades: {len(ledger.fills)}
"""
        return report
