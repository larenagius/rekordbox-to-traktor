"""Traktor NML I/O.

``safe_output`` has no third-party deps and is always importable. ``reader`` and
``writer`` depend on traktor-nml-utils / lxml and are imported lazily by callers.
"""

from . import safe_output

__all__ = ["safe_output"]
