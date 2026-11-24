# AI Usage Disclosure

<!--
Fill in this file before you submit. Submissions without it are not graded.
If you used no AI tools, delete everything below and write only:
No AI tools were used.
-->

## Reference Resources Used

## Websites and Books

- Python Module of the Week (pymotw.com) by Doug Hellmann for csv, re, datetime, argparse, logging, json, and pathlib
- W3Schools Python Tutorial (w3schools.com/python) for sets, dictionaries, lambda functions, and the sorted() function
- GeeksforGeeks articles on Python regular expressions and handling CSV files
- Think Python by Allen B. Downey for functions, tuples, dictionaries, and exception handling

## How I Used These Resources

- Used the PyMOTW csv and pathlib pages in csv_loader.py to read files line by line, skip comments and blank lines, and parse each row with csv.reader. I used a set of (flight_id, departure_datetime) tuples to detect duplicate flights.
- Used the GeeksforGeeks regex articles and the PyMOTW datetime page in validator.py to build the patterns for flight IDs, IATA codes, and timestamps, and to check real dates with datetime.strptime. I handled invalid prices with try/except and math.isfinite.
- Used the PyMOTW argparse, json, and logging pages in flight_parser.py to set up mutually exclusive input options (-i, -d, -j), save db.json and the response file, and write invalid rows to errors.log.
- Used W3Schools and Think Python in query.py for filtering with list comprehensions, sorting with sorted(key=lambda, reverse=...), and applying limit with slicing. I tested the edge cases with python tests/run_public_tests.py.
