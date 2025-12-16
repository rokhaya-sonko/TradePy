# TradePy

A clean, minimal-dependency Python library for quantitative trading with strict architectural separation.

## Features

- **Clean Architecture**: Strict separation of concerns (Signal → Portfolio → Execution → Accounting → Analytics)
- **Type Hints**: Comprehensive type annotations throughout
- **Minimal Dependencies**: Only numpy, pandas, plotly, sklearn, and optional xgboost
- **Deterministic**: Reproducible results with configurable random seeds
- **Well-Tested**: Comprehensive unit test coverage with pytest
- **Data Caching**: Efficient local caching with Parquet (preferred) and CSV (fallback)
- **Daily OHLCV**: Focus on daily bar data only

## Installation

```bash
pip install -e .
```

For development with testing:
```bash
pip install -e ".[dev]"
```

For XGBoost support:
```bash
pip install -e ".[xgboost]"
```

## Requirements

- Python 3.11+
- numpy >= 1.24.0
- pandas >= 2.0.0
- plotly >= 5.14.0
- scikit-learn >= 1.3.0

## Architecture

TradePy follows a strict separation of concerns:

### 1. Signal
Generate trading signals from market data.

```python
from tradepy.signal import SimpleMovingAverageCrossover
from tradepy.data import OHLCV

# Create signal generator
generator = SimpleMovingAverageCrossover(fast_period=20, slow_period=50)

# Generate signals from OHLCV data
signal = generator.generate(ohlcv_data)
```

### 2. Portfolio
Manage portfolio positions and weights.

```python
from tradepy.portfolio import EqualWeightPortfolio, Portfolio

# Create portfolio manager
manager = EqualWeightPortfolio(max_positions=10)

# Calculate target weights
portfolio = Portfolio(cash=10000.0, positions={})
weights = manager.update(portfolio, signal, current_prices)
```

### 3. Execution
Execute trades and manage orders.

```python
from tradepy.execution import ExecutionEngine, Order, OrderType, OrderSide

# Create execution engine
engine = ExecutionEngine(commission_rate=0.001)

# Execute order
order = Order(symbol="AAPL", side=OrderSide.BUY, shares=100.0)
fill = engine.execute(order, market_price=150.0, timestamp=datetime.now())

# Rebalance portfolio
fills = engine.rebalance(portfolio, target_weights, current_prices, timestamp)
```

### 4. Accounting
Track P&L, returns, and performance metrics.

```python
from tradepy.accounting import AccountingLedger

# Create ledger
ledger = AccountingLedger(initial_capital=10000.0)

# Record fills and equity
ledger.add_fill(fill)
ledger.record_equity(timestamp, portfolio.equity)

# Calculate performance metrics
metrics = ledger.calculate_metrics(risk_free_rate=0.02)
print(f"Total Return: {metrics.total_return:.2f}%")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2f}%")
```

### 5. Analytics
Analyze and visualize performance.

```python
from tradepy.analytics import Analytics

# Plot OHLCV with signals
fig = Analytics.plot_signals(ohlcv_data, signal)
fig.show()

# Plot equity curve
fig = Analytics.plot_equity_curve(ledger)
fig.show()

# Generate performance report
report = Analytics.create_performance_report(ledger, metrics)
print(report)
```

## Data Management

### OHLCV Data Structure

```python
from tradepy.data import OHLCV
import numpy as np
from datetime import datetime

# Create OHLCV data
ohlcv = OHLCV(
    symbol="AAPL",
    dates=np.array([datetime(2024, 1, i) for i in range(1, 6)]),
    open=np.array([100.0, 101.0, 102.0, 103.0, 104.0]),
    high=np.array([105.0, 106.0, 107.0, 108.0, 109.0]),
    low=np.array([99.0, 100.0, 101.0, 102.0, 103.0]),
    close=np.array([104.0, 105.0, 106.0, 107.0, 108.0]),
    volume=np.array([1000, 1100, 1200, 1300, 1400]),
)

# Convert to DataFrame
df = ohlcv.to_dataframe()

# Create from DataFrame
ohlcv = OHLCV.from_dataframe("AAPL", df)
```

### Data Caching

```python
from tradepy.config import Config, CacheConfig
from tradepy.data import DataCache
from pathlib import Path

# Configure cache
config = Config(
    random_seed=42,
    cache=CacheConfig(
        cache_dir=Path.home() / ".tradepy" / "cache",
        format="parquet",  # or "csv"
        enabled=True,
    )
)

# Use cache
cache = DataCache(config.cache)
cache.save(ohlcv)
loaded_data = cache.load("AAPL")
```

## Configuration

### Deterministic Seeds

```python
from tradepy.config import Config

# Set seed for reproducibility
config = Config(random_seed=42)
# This automatically sets numpy.random.seed and random.seed
```

### Custom Configuration

```python
from tradepy.config import Config, CacheConfig
from pathlib import Path

config = Config(
    random_seed=123,
    cache=CacheConfig(
        cache_dir=Path("/custom/cache/dir"),
        format="csv",
        enabled=True,
    )
)
```

## Testing

Run tests with pytest:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=tradepy --cov-report=html
```

## Development

The project structure:

```
tradepy/
├── __init__.py
├── config.py          # Configuration dataclasses
├── data.py            # OHLCV data and caching
├── signal/            # Signal generation
├── portfolio/         # Portfolio management
├── execution/         # Order execution
├── accounting/        # P&L and metrics
└── analytics/         # Visualization and analysis

tests/
├── test_config.py
├── test_data.py
├── test_signal.py
├── test_portfolio.py
├── test_execution.py
└── test_accounting.py
```

## License

MIT License

## Contributing

Contributions are welcome! Please ensure:
- Type hints are used everywhere
- Comprehensive docstrings are included
- Unit tests are provided for new functionality
- Code follows the existing architectural patterns