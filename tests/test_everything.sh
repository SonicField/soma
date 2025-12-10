#!/bin/bash
# SOMA Complete Test Suite
# Runs all tests: Python unit tests, SOMA tests, markdown tests, and doc build

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOMA_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$SOMA_ROOT"

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

echo "=============================================="
echo "SOMA Complete Test Suite"
echo "=============================================="
echo

# Track results
PYTHON_RESULT=0
SOMA_PASSED=0
SOMA_FAILED=0
SOMA_EXPECTED_FAIL=0
MARKDOWN_RESULT=0
DOCS_RESULT=0

# 1. Python Unit Tests
echo "1. Running Python unit tests..."
echo "----------------------------------------------"
if python3 -m unittest discover tests/ 2>&1 | tee /tmp/soma_python_tests.log | tail -5; then
    PYTHON_COUNT=$(grep -oP 'Ran \K\d+' /tmp/soma_python_tests.log || echo "?")
    echo -e "${GREEN}Python unit tests: ${PYTHON_COUNT} tests passed${NC}"
    PYTHON_RESULT=1
else
    echo -e "${RED}Python unit tests: FAILED${NC}"
fi
echo

# 2. SOMA Tests
echo "2. Running SOMA tests..."
echo "----------------------------------------------"
for f in tests/soma/*.soma; do
    basename_f=$(basename "$f")

    # Skip expected-failure tests (error validation tests)
    if [[ "$basename_f" == *"_errors"* ]] || [[ "$basename_f" == *"_error"* ]]; then
        # These tests are expected to fail - they test error handling
        if ! python3 examples/soma_runner/soma.py < "$f" 2>/dev/null >/dev/null; then
            echo -e "  ${GREEN}$basename_f: PASS (expected error)${NC}"
            SOMA_EXPECTED_FAIL=$((SOMA_EXPECTED_FAIL + 1))
        else
            echo -e "  ${RED}$basename_f: FAIL (should have errored)${NC}"
            SOMA_FAILED=$((SOMA_FAILED + 1))
        fi
    else
        if python3 examples/soma_runner/soma.py < "$f" 2>/dev/null >/dev/null; then
            echo -e "  ${GREEN}$basename_f: PASS${NC}"
            SOMA_PASSED=$((SOMA_PASSED + 1))
        else
            echo -e "  ${RED}$basename_f: FAIL${NC}"
            SOMA_FAILED=$((SOMA_FAILED + 1))
        fi
    fi
done
echo
echo "SOMA tests: $SOMA_PASSED passed, $SOMA_EXPECTED_FAIL expected failures, $SOMA_FAILED failed"
echo

# 3. Markdown Extension Tests
echo "3. Running markdown extension tests..."
echo "----------------------------------------------"
if python3 -m unittest tests.test_markdown_extension 2>&1 | tee /tmp/soma_markdown_tests.log | tail -5; then
    MARKDOWN_COUNT=$(grep -oP 'Ran \K\d+' /tmp/soma_markdown_tests.log || echo "?")
    echo -e "${GREEN}Markdown tests: ${MARKDOWN_COUNT} tests passed${NC}"
    MARKDOWN_RESULT=1
else
    echo -e "${RED}Markdown tests: FAILED${NC}"
fi
echo

# 4. Documentation Build
echo "4. Building documentation..."
echo "----------------------------------------------"
if [ -f build_docs.sh ]; then
    if ./build_docs.sh 2>&1 | tee /tmp/soma_docs_build.log | tail -5; then
        DOCS_COUNT=$(grep -oP 'Rendered \K\d+' /tmp/soma_docs_build.log || echo "?")
        echo -e "${GREEN}Documentation: ${DOCS_COUNT} files rendered${NC}"
        DOCS_RESULT=1
    else
        echo -e "${RED}Documentation build: FAILED${NC}"
    fi
else
    echo -e "${YELLOW}Documentation build: SKIPPED (no build_docs.sh)${NC}"
    DOCS_RESULT=1
fi
echo

# Summary
echo "=============================================="
echo "Summary"
echo "=============================================="
TOTAL_FAILURES=0

if [ $PYTHON_RESULT -eq 1 ]; then
    echo -e "${GREEN}[PASS]${NC} Python unit tests"
else
    echo -e "${RED}[FAIL]${NC} Python unit tests"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi

if [ $SOMA_FAILED -eq 0 ]; then
    echo -e "${GREEN}[PASS]${NC} SOMA tests ($SOMA_PASSED passed, $SOMA_EXPECTED_FAIL expected failures)"
else
    echo -e "${RED}[FAIL]${NC} SOMA tests ($SOMA_FAILED failures)"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi

if [ $MARKDOWN_RESULT -eq 1 ]; then
    echo -e "${GREEN}[PASS]${NC} Markdown extension tests"
else
    echo -e "${RED}[FAIL]${NC} Markdown extension tests"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi

if [ $DOCS_RESULT -eq 1 ]; then
    echo -e "${GREEN}[PASS]${NC} Documentation build"
else
    echo -e "${RED}[FAIL]${NC} Documentation build"
    TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
fi

echo
if [ $TOTAL_FAILURES -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$TOTAL_FAILURES test suite(s) failed${NC}"
    exit 1
fi
