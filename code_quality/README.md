# Code Quality Tools

This directory contains configuration files for all code quality, security, and testing tools used in the PiKaraoke project.

## Tools Overview

### Python Code Quality

#### Black (Code Formatter)

- **Config:** Inline in `.pre-commit-config.yaml`
- **Purpose:** Enforces consistent Python code formatting
- **Line Length:** 100 characters
- **Usage:** `black --line-length 100 pikaraoke/`

#### isort (Import Sorter)

- **Config:** Inline in `.pre-commit-config.yaml`
- **Purpose:** Sorts and organizes Python imports
- **Profile:** Black-compatible
- **Usage:** `isort --profile black pikaraoke/`

#### pycln (Unused Import Remover)

- **Config:** Inline in `.pre-commit-config.yaml`
- **Purpose:** Removes unused Python imports
- **Usage:** `pycln pikaraoke/`

#### pylint (Python Linter)

- **Config:** `.pylintrc`
- **Purpose:** Static code analysis for Python
- **Mode:** Errors-only (suppresses warnings)
- **Usage:** `pylint --rcfile=code_quality/.pylintrc pikaraoke/`

### Security

#### Bandit (Security Linter)

- **Config:** `.bandit`
- **Purpose:** Detects common security issues in Python code
- **Checks:** SQL injection, command injection, hardcoded passwords, etc.
- **Skipped Tests:**
  - B603: subprocess without shell=True (needed for some commands)
  - B607: Starting process with partial path (system commands)
- **Usage:** `bandit -c code_quality/.bandit -r pikaraoke/`

#### Safety (Dependency Scanner)

- **Config:** None (uses default)
- **Purpose:** Checks dependencies for known security vulnerabilities
- **Usage:** `safety check --file pyproject.toml`

### Type Checking

#### MyPy (Static Type Checker)

- **Config:** `.mypy.ini`
- **Purpose:** Optional static type checking for Python
- **Adoption:** Gradual (starting with `lib/database.py` and `lib/args.py`)
- **Usage:** `mypy --config-file=code_quality/.mypy.ini pikaraoke/`

### Documentation

#### Markdownlint (Markdown Linter)

- **Config:** `.markdownlint.yaml`
- **Purpose:** Enforces consistent Markdown formatting
- **Usage:** Runs automatically via mdformat in pre-commit

#### Docstring Coverage

- **Config:** `.docstr.yaml`
- **Purpose:** Measures documentation coverage
- **Threshold:** 0% (informational only)
- **Usage:** `docstr-coverage`

#### YAML Lint

- **Config:** `.yamllint`
- **Purpose:** Validates YAML file syntax and style
- **Usage:** Runs automatically in pre-commit

## Running All Checks

### Pre-commit (Recommended)

Install pre-commit hooks to run automatically before each commit:

```bash
pre-commit install --config code_quality/.pre-commit-config.yaml
```

Run all checks manually:

```bash
pre-commit run --all-files --config code_quality/.pre-commit-config.yaml
```

### Individual Tools

```bash
# Python formatting and linting
black --line-length 100 pikaraoke/
isort --profile black pikaraoke/
pycln pikaraoke/
pylint --rcfile=code_quality/.pylintrc pikaraoke/

# Security
bandit -c code_quality/.bandit -r pikaraoke/
safety check

# Type checking (optional)
mypy --config-file=code_quality/.mypy.ini pikaraoke/

# Documentation
docstr-coverage
```

## CI/CD Integration

All checks run automatically in GitHub Actions on:

- Pull requests (opened or synchronized)
- Pushes to master branch

See `.github/workflows/ci.yml` for the complete CI pipeline.

## Adding New Checks

1. Add the tool to `pyproject.toml` dev dependencies
2. Create a configuration file in this directory (if needed)
3. Add the pre-commit hook to `.pre-commit-config.yaml`
4. Update this README
5. Update `.github/copilot-instructions.md`

## Skipping Checks

To skip specific checks during development:

```bash
# Skip all checks for a commit (use sparingly!)
git commit --no-verify

# Skip specific pre-commit hooks
SKIP=pylint,bandit pre-commit run --all-files
```

## Configuration Files

- `.bandit` - Bandit security scanner configuration
- `.docstr.yaml` - Docstring coverage configuration
- `.markdownlint.yaml` - Markdown linting rules
- `.mypy.ini` - MyPy type checker configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.pylintrc` - Pylint static analysis configuration
- `.yamllint` - YAML linting rules
