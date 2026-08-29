# src/edgar

Everything that talks to the SEC.

Three responsibilities. Pull XBRL facts from Company Facts per CIK, keeping as-first-reported values rather than the current value of a concept. Pull filing dates from the submissions API, taking the first filing covering a period rather than an amendment. Resolve fiscal calendars, including non-standard year ends and 52- and 53-week retail years.

The fiscal-calendar work is unglamorous and is a real source of label noise, which is why it lives in its own module with its own tests rather than being inlined wherever a quarter needs resolving.

No API key is required. Respect the SEC's rate limits and declare a User-Agent.
