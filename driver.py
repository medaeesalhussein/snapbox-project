from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from validators import validate_category, validate_position, validate_username

if TYPE_CHECKING:  # pragma: no cover
    from order import Order

FREE = "FREE"
BUSY = "BUSY"
DRIVER_STATUSES = (FREE, BUSY)


class Driver:
    """A delivery driver. Public attributes are read-only properties;
    state changes happen through underscore methods used by DeliverySystem."""

    def __init__(self, username: str, position: tuple, service_category: str):
        self._username = validate_username(username)
        self._position = validate_position(position)
        self._service_category = validate_category(service_category)
        self._credit = Decimal("0")
        self._status = FREE
        self._current_order = None
        self._score_sum = 0
        self._score_count = 0

    @property
    def username(self) -> str:
        return self._username

    @property
    def position(self) -> tuple:
        return self._position

    @property
    def service_category(self) -> str:
        return self._service_category

    @property
    def credit(self) -> Decimal:
        return self._credit

    @property
    def status(self) -> str:
        return self._status

    @property
    def current_order(self) -> "Order | None":
        return self._current_order
    
    @property
    def score(self) -> float | None:
        if self._score_count == 0:
            return None
        return self._score_sum / self._score_count

    def is_available(self) -> bool:
        return self._status == FREE

    # ---- internal mutators (called by DeliverySystem only) ----
    def _take_order(self, order: "Order") -> None:
        self._current_order = order
        self._status = BUSY

    def _move_to(self, position: tuple) -> None:
        self._position = position

    def _add_credit(self, amount: Decimal) -> None:
        self._credit += amount

    def _release(self) -> None:
        self._current_order = None
        self._status = FREE

    def _add_score(self, value: int) -> None:
        self._score_sum += value
        self._score_count += 1
