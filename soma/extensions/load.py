"""
Pure SOMA Load Extension

Provides >load builtin for loading SOMA files with path searching.
Searches current directory first, then $SOMA_LIB environment variable.

All logic implemented in pure SOMA using Python FFI primitives.
"""


def register(vm):
    """Register extension (no Python builtins needed)."""
    pass  # Pure SOMA implementation


def get_soma_setup():
    """Return SOMA code implementing >load."""
    import os
    soma_file = os.path.join(os.path.dirname(__file__), 'load.soma')
    with open(soma_file, 'r') as f:
        return f.read()
