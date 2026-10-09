# Ezplog

[![PyPI version](https://img.shields.io/pypi/v/ezplog?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/ezplog/)
[![Python versions](https://img.shields.io/pypi/pyversions/ezplog?style=flat&logo=python&logoColor=white)](https://pypi.org/project/ezplog/)
[![PyPI status](https://img.shields.io/pypi/status/ezplog?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/ezplog/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat&logo=github&logoColor=white)](https://github.com/neuraaak/ezplog/blob/main/LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/neuraaak/ezplog/ci.yml?style=flat&label=ci&logo=githubactions&logoColor=white)](https://github.com/neuraaak/ezplog/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue?style=flat&logo=materialformkdocs&logoColor=white)](https://neuraaak.github.io/ezplog/)
[![uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9?style=flat&logo=uv&logoColor=white)](https://github.com/astral-sh/uv)
[![linter](https://img.shields.io/badge/linter-ruff-D7FF64?style=flat&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![type checker](https://img.shields.io/badge/type%20checker-ty-261230?style=flat&logo=astral&logoColor=white)](https://github.com/astral-sh/ty)
[![tests](https://img.shields.io/badge/tests-pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)](https://github.com/pytest-dev/pytest)

![Ezplog Logo](https://raw.githubusercontent.com/neuraaak/ezplog/refs/heads/main/docs/assets/logo-min.png)

**ezplog** is a modern Python logging framework combining Rich console rendering and loguru file logging with an explicit app/lib compatibility model.

## 📦 Installation

```bash
# With uv (recommended)
uv add ezplog

# With pip
pip install ezplog
```

Or from source:

```bash
git clone https://github.com/neuraaak/ezplog.git
cd ezplog

uv pip install -e .   # uv
pip install -e .      # pip
```

## 🚀 Quick Start

```python
from ezplog import Ezpl

# Initialize once in the application entrypoint
ezpl = Ezpl(log_file="app.log", hook_logger=True, hook_printer=True)
printer = ezpl.get_printer()
logger = ezpl.get_logger()

# Console output (Rich formatting)
printer.info("Information message")
printer.success("Operation completed!")
printer.warning("Warning message")

# File logging (loguru)
logger.info("Logged to file")

# Advanced features
printer.wizard.success_panel("Success", "Operation completed")
printer.wizard.table([{"Name": "Alice", "Age": 30}], title="Users")
```

## 🎯 Key Features

- **✅ Singleton Pattern**: One global instance for the whole application
- **✅ Rich Console Output**: Colors, panels, tables, JSON, and progress bars
- **✅ File Logging**: Rotation, retention, and compression via loguru
- **✅ Explicit Compatibility Hooks**: Fine control between app mode and lib mode
- **✅ Configuration Management**: Arguments, environment variables, file, and runtime updates
- **✅ CLI Tools**: Commands for logs and configuration
- **✅ Full Type Hints**: Complete typing support for IDEs and linters
- **✅ Robust Fallbacks**: Safe behavior even with problematic message objects

## 📚 Documentation

Complete documentation is available at **[neuraaak.github.io/ezplog](https://neuraaak.github.io/ezplog/)**

| Section                                                                   | Description                                    |
| ------------------------------------------------------------------------- | ---------------------------------------------- |
| **[Getting Started](https://neuraaak.github.io/ezplog/getting-started/)** | Installation, basic usage, and first steps     |
| **[Concepts](https://neuraaak.github.io/ezplog/concepts/)**               | Design rationale, trade-offs, and architecture |
| **[API Reference](https://neuraaak.github.io/ezplog/api/)**               | Complete API documentation with examples       |
| **[CLI Reference](https://neuraaak.github.io/ezplog/cli/)**               | Command-line interface guide                   |
| **[User Guides](https://neuraaak.github.io/ezplog/guides/)**              | Configuration, development, and testing guides |
| **[Examples](https://neuraaak.github.io/ezplog/examples/)**               | Practical examples and demonstrations          |

## 🧪 Testing

Comprehensive test suite covering unit, integration, and robustness scenarios.
Coverage is generated automatically in documentation workflows.

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest tests/

# Run specific test types
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/robustness/

# With coverage
uv run pytest --cov=src/ezplog --cov-report=term --cov-report=html
```

See **[Testing Guide](https://neuraaak.github.io/ezplog/guides/testing/)** for complete details.

## 🛠️ Development Setup

For contributors and developers:

```bash
# Install in development mode with all dependencies
uv sync --extra dev --extra docs --extra test

# Install pre-commit hooks (code formatting, linting)
uv run pre-commit install

# Run quality checks
uv run ruff check src tests
uv run ty check
```

Source code uses a `src/` layout (`src/ezplog`).

**Git Hooks:**

- **pre-commit**: Automatically formats and lints code before commit

See **[Development Guide](https://neuraaak.github.io/ezplog/guides/development/)** for full details.

## 🎨 Main Components

- **`Ezpl`**: Singleton main class for centralized logging management
- **`EzPrinter`** (alias: `Printer`): Rich-based console output with pattern format
- **`EzLogger`** (alias: `Logger`): loguru-based file logging with rotation support
- **`RichWizard`**: Advanced Rich display (panels, tables, JSON, progress bars)
- **`ConfigurationManager`**: Centralized configuration management

## 📦 Dependencies

- **rich>=13.0.0** – Beautiful console output and formatting
- **loguru>=0.7.2** – Modern and powerful file logging
- **click>=8.0.0** – CLI framework

## 🔧 Quick API Reference

```python
from ezplog import Ezpl, Printer, Logger

ezpl = Ezpl(hook_logger=True, hook_printer=True)
printer: Printer = ezpl.get_printer()
logger: Logger = ezpl.get_logger()

# Console methods
printer.info(), printer.success(), printer.warning(), printer.error()
printer.trace(), printer.exception()
printer.tip(), printer.system(), printer.install()  # Pattern methods
printer.wizard.panel(), printer.wizard.table(), printer.wizard.json()

# File logging
logger.info(), logger.debug(), logger.warning(), logger.error()
logger.trace(), logger.exception()

# Configuration
ezpl.set_level("DEBUG")
ezpl.configure(log_rotation="10 MB", log_retention="7 days")
ezpl.set_compatibility_hooks(hook_logger=True, logger_names=["vendor.payment"])
```

## 💻 CLI Usage

The `ezpl` command provides tools for log inspection and configuration management.

```bash
# View recent log entries
ezpl logs view --lines 50

# Search for errors across log files
ezpl logs search --pattern "error|exception" --level ERROR

# Export logs to JSON
ezpl logs export --format json --output logs.json

# Read or update configuration
ezpl config get --show-env
ezpl config set log-level DEBUG

# Open the documentation site
ezpl docs
```

See the **[CLI Reference](https://neuraaak.github.io/ezplog/cli/)** for the full command and option listing.

## 🛡️ Robustness

Ezpl is designed to never crash, even with problematic input:

- Automatic string conversion for non-string messages
- Robust error handling in formatters
- Safe handling of special characters and Unicode
- Graceful fallbacks for all error cases

## 📝 License

MIT License – See [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [https://neuraaak.github.io/ezplog/](https://neuraaak.github.io/ezplog/)
- **Repository**: [https://github.com/neuraaak/ezplog](https://github.com/neuraaak/ezplog)
- **PyPI**: [https://pypi.org/project/ezplog/](https://pypi.org/project/ezplog/)
- **Issues**: [GitHub Issues](https://github.com/neuraaak/ezplog/issues)

---

**ezplog** - Modern, typed, robust and beautiful logging for Python.
