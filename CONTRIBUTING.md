# Contributing to TradePy

Thank you for your interest in contributing to TradePy! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/rokhaya-sonko/TradePy.git
cd TradePy
```

2. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Code Standards

### Type Hints
All code must include comprehensive type hints:
```python
def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe ratio."""
    ...
```

### Docstrings
All public classes, functions, and methods must have docstrings following Google style:
```python
def my_function(param1: str, param2: int) -> bool:
    """Short description of function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: Description of when this is raised
    """
    ...
```

### Architectural Principles

TradePy follows a strict separation of concerns:

1. **Signal**: Generate trading signals from market data
2. **Portfolio**: Manage portfolio positions and weights
3. **Execution**: Execute trades and manage orders
4. **Accounting**: Track P&L, returns, and accounting
5. **Analytics**: Analyze and visualize performance

Each module should have minimal dependencies on others and maintain clear boundaries.

## Testing

All new code must include unit tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tradepy --cov-report=html

# Run specific test file
pytest tests/test_signal.py
```

Aim for:
- High test coverage (>80%)
- Clear test names that describe what's being tested
- Independent tests that don't rely on execution order

## Submitting Changes

1. Create a new branch for your feature or fix
2. Make your changes following the code standards
3. Add tests for your changes
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

## Questions?

If you have questions, please open an issue on GitHub.
