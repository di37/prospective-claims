"""Console and file logging for the study.

Every script mirrors its stdout to ``reports/logs`` and announces each artifact it
writes. A run that takes an hour should leave a record of what it produced, and an
artifact in the repository should be traceable to the script that made it without
opening the script.

Import this rather than calling ``print`` directly.
"""

# region Imports
from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Iterator

from constants import LOGS_DIR, PROJECT_ROOT

# endregion

# region Script identity
def calling_script_stem() -> str:
    """Return the filename stem of the script that started the process.

    Returns:
        Stem of ``sys.argv[0]``, or ``"interactive"`` when there is none, which is
        the case inside a notebook or a REPL.
    """
    argv0 = sys.argv[0] if sys.argv else ""
    return Path(argv0).stem or "interactive"


# endregion

# region Console output
def banner(text: str) -> None:
    """Print a section header.

    Args:
        text: Header text.

    Returns:
        None.
    """
    print(f"\n{'=' * 78}\n{text}\n{'=' * 78}", flush=True)


def log_detail(text: str) -> None:
    """Print an indented detail line beneath a banner.

    Args:
        text: Detail text.

    Returns:
        None.
    """
    print(f"  {text}", flush=True)


def log_saved(path: Path) -> None:
    """Announce a written artifact.

    Args:
        path: Path that was written.

    Returns:
        None.
    """
    try:
        shown = path.relative_to(PROJECT_ROOT)
    except ValueError:
        shown = path
    print(f"  saved  {shown}", flush=True)


# endregion

# region File logging
class _Tee:
    """Write to an original stream and to a logfile at once.

    Attributes:
        stream: The stream being wrapped.
        handle: Open file handle receiving a copy of everything written.
    """

    def __init__(self, stream, handle) -> None:
        """Wrap ``stream``, mirroring writes into ``handle``.

        Args:
            stream: Original stdout or stderr.
            handle: Open, writable text file.
        """
        self.stream = stream
        self.handle = handle

    def write(self, text: str) -> int:
        """Write ``text`` to both destinations.

        Args:
            text: Text to write.

        Returns:
            Number of characters written to the original stream.
        """
        self.handle.write(text)
        return self.stream.write(text)

    def flush(self) -> None:
        """Flush both destinations.

        Returns:
            None.
        """
        self.handle.flush()
        self.stream.flush()


def tee_to_logfile() -> None:
    """Mirror stdout and stderr into a timestamped file under ``reports/logs``.

    Call once at the top of ``__main__``, before ``main()``, so a run that fails
    halfway still leaves a record of how far it got. The timestamp is the only
    nondeterministic value a script produces, which is why it lives in the logfile
    name rather than in any committed artifact.

    Returns:
        None.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    handle = (LOGS_DIR / f"{calling_script_stem()}_{stamp}.log").open("w", encoding="utf-8")
    sys.stdout = _Tee(sys.stdout, handle)
    sys.stderr = _Tee(sys.stderr, handle)


@contextmanager
def logged_run(label: str) -> Iterator[None]:
    """Bracket a stage with a banner and an elapsed-time line.

    Args:
        label: Stage name.

    Yields:
        None.
    """
    banner(label)
    start = perf_counter()
    try:
        yield
    finally:
        log_detail(f"elapsed {perf_counter() - start:.1f}s")


# endregion
