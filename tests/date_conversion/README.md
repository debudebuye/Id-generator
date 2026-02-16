# Ethiopian Date Conversion Tests

This directory contains test and debug scripts for the Ethiopian ↔ Gregorian date conversion implementation.

## Main Test File

- **test_date_conversion.py** - Comprehensive test suite for date conversion
  - Tests Ethiopian → Gregorian conversion
  - Tests Gregorian → Ethiopian conversion
  - Tests round-trip conversion
  - Tests leap year handling
  - Tests edge cases

## Debug Scripts

These scripts were used during development to debug and verify the algorithm:

- **debug_jdn.py** - Debug Julian Day Number calculation
- **debug_reverse.py** - Debug reverse conversion (JDN → Ethiopian)
- **verify_jdn_gregorian.py** - Verify JDN to Gregorian conversion
- **verify_algorithm.py** - Verify algorithm correctness against known facts

## Analysis Scripts

- **check_leap_formula.py** - Analyze leap year formula correctness
- **check_sept_11_2022.py** - Verify specific date (Sept 11, 2022)
- **derive_correct_formula.py** - Derive the correct formula from first principles
- **find_correct_epoch.py** - Calculate the correct epoch constant
- **final_check.py** - Final verification before implementation

## Running Tests

To run the main test suite:

```bash
python tests/date_conversion/test_date_conversion.py
```

## Implementation

The actual implementation is in:
- `app/utils/date_utils.py`

## Documentation

See `docs/date_conversion/` for detailed documentation on the algorithm and implementation decisions.
