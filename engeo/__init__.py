"""English -> Georgian dictionary lookup.

    >>> from engeo import lookup
    >>> lookup("Apple")["results"][0]["meanings"]
    ['ვაშლი']
"""

from .dictionary import Dictionary, lookup, suggest

__all__ = ["Dictionary", "lookup", "suggest"]
