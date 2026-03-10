# Very small shim implementing LooseVersion used by some packages
from distutils.version import LooseVersion as _LooseVersion  # try stdlib first

class LooseVersion(_LooseVersion):
    pass

# If stdlib distutils is absent (Python 3.12+), fallback to packaging.version
try:
    from distutils.version import LooseVersion as _LooseVersion
except Exception:
    try:
        from packaging.version import Version as _Version

        class LooseVersion:
            def __init__(self, v):
                self.v = _Version(v)
            def __lt__(self, other):
                return self.v < _Version(other)
            def __gt__(self, other):
                return self.v > _Version(other)
            def __str__(self):
                return str(self.v)
    except Exception:
        # last resort: naive implementation
        class LooseVersion:
            def __init__(self, v):
                self.v = v
            def __lt__(self, other):
                return str(self.v) < str(other)
            def __gt__(self, other):
                return str(self.v) > str(other)
            def __str__(self):
                return str(self.v)
