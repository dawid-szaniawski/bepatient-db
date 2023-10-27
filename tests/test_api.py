import os
import sqlite3
import threading
from pathlib import Path
from time import sleep

import pytest
from _pytest.logging import LogCaptureFixture
from bepatient.waiter_src.comparators import is_equal
from bepatient.waiter_src.exceptions.waiter_exceptions import WaiterConditionWasNotMet

from bepatient_db.api import SQLWaiter
from bepatient_db.sql_checkers import SQLChecker


class TestSQLWaiter:
    def test_init(self, sqlite_db: sqlite3.Cursor, select_all_from_user_query: str):
        executor = SQLWaiter(
            cursor=sqlite_db, query=select_all_from_user_query
        ).executor
        exec_input = executor._input

        assert exec_input == select_all_from_user_query
        assert executor._cursor == sqlite_db

    def test_add_checker(
        self, sqlite_db: sqlite3.Cursor, select_all_from_user_query: str
    ):
        waiter = SQLWaiter(cursor=sqlite_db, query=select_all_from_user_query)
        executor = waiter.add_checker(
            expected_value="TEST",
            comparer="is_equal",
            dict_path="dict",
            search_query="query",
        ).executor

        checker = SQLChecker(
            comparer=is_equal,
            expected_value="TEST",
            dict_path="dict",
            search_query="query",
        )

        assert executor._checkers[0].__dict__ == checker.__dict__

    def test_add_custom_checker(
        self, sqlite_db: sqlite3.Cursor, select_all_from_user_query: str
    ):
        checker = SQLChecker(
            comparer=is_equal,
            expected_value="TEST",
            dict_path="dict",
            search_query="query",
        )
        waiter = SQLWaiter(cursor=sqlite_db, query=select_all_from_user_query)
        executor = waiter.add_custom_checker(checker).executor
        w_checker = executor._checkers[0]

        assert w_checker is checker

    def test_happy_path(self, sqlite_db: sqlite3.Cursor):
        waiter = SQLWaiter(cursor=sqlite_db, query="SELECT description FROM tests")
        waiter.add_checker(
            expected_value="DESC", comparer="is_equal", dict_path="2.description"
        )
        result = waiter.run(retries=1).get_result()
        assert result == [
            {"description": None},
            {"description": ""},
            {"description": "DESC"},
        ]

    def test_happy_path_with_custom_checker(
        self, sqlite_db: sqlite3.Cursor, select_all_from_user_query: str
    ):
        checker = SQLChecker(
            comparer=is_equal,
            expected_value="WebLudus",
            dict_path="0.username",
        )
        waiter = SQLWaiter(cursor=sqlite_db, query=select_all_from_user_query)
        waiter.add_custom_checker(checker)
        result = waiter.run(retries=1).get_result()
        assert result == [
            {"id": 1, "username": "WebLudus"},
            {"id": 2, "username": "Dawid"},
        ]

    def test_condition_not_met_raise_error(
        self, sqlite_db: sqlite3.Cursor, select_all_from_user_query: str
    ):
        waiter = SQLWaiter(cursor=sqlite_db, query=select_all_from_user_query)
        waiter.add_checker(
            expected_value="TEST",
            comparer="is_equal",
        )

        mgs = (
            "The condition has not been met! | Failed checkers: (Checker: SQLChecker"
            " | Comparer: is_equal | Dictor_fallback: None | Expected_value: TEST"
            " | Path: None | Search_query: None | Data:"
            " [{'id': 1, 'username': 'WebLudus'}, {'id': 2, 'username': 'Dawid'}])"
            " | SELECT * from user"
        )
        with pytest.raises(WaiterConditionWasNotMet, match=mgs):
            waiter.run(retries=1)

    def test_condition_not_met_without_error(
        self, sqlite_db: sqlite3.Cursor, select_all_from_user_query: str
    ):
        waiter = SQLWaiter(cursor=sqlite_db, query=select_all_from_user_query)
        waiter.add_checker(
            expected_value="TEST",
            comparer="is_equal",
        )
        result = [{"id": 1, "username": "WebLudus"}, {"id": 2, "username": "Dawid"}]

        waiter.run(retries=1, raise_error=False)

        assert waiter.get_result() == result

    def test_wait_for_value(
        self,
        sqlite_db: sqlite3.Cursor,
        tmp_path: Path,
        caplog: LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ):
        def insert_data():
            sleep(1)
            conn = sqlite3.connect(
                database=os.path.join(tmp_path, "bepatient.sqlite"),
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            conn.execute("INSERT INTO user (username) VALUES ('Jerry')")
            conn.commit()
            conn.close()

        monkeypatch.setattr("uuid.uuid4", lambda: "SQLWaiter")
        logs = [
            (
                "bepatient.waiter_src.waiter",
                10,
                "Checking whether the condition has been met. The 1 approach",
            ),
            (
                "bepatient.waiter_src.checker",
                20,
                "Check uuid: SQLWaiter | Checker: SQLChecker | Comparer: is_equal | "
                "Dictor_fallback: None | Expected_value: Jerry | Path: 0.username | "
                "Search_query: None | Data: Jerry",
            ),
            ("bepatient_db.sql_checkers", 20, "Check uuid: SQLWaiter | Data: []"),
            (
                "bepatient.waiter_src.checker",
                10,
                "Check uuid: SQLWaiter | Condition not met | Expected: Jerry"
                " | Data: None",
            ),
            (
                "bepatient.waiter_src.waiter",
                10,
                "The condition has not been met. Waiting: 2",
            ),
            (
                "bepatient.waiter_src.waiter",
                10,
                "Checking whether the condition has been met. The 2 approach",
            ),
            (
                "bepatient.waiter_src.checker",
                20,
                "Check uuid: SQLWaiter | Checker: SQLChecker | Comparer: is_equal | "
                "Dictor_fallback: None | Expected_value: Jerry | Path: 0.username | "
                "Search_query: None | Data: Jerry",
            ),
            (
                "bepatient_db.sql_checkers",
                20,
                "Check uuid: SQLWaiter | Data: [{'username': 'Jerry'}]",
            ),
            ("bepatient.waiter_src.waiter", 10, "Condition met!"),
        ]

        waiter = SQLWaiter(
            cursor=sqlite_db, query="SELECT username FROM user WHERE id = 3"
        )
        waiter.add_checker(
            expected_value="Jerry", comparer="is_equal", dict_path="0.username"
        )

        threading.Thread(target=insert_data).start()
        waiter.run(retries=5, delay=2)

        assert waiter.get_result() == [{"username": "Jerry"}]
        assert caplog.record_tuples == logs
