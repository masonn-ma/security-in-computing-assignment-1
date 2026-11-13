"""Boundary for the pinned official Ascon C implementation.

The shared-library build is intentionally kept explicit so an obsolete PyPI
implementation cannot be selected accidentally.
"""


def unavailable() -> None:
    raise RuntimeError(
        "Ascon requires the vendored official NIST SP 800-232 ascon-c "
        "implementation; build the ctypes binding before running"
    )
