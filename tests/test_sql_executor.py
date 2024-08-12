from sqlite3 import Cursor

import pytest
from _pytest.logging import LogCaptureFixture
from bepatient.waiter_src.checkers.checker import Checker
from bepatient.waiter_src.exceptions.executor_exceptions import ExecutorIsNotReady

from bepatient_db.sql_executor import SQLExecutor


class TestSQLExecutor:
    def test_is_condition_met_returns_true_when_checker_pass(
        self,
        sqlite_db: Cursor,
        select_all_from_user_query: str,
        checker_true: Checker,
        caplog: LogCaptureFixture,
    ):
        logs = [
            (
                "bepatient_db.sql_executor",
                20,
                "Query send to database: SELECT * from user",
            )
        ]
        executor = SQLExecutor(
            db_cursor=sqlite_db, query=select_all_from_user_query
        ).add_checker(checker_true)

        assert executor.is_condition_met() is True
        assert caplog.record_tuples == logs

    def test_is_condition_met_returns_true_when_all_checkers_pass(
        self,
        sqlite_db: Cursor,
        select_all_from_user_query: str,
        checker_true: Checker,
    ):
        executor = (
            SQLExecutor(sqlite_db, select_all_from_user_query)
            .add_checker(checker_true)
            .add_checker(checker_true)
        )

        assert executor.is_condition_met() is True

    def test_is_condition_met_returns_false_when_checker_fail(
        self,
        sqlite_db: Cursor,
        select_all_from_user_query: str,
        checker_false: Checker,
    ):
        executor = SQLExecutor(sqlite_db, select_all_from_user_query).add_checker(
            checker_false
        )

        assert executor.is_condition_met() is False

    def test_is_condition_met_returns_false_when_not_all_checkers_pass(
        self,
        sqlite_db: Cursor,
        select_all_from_user_query: str,
        checker_true: Checker,
        checker_false: Checker,
    ):
        executor = SQLExecutor(sqlite_db, select_all_from_user_query).add_checker(
            checker_true
        )
        executor.add_checker(checker_false).add_checker(checker_true)

        assert executor.is_condition_met() is False

    def test_get_result_returns_select_all_from_user_query_result(
        self,
        sqlite_db: Cursor,
        checker_true: Checker,
    ):
        query = "SELECT title FROM tests WHERE author_id = 1"
        executor = SQLExecutor(sqlite_db, query).add_checker(checker_true)
        executor.is_condition_met()

        assert executor.get_result() is not None
        assert executor.get_result() == [{"title": "TEST_1"}]

    def test_get_result_raises_exception_when_condition_has_not_been_checked(
        self,
        sqlite_db: Cursor,
        select_all_from_user_query: str,
    ):
        executor = SQLExecutor(sqlite_db, select_all_from_user_query)
        msg = "The condition has not yet been checked."

        with pytest.raises(ExecutorIsNotReady, match=msg):
            executor.get_result()

    def test_error_message_returns_correct_message(
        self,
        sqlite_db: Cursor,
        select_all_from_user_query: str,
        checker_false: Checker,
    ):
        executor = SQLExecutor(sqlite_db, select_all_from_user_query).add_checker(
            checker_false
        )
        msg = (
            "The condition has not been met!"
            " | Failed checkers: (I'm falsy) | SELECT * from user"
        )
        executor.is_condition_met()

        assert executor.error_message() == msg

    def test_error_message_raises_exception_when_condition_has_not_been_checked(
        self,
        sqlite_db: Cursor,
        select_all_from_user_query: str,
    ):
        executor = SQLExecutor(sqlite_db, select_all_from_user_query)
        msg = "The condition has not yet been checked."

        with pytest.raises(ExecutorIsNotReady, match=msg):
            executor.error_message()
