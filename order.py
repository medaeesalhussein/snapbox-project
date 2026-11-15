from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from validators import (validate_category, validate_int, validate_position,
                        validate_positive_decimal)

if TYPE_CHECKING:  # pragma: no cover
    from driver import Driver

PENDING = "PENDING"
ARRIVED = "ARRIVED"
PICKUP = "PICKUP"
DELIVERED = "DELIVERED"
ORDER_STATUSES = (PENDING, ARRIVED, PICKUP, DELIVERED)


class Order:
    """A delivery order. Public attributes are read-only properties;
    state changes happen through underscore methods used by DeliverySystem."""

    def __init__(self, order_id: int, service_category: str,
                 starting_position: tuple, finishing_position: tuple,
                 cost: Decimal):
        self._order_id = validate_int(order_id, "order_id", minimum=1)
        self._service_category = validate_category(service_category)
        self._starting_position = validate_position(starting_position)
        self._finishing_position = validate_position(finishing_position)
        self._cost = validate_positive_decimal(cost, "cost")
        self._status = PENDING
        self._assigned_driver = None

    # ---- read-only properties ----
    @property
    def order_id(self) -> int:
        return self._order_id

    @property
    def service_category(self) -> str:
        return self._service_category

    @property
    def starting_position(self) -> tuple:
        return self._starting_position

    @property
    def finishing_position(self) -> tuple:
        return self._finishing_position

    @property
    def cost(self) -> Decimal:
        return self._cost

    @property
    def status(self) -> str:
        return self._status

    @property
    def assigned_driver(self) -> "Driver | None":
        return self._assigned_driver

    def is_pending(self) -> bool:
        return self._status == PENDING

    # ---- internal transitions (called by DeliverySystem only) ----
    def _mark_arrived(self, driver: "Driver") -> None:
        self._assigned_driver = driver
        self._status = ARRIVED

    def _mark_pickup(self) -> None:
        self._status = PICKUP

    def _mark_delivered(self) -> None:
        self._status = DELIVERED
