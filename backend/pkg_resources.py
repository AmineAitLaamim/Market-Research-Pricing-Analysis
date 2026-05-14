# This file exists to satisfy imports that do `import pkg_resources` while
# running from /app (the Django project root).  It re-exports everything from
# the real setuptools pkg_resources so that libraries like playwright-stealth
# that call pkg_resources.resource_string() work correctly.
#
# Background: Python resolves imports relative to sys.path.  Because /app is
# first on sys.path inside the container, a bare `import pkg_resources` would
# find *this* file first.  We therefore import and re-export the real module.

import importlib
import sys

# Temporarily remove this file's directory from sys.path so we can import the
# *real* pkg_resources from setuptools (installed in /opt/venv).
_this_dir = __file__[:__file__.rfind('/')]
_patched = False
if _this_dir in sys.path:
    sys.path.remove(_this_dir)
    _patched = True

try:
    import pkg_resources as _real_pkg_resources  # noqa: E402
    from pkg_resources import *  # noqa: F401, F403
    from pkg_resources import (  # noqa: F401
        resource_string,
        resource_filename,
        resource_exists,
        resource_listdir,
        resource_stream,
        resource_isdir,
        working_set,
        require,
        get_distribution,
        DistributionNotFound,
        VersionConflict,
    )
except ImportError:
    # Absolute fallback: provide the minimal surface used by legacy code in
    # this project so startup does not crash even without setuptools.
    class DistributionNotFound(Exception):  # noqa: F811
        pass

    class VersionConflict(Exception):  # noqa: F811
        pass

    def get_distribution(_name):  # noqa: F811
        raise DistributionNotFound(_name)

    def resource_string(_package, _resource):
        raise NotImplementedError(
            "pkg_resources.resource_string is not available: "
            "setuptools is not installed in this environment."
        )

finally:
    if _patched:
        sys.path.insert(0, _this_dir)
