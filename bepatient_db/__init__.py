"""A plugin for the 'bepatient' library adding database support"""
import logging
from logging import NullHandler

from bepatient_db.api import SQLWaiter

__version__ = "0.1.0"
__all__ = [
    "SQLWaiter",
]

logging.getLogger(__name__).addHandler(NullHandler())
