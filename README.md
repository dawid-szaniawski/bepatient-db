[![Tests](https://github.com/dawid-szaniawski/bepatient-db/actions/workflows/tox.yml/badge.svg)](https://github.com/dawid-szaniawski/bepatient-db/actions/workflows/tox.yml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bepatient-db)](https://pypi.org/project/bepatient-db/)
[![PyPI](https://img.shields.io/pypi/v/bepatient-db)](https://pypi.org/project/bepatient-db/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/dawid-szaniawski/bepatient-db/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/github/dawid-szaniawski/bepatient-db/branch/master/graph/badge.svg?token=hY7Nb5jGgi)](https://codecov.io/github/dawid-szaniawski/bepatient-db)
[![CodeFactor](https://www.codefactor.io/repository/github/dawid-szaniawski/bepatient-db/badge)](https://www.codefactor.io/repository/github/dawid-szaniawski/bepatient-db)

# bepatient-db

Plugin for the `bepatient` library adding database support.
It enables the repeated execution of database queries while waiting for a specific
condition to be met.

## Supported databases:

- PostgreSQL,
- MySQL,
- SQLite.

## Installation

To install _bepatient-db_, you can use pip:

```bash
pip install bepatient-db
```

_bepatient_ supports Python 3.10+

## Usage

First and foremost, we need to configure the database connection. `SQLWaiter` utilizes
the `Cursor` object of supported databases. Data returned by the `Cursor` should be in
the format of a list of dictionaries (`list[dict]`) or a dictionary (`dict`).
Each of the supported databases allows for such configuration.

### SQLite example

```python
import sqlite3

from flask import current_app, g


def dict_factory(cur, row):
    fields = [column[0] for column in cur.description]
    return dict(zip(fields, row))


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
```

With the `Cursor` configured in this way, we can use `SQLWaiter` to repeatedly execute
queries until we receive the desired data or reach a predefined number of attempts.



Database: `user`

| id | name  |
|----|-------|
| 1  | Bob   |
| 2  | Jerry |
| 3  | Matt  |


```python
from sqlite3 import Cursor

from bepatient_db import SQLWaiter


def wait_for_user(cursor: Cursor) -> list[dict[str, str]]:
    waiter = SQLWaiter(cursor=cursor, query="SELECT name FROM user")
    waiter.add_checker(
        expected_value="Bob", comparer="is_equal", dict_path="0.name"
    )
    return waiter.run(retries=1).get_result()
```

Output:

```python
[
    {"name": "Bob"},
    {"name": "Jerry"},
    {"name": "Matt"},
]
```

## License

MIT License

Copyright (c) 2023 Dawid Szaniawski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
