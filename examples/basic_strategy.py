"""Example demonstrating TradePy usage."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from tradepy.config import Config
from tradepy.data import OHLCV, DataCache
from tradepy.signal import SimpleMovingAverageCrossover
from tradepy.portfolio import Portfolio, EqualWeightPortfolio, Position
from tradepy.execution import ExecutionEngine, OrderSide
from tradepy.accounting import AccountingLedger
from tradepy.analytics import Analytics


def create_sample_data(symbol: str, days: int = 252) -> OHLCV:
    """Create sample OHLCV data for demonstration.
    
    Args:
        symbol: Ticker symbol
        days: Number of days of data
    
    Returns:
        Sample OHLCV data
    """
    # Create dates
    start_date = datetime(2024, 1, 1)
    dates = pd.date_range(start_date, periods=days, freq='D').to_numpy()
    
    # Generate synthetic price data with trend and noise
    np.random.seed(42)
    trend = np.linspace(100, 150, days)
    noise = np.random.normal(0, 2, days).cumsum()
    close = trend + noise
    
    # Generate OHLC from close prices
    high = close * (1 + np.random.uniform(0.01, 0.03, days))
    low = close * (1 - np.random.uniform(0.01, 0.03, days))
    open_prices = close * (1 + np.random.uniform(-0.01, 0.01, days))
    
    # Generate volume
    volume = np.random.randint(100000, 1000000, days)
    
    return OHLCV(
        symbol=symbol,
        dates=dates,
        open=open_prices,
        high=high,
        low=low,
        close=close,
        volume=volume.astype(float),
    )


def main() -> None:
    """Run complete trading strategy example."""
    print("=" * 60)
    print("TradePy - Complete Trading Strategy Example")
    print("=" * 60)
    print()
    
    # 1. Configuration with deterministic seed
    print("1. Setting up configuration...")
    config = Config(random_seed=42)
    cache = DataCache(config.cache)
    print(f"   Random seed: {config.random_seed}")
    print(f"   Cache format: {config.cache.format}")
    print()
    
    # 2. Create or load data
    print("2. Creating sample OHLCV data...")
    symbol = "DEMO"
    ohlcv = create_sample_data(symbol, days=252)
    print(f"   Symbol: {ohlcv.symbol}")
    print(f"   Data points: {len(ohlcv.dates)}")
    print(f"   Date range: {ohlcv.dates[0]} to {ohlcv.dates[-1]}")
    print()
    
    # Save to cache
    print("3. Caching data...")
    cache.save(ohlcv)
    print(f"   Saved to: {cache._get_cache_path(symbol)}")
    print()
    
    # 3. Generate signals
    print("4. Generating trading signals...")
    signal_generator = SimpleMovingAverageCrossover(fast_period=20, slow_period=50)
    signal = signal_generator.generate(ohlcv)
    
    long_signals = (signal.values > 0).sum()
    short_signals = (signal.values < 0).sum()
    neutral_signals = (signal.values == 0).sum()
    
    print(f"   Fast MA: {signal_generator.fast_period} days")
    print(f"   Slow MA: {signal_generator.slow_period} days")
    print(f"   Long signals: {long_signals}")
    print(f"   Short signals: {short_signals}")
    print(f"   Neutral signals: {neutral_signals}")
    print()
    
    # 4. Initialize portfolio
    print("5. Initializing portfolio...")
    initial_capital = 100000.0
    portfolio = Portfolio(cash=initial_capital, positions={})
    portfolio_manager = EqualWeightPortfolio(max_positions=10)
    print(f"   Initial capital: ${initial_capital:,.2f}")
    print()
    
    # 5. Set up execution
    print("6. Setting up execution engine...")
    execution_engine = ExecutionEngine(commission_rate=0.001)  # 0.1% commission
    print(f"   Commission rate: {execution_engine.commission_rate * 100:.2f}%")
    print()
    
    # 6. Set up accounting
    print("7. Initializing accounting ledger...")
    ledger = AccountingLedger(initial_capital=initial_capital)
    ledger.record_equity(ohlcv.dates[0], initial_capital)
    print(f"   Initial equity recorded")
    print()
    
    # 7. Run backtest simulation
    print("8. Running backtest...")
    for i in range(50, len(ohlcv.dates)):  # Start after MA warmup
        current_date = ohlcv.dates[i]
        current_price = ohlcv.close[i]
        
        # Create signal for current point
        current_signal = SimpleMovingAverageCrossover(fast_period=20, slow_period=50)
        current_ohlcv = OHLCV(
            symbol=symbol,
            dates=ohlcv.dates[:i+1],
            open=ohlcv.open[:i+1],
            high=ohlcv.high[:i+1],
            low=ohlcv.low[:i+1],
            close=ohlcv.close[:i+1],
            volume=ohlcv.volume[:i+1],
        )
        sig = current_signal.generate(current_ohlcv)
        
        # Get target weights
        current_prices = {symbol: current_price}
        target_weights = portfolio_manager.update(portfolio, sig, current_prices)
        
        # Rebalance portfolio
        fills = execution_engine.rebalance(
            portfolio,
            target_weights,
            current_prices,
            current_date,
        )
        
        # Update portfolio positions
        for fill in fills:
            ledger.add_fill(fill)
            if fill.order.symbol not in portfolio.positions:
                portfolio.positions[fill.order.symbol] = Position(
                    symbol=symbol,
                    shares=0,
                    entry_price=fill.fill_price,
                    current_price=fill.fill_price,
                )
            
            position = portfolio.positions[fill.order.symbol]
            if fill.order.side == OrderSide.BUY:
                position.shares += fill.fill_shares
            else:
                position.shares -= fill.fill_shares
            position.current_price = fill.fill_price
            
            # Update cash
            if fill.order.side == OrderSide.BUY:
                portfolio.cash -= fill.total_cost
            else:
                portfolio.cash += fill.fill_value - fill.commission
        
        # Update position prices
        for pos_symbol, position in portfolio.positions.items():
            position.current_price = current_prices.get(pos_symbol, position.current_price)
        
        # Record equity
        ledger.record_equity(current_date, portfolio.equity)
    
    print(f"   Backtest complete: {len(ledger.fills)} trades executed")
    print()
    
    # 8. Calculate performance metrics
    print("9. Calculating performance metrics...")
    metrics = ledger.calculate_metrics(risk_free_rate=0.02)
    
    print(f"   Final equity: ${portfolio.equity:,.2f}")
    print(f"   Total return: {metrics.total_return:.2f}%")
    print(f"   Annualized return: {metrics.annualized_return:.2f}%")
    print(f"   Sharpe ratio: {metrics.sharpe_ratio:.2f}")
    print(f"   Max drawdown: {metrics.max_drawdown:.2f}%")
    print(f"   Win rate: {metrics.win_rate:.2f}%")
    print(f"   Profit factor: {metrics.profit_factor:.2f}")
    print()
    
    # 9. Generate report
    print("10. Performance Report")
    print("-" * 60)
    report = Analytics.create_performance_report(ledger, metrics)
    print(report)
    
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
