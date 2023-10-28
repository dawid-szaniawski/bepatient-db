import logging
from typing import Any, Callable, TypeAlias

from bepatient.waiter_src.checker import Checker
from dictor import dictor

log = logging.getLogger(__name__)

DbValueType: TypeAlias = str | int | float | None | bool
DbData: TypeAlias = dict[str, DbValueType] | DbValueType
ResultType: TypeAlias = DbData | list[DbData]


class SQLChecker(Checker):
    def __init__(
        self,
        comparer: Callable[[Any, Any], bool],
        expected_value: Any,
        dict_path: str | None = None,
        search_query: str | None = None,
        dictor_fallback: str | None = None,
    ):
        self.path = dict_path
        self.search_query = search_query
        self.dictor_fallback = dictor_fallback
        super().__init__(comparer, expected_value)

    def prepare_data(
        self, data: list[dict[str, Any]], run_uuid: str | None = None
    ) -> ResultType:
        """Prepare the response data for comparison.

        Args:
            data (Response): The response containing the data.
            run_uuid (str | None): The unique run identifier. Defaults to None.

        Returns:
            Any: The prepared data for comparison."""
        log.info("Check uuid: %s | Data: %s", run_uuid, data)
        return dictor(
            data=data,
            path=self.path,
            search=self.search_query,
            default=self.dictor_fallback,
        )
