"""A plugin for the 'bepatient' library adding database support"""
import logging

from bepatient_db.api import SQLWaiter

__version__ = "0.3.0"
__all__ = [
    "SQLWaiter",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
