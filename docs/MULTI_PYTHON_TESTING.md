# Multi-Python Version Testing

This directory contains tools for testing PiKaraoke code quality across all supported Python versions (3.10+).

## Quick Start

### Using the Bash Script (Recommended for macOS/Linux)

```bash
./test_all_python_versions.sh
```

This script will:
1. Detect available Python versions (3.10, 3.11, 3.12, 3.13, 3.14)
2. Create a fresh virtual environment for each version
3. Install all dependencies in each environment
4. Run all pre-commit code quality checks
5. Clean up virtual environments after testing
6. Display a summary of results

### Using Tox (Alternative Method)

If you have tox installed:

```bash
# Install tox first
pip install tox

# Test all Python versions
tox

# Test specific Python version
tox -e py310  # or py311, py312, py313, py314

# Run tests in parallel
tox -p auto
```

## Prerequisites

### Required Python Versions

Install the required Python versions using pyenv:

```bash
# Install pyenv if not already installed
brew install pyenv

# Install Python versions
pyenv install 3.10.19
pyenv install 3.11.11
pyenv install 3.12.8
pyenv install 3.13.3
pyenv install 3.14.0

# Make them available globally
pyenv global system 3.10.19 3.11.11 3.12.8 3.13.3 3.14.0
```

### Verify Installation

```bash
python3.10 --version  # Should show Python 3.10.x
python3.11 --version  # Should show Python 3.11.x
python3.12 --version  # Should show Python 3.12.x
python3.13 --version  # Should show Python 3.13.x
python3.14 --version  # Should show Python 3.14.x
```

## What Gets Tested

Each Python version runs the following checks:

1. **Remove Unused Python Imports** (pycln)
2. **Sort Python Imports** (isort)
3. **Format Python Code** (black)
4. **Lint Python Code** (pylint)
5. **Security Linting** (bandit)
6. **Format Markdown Files** (mdformat)
7. **File Validation** (YAML, JSON, TOML)
8. **Type Checking** (mypy)
9. **Code Quality Checks** (AST, debug statements, etc.)

## Understanding Results

### Success
```
Python 3.10: ✓ PASSED
Python 3.11: ✓ PASSED
Python 3.12: ✓ PASSED
Python 3.13: ✓ PASSED
Python 3.14: ✓ PASSED
```

All code quality checks passed across all Python versions!

### Failure
```
Python 3.12: ✗ FAILED
```

Check the detailed output above the summary to see which specific check failed and why.

### Skipped
```
Python 3.13: ⊘ SKIPPED
```

Python version not found on system - install it using pyenv.

## Continuous Integration

These tests ensure that:
- Code works correctly across all supported Python versions
- No version-specific syntax issues
- All dependencies are compatible
- Code quality standards are maintained

## Troubleshooting

### "Python X.Y not found"

Install the missing Python version:
```bash
pyenv install 3.X.Y
```

### "pre-commit hook failed"

The script will show detailed error output. Common issues:
- Syntax errors in code
- Import issues
- Formatting violations
- Security warnings

### Clean Up Failed Tests

If a test is interrupted, clean up manually:
```bash
rm -rf .venv_py3.*
```

## Performance Notes

- Each Python version test takes ~2-3 minutes
- Total runtime for all 5 versions: ~10-15 minutes
- Virtual environments are automatically cleaned up after each test
- Tests run sequentially to avoid resource contention

## Integration with CI/CD

Add to GitHub Actions workflow:

```yaml
name: Multi-Python Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13', '3.14']
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e .
      - run: pip install pre-commit
      - run: pre-commit run --all-files --config code_quality/.pre-commit-config.yaml
```

## See Also

- [Pre-commit Configuration](../code_quality/.pre-commit-config.yaml)
- [Tox Configuration](../tox.ini)
- [Python Version Requirements](../pyproject.toml)
