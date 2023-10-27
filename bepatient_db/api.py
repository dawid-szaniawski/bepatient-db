import sqlite3
from typing import Any

from bepatient import Checker
from bepatient.waiter_src.comparators import COMP_DICT, COMPARATORS
from bepatient.waiter_src.waiter import wait_for_executor
from mysql.connector.cursor import CursorBase as MySqlCursor
from psycopg2.extensions import cursor as Psycopg2Cursor

from .sql_checkers import ResultType, SQLChecker
from .sql_executor import SQLExecutor


class SQLWaiter:
    """A utility class for creating and managing asynchronous SQL query response
    checkers.

    SQLWaiter is designed to be used in testing scenarios for applications that interact
    with SQL databases asynchronously. It provides a way to add response checkers and
    monitor the specified SQL query's response until a condition is met.

    Args:
        cursor (DbCursor): The database cursor to execute the SQL query.
        query (str): The SQL query to be executed.

    Example:
        ```python
        # Create an SQLWaiter instance
        waiter = SQLWaiter(cursor=my_sqlite3_cursor, query="SELECT * FROM users")

        # Add a response checker
        waiter.add_checker(
            expected_value=10, comparer=COMPARATORS.EQUALS, dict_path="user_count"
        )

        # Run the waiter
        waiter.run()

        # Get the final response
        result = waiter.get_result()
        ```"""
    def __init__(
        self, cursor: sqlite3.Cursor | Psycopg2Cursor | MySqlCursor, query: str
    ):
        self.executor = SQLExecutor(db_cursor=cursor, query=query)

    def add_checker(
        self,
        expected_value: Any,
        comparer: COMPARATORS,
        dict_path: str | None = None,
        search_query: str | None = None,
    ):
        """Add a response checker to the waiter.

        Args:
            expected_value (Any): The value to be compared against the response data.
            comparer (COMPARATORS): The comparer function or operator used for
                value comparison.
            dict_path (str | None, optional): The dot-separated path to the value in the
                response data. Defaults to None.
            search_query (str | None, optional): A search query to use to find the value
                in the response data. Defaults to None.

        Returns:
            self: updated RequestsWaiter instance."""
        self.executor.add_checker(
            SQLChecker(
                comparer=COMP_DICT[comparer],
                expected_value=expected_value,
                dict_path=dict_path,
                search_query=search_query,
            )
        )
        return self

    def add_custom_checker(self, checker: Checker):
        """Add a custom response checker to the waiter.
        This method allows users to add their own custom response checker by providing
        an object that inherits from the abstract base class Checker.

        Args:
            checker (Checker): An instance of a custom checker object that inherits
                from the Checker class.

        Returns:
            self: updated RequestsWaiter instance."""
        self.executor.add_checker(checker)
        return self

    def run(self, retries: int = 60, delay: int = 1, raise_error: bool = True):
        """Run the waiter and monitor the specified request or response.

        Args:
            retries (int, optional): The number of retries to perform. Defaults to 60.
            delay (int, optional): The delay between retries in seconds. Defaults to 1.
            raise_error (bool): raises WaiterConditionWasNotMet.

        Returns:
            self: updated RequestsWaiter instance.

        Raises:
            WaiterConditionWasNotMet: if the condition is not met within the specified
                number of attempts."""
        wait_for_executor(
            executor=self.executor,
            retries=retries,
            delay=delay,
            raise_error=raise_error,
        )
        return self

    def get_result(self) -> ResultType:
        """Get the final response containing the expected values.

        Returns:
            Response: final response containing the expected values."""
        return self.executor.get_result()
