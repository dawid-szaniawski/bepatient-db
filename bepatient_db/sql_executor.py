import sqlite3
from typing import TypeAlias

from bepatient.waiter_src.executor import Executor
from mysql.connector.cursor import CursorBase
from psycopg2.extensions import cursor


DbCursor: TypeAlias = sqlite3.Cursor | CursorBase | cursor


class SQLExecutor(Executor):
    """Initialize an SQLExecutor.

    Args:
        db_cursor (DbCursor): the database cursor
            with a cursor factory that returns dictionary objects.
        query (str): SQL query to be executed by the cursor.

    Note:
        The cursor object provided should have a cursor factory that returns
            dictionaries."""

    def __init__(
        self, db_cursor: DbCursor, query: str
    ):
        """Cursor should have cursor_factory that returns dict object"""
        super().__init__()
        self._cursor = db_cursor
        self._input: str = query

    def is_condition_met(self) -> bool:
        """Check whether the condition has been met.

        Returns:
            bool: True if the condition has been met, False otherwise."""
        self._result = self._cursor.execute(self._input).fetchall()

        self._failed_checkers = [
            checker for checker in self._checkers if not checker.check(self._result)
        ]

        if len(self._failed_checkers) == 0:
            return True
        return False
