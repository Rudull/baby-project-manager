# src/version.py
"""Central version definition for Baby Project Manager.

Single source of truth for the application version. Read by the UI, the
updater (to compare against GitHub release tags) and the build scripts.
Release tags must match this value, prefixed with ``v`` (e.g. v0.5.1).
"""

__version__ = "0.5.1"
