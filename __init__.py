# aiesda/__init__.py
import os

# 1. Read Version from the VERSION file
_pkg_root = os.path.dirname(os.path.abspath(__file__))
_version_file = os.path.join(_pkg_root, "VERSION")

if os.path.exists(_version_file):
    with open(_version_file, "r") as f:
        __version__ = f.read().strip()
else:
    __version__ = "dev"

# 2. Expose AIESDAConfig from pylib.aidaconf
# This allows users to do: import aiesda; config = aiesda.AIESDAConfig()
try:
    from .pylib.aidaconf import AIESDAConfig
except ImportError:
    # This prevents the package from crashing if dependencies aren't met yet
    pass
