"""rb2traktor: one-way Rekordbox -> Traktor 4 metadata sync.

Safety contract: this package NEVER writes to a live collection.nml. All output
goes to a sibling ``collection-merge.nml`` that the user swaps in manually.
"""

__version__ = "0.1.0"
