import sqlite3
from typing import Any, Callable

import pytest
from _pytest.logging import LogCaptureFixture

from bepatient_db.sql_checkers import SQLChecker


class TestSQLChecker:
    def test_str(self, is_equal: Callable[[Any, Any], bool]):
        checker = SQLChecker(is_equal, 5)
        msg = (
            "Checker: SQLChecker | Comparer: comparer | Dictor_fallback: None | "
            "Expected_value: 5 | Path: None | Search_query: None | Data: None"
        )

        assert str(checker) == msg

    def test_prepare_data(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        caplog: LogCaptureFixture,
    ):
        logs = [
            (
                "bepatient_db.sql_checkers",
                20,
                "Check uuid: None | Data: [{'id': 1, 'username': 'WebLudus'}]",
            )
        ]
        expected = [{"id": 1, "username": "WebLudus"}]
        checker = SQLChecker(is_equal, expected)
        checker_data = checker.prepare_data(
            sqlite_db.execute("SELECT * FROM user WHERE id = 1").fetchall()
        )
        assert checker_data == expected
        assert caplog.record_tuples == logs

    def test_prepare_data_dict_path(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        select_all_from_user_query: str,
    ):
        expected = "WebLudus"
        checker = SQLChecker(
            comparer=is_equal, expected_value=expected, dict_path="0.username"
        )
        checker_data = checker.prepare_data(
            sqlite_db.execute(select_all_from_user_query).fetchall()
        )

        assert checker_data == expected

    def test_prepare_data_search_query(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        select_all_from_user_query: str,
    ):
        expected = ["WebLudus", "Dawid"]
        checker = SQLChecker(
            comparer=is_equal, expected_value=expected, search_query="username"
        )
        checker_data = checker.prepare_data(
            sqlite_db.execute(select_all_from_user_query).fetchall()
        )

        assert checker_data == expected

    def test_check(
        self, sqlite_db: sqlite3.Cursor, is_equal: Callable[[Any, Any], bool]
    ):
        checker = SQLChecker(is_equal, [{"id": 1, "username": "WebLudus"}])
        checker_data = sqlite_db.execute("SELECT * FROM user WHERE id = 1").fetchall()

        assert checker.check(checker_data) is True

    def test_condition_not_met(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        select_all_from_user_query: str,
    ):
        checker = SQLChecker(is_equal, "TEST")
        checker_data = sqlite_db.execute(select_all_from_user_query).fetchall()

        assert checker.check(checker_data) is False

    def test_missing_key(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        select_all_from_user_query: str,
    ):
        checker = SQLChecker(
            comparer=is_equal,
            expected_value="missing_key",
            dict_path="0.TEST",
            dictor_fallback="missing_key",
        )
        checker_data = sqlite_db.execute(select_all_from_user_query).fetchall()

        assert checker.check(checker_data) is True

    def test_missing_key_in_search_query(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        select_all_from_user_query: str,
    ):
        checker = SQLChecker(
            comparer=is_equal,
            expected_value="missing_key",
            search_query="TEST",
            dictor_fallback="missing_key",
        )
        checker_data = sqlite_db.execute(select_all_from_user_query).fetchall()

        assert checker.check(checker_data) is True

    def test_null_value(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        caplog: LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setattr("uuid.uuid4", lambda: "TestSQLChecker")
        logs = [
            (
                "bepatient.waiter_src.checker",
                20,
                "Check uuid: TestSQLChecker | Checker: SQLChecker | Comparer: comparer"
                " | Dictor_fallback: missing | Expected_value: None"
                " | Path: 0.description | Search_query: None | Data: None",
            ),
            (
                "bepatient_db.sql_checkers",
                20,
                "Check uuid: TestSQLChecker | Data: [{'description': None}]",
            ),
        ]
        checker = SQLChecker(
            comparer=is_equal,
            expected_value=None,
            dict_path="0.description",
            dictor_fallback="missing",
        )
        checker_data = sqlite_db.execute(
            "SELECT description from tests WHERE id = 1"
        ).fetchall()

        assert checker.check(checker_data) is True
        assert caplog.record_tuples == logs

    def test_empty_string_value(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        caplog: LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setattr("uuid.uuid4", lambda: "TestSQLChecker")
        logs = [
            (
                "bepatient.waiter_src.checker",
                20,
                "Check uuid: TestSQLChecker | Checker: SQLChecker | Comparer: comparer"
                " | Dictor_fallback: missing | Expected_value: "
                " | Path: 0.description | Search_query: None | Data: ",
            ),
            (
                "bepatient_db.sql_checkers",
                20,
                "Check uuid: TestSQLChecker | Data: [{'description': ''}]",
            ),
        ]
        checker = SQLChecker(
            comparer=is_equal,
            expected_value="",
            dict_path="0.description",
            dictor_fallback="missing",
        )
        checker_data = sqlite_db.execute(
            "SELECT description from tests WHERE id = 2"
        ).fetchall()

        assert checker.check(checker_data) is True
        assert caplog.record_tuples == logs

    @pytest.mark.xfail(reason="The dictor library bug")
    def test_search_for_null_value(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setattr("uuid.uuid4", lambda: "TestSQLChecker")
        checker = SQLChecker(
            comparer=is_equal,
            expected_value=[None],
            search_query="description",
            dictor_fallback="missing",
        )
        checker_data = sqlite_db.execute(
            "SELECT description from tests WHERE id = 1"
        ).fetchall()

        assert checker.check(checker_data) is True

    def test_search_for_empty_string_value(
        self,
        sqlite_db: sqlite3.Cursor,
        is_equal: Callable[[Any, Any], bool],
        caplog: LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setattr("uuid.uuid4", lambda: "TestSQLChecker")
        logs = [
            (
                "bepatient.waiter_src.checker",
                20,
                "Check uuid: TestSQLChecker | Checker: SQLChecker | Comparer: comparer"
                " | Dictor_fallback: missing | Expected_value: [''] | Path: None"
                " | Search_query: description | Data: ['']",
            ),
            (
                "bepatient_db.sql_checkers",
                20,
                "Check uuid: TestSQLChecker | Data: [{'description': ''}]",
            ),
        ]
        checker = SQLChecker(
            comparer=is_equal,
            expected_value=[""],
            search_query="description",
            dictor_fallback="missing",
        )
        checker_data = sqlite_db.execute(
            "SELECT description from tests WHERE id = 2"
        ).fetchall()

        assert checker.check(checker_data) is True
        assert caplog.record_tuples == logs
