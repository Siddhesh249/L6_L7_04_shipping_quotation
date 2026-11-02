# L6_L7_04 — Shipping Quote

Lab 6: Code and Branch Coverage

## About

A small Python module that calculates shipping quotes by transport mode, parcel weights, and hazardous material rules, and inspects cargo pressure logs for depressurization leaks.

## Deliverables

| File | Description | Coverage Achieved |
|------|-------------|-------------------|
| `shipping_quote.py` | The module under test | - |
| `test_shipping_quote.py` | Starter test file (updated with full coverage suite) | 100% Line / 100% Branch |
| `CodeCoverageTest_shipping_quote.py` | Test suite designed for code coverage | 100% Line Coverage |
| `CodeCoverageTest_PES2UG24CS502_shipping_quote.py` | Student SRN alias for code coverage test suite | 100% Line Coverage |
| `code_coverage_analysis.png` | Terminal output screenshot for code coverage | 100% Line Coverage |
| `BranchCoverageTest_shipping_quote.py` | Comprehensive test suite for branch coverage | 100% Branch Coverage |
| `BranchCoverageTest_PES2UG24CS502_shipping_quote.py` | Student SRN alias for branch coverage test suite | 100% Branch Coverage |
| `branch_coverage_analysis.png` | Terminal output screenshot for branch coverage | 100% Branch Coverage |

## Running Coverage

### Code (Line) Coverage
```bash
coverage run -m pytest CodeCoverageTest_shipping_quote.py
coverage report -m
```

### Branch Coverage
```bash
coverage run --branch -m pytest BranchCoverageTest_shipping_quote.py
coverage report -m
```