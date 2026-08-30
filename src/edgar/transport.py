"""One place where the study talks to the SEC over HTTP.

Every request carries the same User-Agent, the same timeout, and the same retry
policy, because the SEC identifies clients by that header and rate-limits on it.
Spreading the transport across call sites is how a single impolite loop gets an
entire project blocked.

A 404 is a result, not a failure. The frames API returns it for an element that
does not exist in a period, and the company concept API returns it for a filer
that has never tagged one, so callers need to tell that apart from a timeout.
"""

# region Imports
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from constants import (
    SEC_MAX_RETRIES,
    SEC_REQUEST_DELAY_SECONDS,
    SEC_TIMEOUT_SECONDS,
    SEC_USER_AGENT,
)

# endregion

# region Transport
def get_json(url: str) -> tuple[dict | None, int | None, str | None]:
    """Fetch and decode one SEC endpoint, retrying transient failures.

    A 404 is returned immediately rather than retried, because it is a definite
    answer rather than a transport problem.

    Args:
        url: Fully formed request URL.

    Returns:
        Tuple of payload, HTTP status, and error description. A payload of None
        with a status of 404 means the resource does not exist; a payload of None
        with an error means every attempt failed.
    """
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})

    last_error: str | None = None
    for attempt in range(SEC_MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=SEC_TIMEOUT_SECONDS) as response:
                return json.load(response), 200, None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None, 404, None
            last_error = f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001  network failures are varied and all retryable
            last_error = type(exc).__name__
        time.sleep(SEC_REQUEST_DELAY_SECONDS * (attempt + 2))

    return None, None, last_error


# endregion
