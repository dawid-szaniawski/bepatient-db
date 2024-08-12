import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pytest
from bepatient import Checker

SCRIPTS_PATH = Path(__file__).parent / "scripts"


@pytest.fixture
def is_equal() -> Callable[[Any, Any], bool]:
    def comparer(data: Any, expected_value: Any) -> bool:
        return data == expected_value

    return comparer


@pytest.fixture
def checker_true(
    is_equal: Callable[[Any, Any], bool]  # pylint: disable=W0621
) -> Checker:
    class CheckerMocker(Checker):
        def __str__(self) -> str:
            return "I'm truthy"

        def prepare_data(self, data: Any, run_uuid: str | None = None) -> None:
            """mock"""

        def check(self, data: Any, run_uuid: str) -> bool:
            return True

    checker = CheckerMocker(is_equal, "")
    assert str(checker) == "I'm truthy"
    return checker


@pytest.fixture
def checker_false(
    is_equal: Callable[[Any, Any], bool]  # pylint: disable=W0621
) -> Checker:
    class CheckerMocker(Checker):
        def __str__(self) -> str:
            return "I'm falsy"

        def prepare_data(self, data: Any, run_uuid: str | None = None) -> None:
            """mock"""

        def check(self, data: Any, run_uuid: str) -> bool:
            return False

    return CheckerMocker(is_equal, "")


@pytest.fixture
def sqlite_db(tmp_path: Path) -> sqlite3.Cursor:  # type: ignore
    def dict_factory(
        cur: sqlite3.Cursor, row: tuple[str | int | datetime]
    ) -> dict[str, str | int | datetime]:
        fields = [column[0] for column in cur.description]
        return dict(zip(fields, row))

    conn = sqlite3.connect(
        database=os.path.join(tmp_path, "bepatient.sqlite"),
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    conn.row_factory = dict_factory
    with open(SCRIPTS_PATH / "init_db.sql", mode="r", encoding="utf-8") as file:
        conn.executescript(file.read())
    cursor = conn.cursor()
    yield cursor
    cursor.close()
    conn.close()


@pytest.fixture
def select_all_from_user_query() -> str:
    return "SELECT * from user"
