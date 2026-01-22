#!/bin/bash
# Test code quality checks across all supported Python versions (3.10+)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python versions to test
PYTHON_VERSIONS=("3.10" "3.11" "3.12" "3.13" "3.14")

# Results tracking (using simple arrays)
RESULTS_VERSION=()
RESULTS_STATUS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PiKaraoke Code Quality Multi-Version Testing${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Function to test a specific Python version
test_python_version() {
    local py_version=$1
    local py_cmd="python${py_version}"
    
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo -e "${YELLOW}Testing Python ${py_version}${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    
    # Check if Python version exists
    if ! command -v "$py_cmd" &> /dev/null; then
        echo -e "${RED}✗ Python ${py_version} not found, skipping...${NC}"
        RESULTS_VERSION+=("$py_version")
        RESULTS_STATUS+=("SKIPPED")
        return 1
    fi
    
    # Get actual Python version
    local actual_version=$($py_cmd --version 2>&1)
    echo -e "Found: ${actual_version}"
    
    # Create virtualenv name
    local venv_name=".venv_py${py_version}"
    
    # Clean up old venv if exists
    if [ -d "$venv_name" ]; then
        echo "Removing old virtualenv..."
        rm -rf "$venv_name"
    fi
    
    # Create new virtualenv
    echo "Creating virtualenv for Python ${py_version}..."
    $py_cmd -m venv "$venv_name"
    
    # Activate virtualenv
    source "$venv_name/bin/activate"
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip -q
    
    # Install project dependencies
    echo "Installing project dependencies..."
    pip install -e . -q
    
    # Install pre-commit
    echo "Installing pre-commit..."
    pip install pre-commit -q
    
    # Install pre-commit hooks
    echo "Installing pre-commit hook environments..."
    pre-commit install-hooks --config code_quality/.pre-commit-config.yaml 2>&1 | grep -E "(Installing|Installed|ERROR)" || true
    
    # Run code quality checks
    echo ""
    echo -e "${YELLOW}Running code quality checks...${NC}"
    echo ""
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if pre-commit run --all-files --config code_quality/.pre-commit-config.yaml; then
        echo ""
        echo -e "${GREEN}✓ All checks passed for Python ${py_version}!${NC}"
        RESULTS_VERSION+=("$py_version")
        RESULTS_STATUS+=("PASSED")
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo ""
        echo -e "${RED}✗ Some checks failed for Python ${py_version}${NC}"
        RESULTS_VERSION+=("$py_version")
        RESULTS_STATUS+=("FAILED")
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    # Deactivate virtualenv
    deactivate
    
    # Clean up venv to save space
    echo "Cleaning up virtualenv..."
    rm -rf "$venv_name"
    
    echo ""
}

# Test each Python version
for version in "${PYTHON_VERSIONS[@]}"; do
    test_python_version "$version" || true
    echo ""
done

# Print summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

for i in "${!RESULTS_VERSION[@]}"; do
    version="${RESULTS_VERSION[$i]}"
    result="${RESULTS_STATUS[$i]}"
    if [ "$result" = "PASSED" ]; then
        echo -e "Python ${version}: ${GREEN}✓ PASSED${NC}"
    elif [ "$result" = "FAILED" ]; then
        echo -e "Python ${version}: ${RED}✗ FAILED${NC}"
    else
        echo -e "Python ${version}: ${YELLOW}⊘ SKIPPED${NC}"
    fi
done

echo ""
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"
else
    echo -e "Failed: 0"
fi
echo ""

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
