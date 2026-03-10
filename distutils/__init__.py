# Minimal shim package to provide distutils.version for projects expecting it on Python 3.12+
# This package lives in the project and will be importable as `distutils` before the missing stdlib module.
__all__ = ['version']
