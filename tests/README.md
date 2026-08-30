# tests

Run with `pytest` from the repository root. No dataset, no API key, no network, no GPU.

| File | Covers |
|---|---|
| `test_windows.py` | Section 5.5 resolved against fiscal calendars that do not match the calendar year |

Every fixture is synthetic. Testing against `reference/fiscal_quarters.csv` would give a suite that fails when the SEC reissues a filing rather than when the logic breaks, and the point of a test is to tell those apart.

The five calendar shapes are the ones that occur in the study set: a December year end where fiscal and calendar quarters coincide, a January year end where "next year" ends eleven months before the calendar year of the same name, a June year end, a 52/53-week retail calendar with the extra week added to the fourth quarter, and a retailer whose quarters are unequal.

Each fixture is modelled on a real shape in `reference/fiscal_quarters.csv` and then written out by hand. The 52/53-week fixture is Target's and Best Buy's calendar quarter for quarter. The uneven fixture is Kroger's, which runs a sixteen-week first quarter and three twelve-week quarters: the year is still 52 weeks and no quarter is a quarter of it, so any code placing a window by counting days from the start of the year lands in the wrong one.

Assertions carry the phrase and the expected period in the message, because a bare `assert window.offsets == (1, 1)` tells you a tuple differs and not which rule broke.

The suite was checked against deliberate breakage rather than assumed to work: making "next quarter" return two quarters fails 10 tests, letting a vague phrase default to next quarter fails 2, and letting "this year" include the quarter the claim was made in fails 3. A test that cannot fail is worse than no test, because it reports coverage it does not have.
