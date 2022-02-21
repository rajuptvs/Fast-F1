"""
:mod:`fastf1` - Package functions
=================================
Available functions directly accessible from fastf1 package

.. autofunction:: fastf1.core.get_session
    :noindex:

.. autofunction:: fastf1.api.Cache.enable_cache
    :noindex:

.. autofunction:: fastf1.api.Cache.clear_cache
    :noindex:

"""
from fastf1.events import get_session, get_testing_session, get_event_schedule  # noqa: F401
from fastf1.api import Cache  # noqa: F401
from fastf1 import legacy  # noqa: F401
from fastf1.version import __version__   # noqa: F401
