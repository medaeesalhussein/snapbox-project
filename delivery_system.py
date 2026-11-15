from __future__ import annotations

from decimal import Decimal

from driver import BUSY, DRIVER_STATUSES, FREE, Driver
from order import (ARRIVED, DELIVERED, ORDER_STATUSES, PENDING, PICKUP, Order)
from validators import (manhattan, validate_category, validate_choice,
                        validate_int, validate_position, validate_username)

DRIVER_SHARE = Decimal("0.8")
COMPANY_SHARE = Decimal("0.2")
ENDPOINTS = ("START", "FINISH")
SCORE_MIN = 1
SCORE_MAX = 5


class DeliverySystem:
    """Owns all drivers/orders of one independent system instance."""

    def __init__(self):
        self._drivers: dict[str, Driver] = {}   # insertion order = registration order
        self._orders: dict[int, Order] = {}     # insertion order = creation order
        self._company_credit = Decimal("0")
        self._next_order_id = 1

    # ---- properties ----
    @property
    def company_credit(self) -> Decimal:
        return self._company_credit

    @property
    def total_drivers(self) -> int:
        return len(self._drivers)

    # ---- commands ----
    def add_driver(self, username: str, position: tuple, service_category: str) -> bool:
        driver = Driver(username, position, service_category)  # validates input
        if username in self._drivers:
            return False
        self._drivers[username] = driver
        return True

    def create_order(self, service_category: str, starting_position: tuple,
                     finishing_position: tuple) -> int | None:
        validate_category(service_category)
        validate_position(starting_position)
        validate_position(finishing_position)
        if starting_position == finishing_position:
            return None
        pending_same = sum(1 for o in self._orders.values()
                           if o.is_pending() and o.service_category == service_category)
        k = pending_same + 1  # include the new order
        d = manhattan(starting_position, finishing_position)
        cost = Decimal(100) * Decimal(k + d)
        order = Order(self._next_order_id, service_category,
                      starting_position, finishing_position, cost)
        self._orders[order.order_id] = order
        self._next_order_id += 1
        return order.order_id

    def assign_next_order(self, username: str) -> int | None:
        validate_username(username)
        driver = self._get_driver_or_raise(username)
        if not driver.is_available():
            raise RuntimeError("driver is busy")
        best = self._nearest_pending(driver.position, driver.service_category)
        if best is None:
            return None
        best._mark_arrived(driver)
        driver._take_order(best)
        return best.order_id

    def update_order_status(self, username: str, order_id: int, new_status: str) -> bool:
        validate_username(username)
        validate_int(order_id, "order_id", minimum=1)
        validate_choice(new_status, ORDER_STATUSES, "status")
        driver = self._get_driver_or_raise(username)
        order = self._orders.get(order_id)
        if order is None or order.assigned_driver is not driver:
            return False
        if new_status == PICKUP and order.status == ARRIVED:
            driver._move_to(order.starting_position)
            order._mark_pickup()
            return True
        if new_status == DELIVERED and order.status == PICKUP:
            driver._move_to(order.finishing_position)
            driver._add_credit(order.cost * DRIVER_SHARE)
            self._company_credit += order.cost * COMPANY_SHARE
            driver._release()
            order._mark_delivered()
            return True
        return False

    # ---- queries ----
    def get_driver(self, username: str) -> tuple | None:
        validate_username(username)
        d = self._drivers.get(username)
        return None if d is None else (d.status, d.position, d.credit)

    def get_order(self, order_id: int) -> tuple | None:
        validate_int(order_id, "order_id", minimum=1)
        o = self._orders.get(order_id)
        if o is None:
            return None
        name = o.assigned_driver.username if o.assigned_driver else None
        return (o.status, name, o.cost)

    def get_order_list(self, status: str) -> list[int]:
        validate_choice(status, ORDER_STATUSES, "status")
        return [o.order_id for o in self._orders.values() if o.status == status]

    def get_driver_list(self, status: str) -> list[str]:
        validate_choice(status, DRIVER_STATUSES, "status")
        return [d.username for d in self._drivers.values() if d.status == status]

    def get_near_drivers(self, position: tuple, count: int) -> list[str]:
        validate_position(position)
        validate_int(count, "count", minimum=0)
        free = [d for d in self._drivers.values() if d.is_available()]
        free.sort(key=lambda d: manhattan(d.position, position))  # stable: ties keep registration order
        return [d.username for d in free[:count]]

    def count_orders(self, position: tuple, distance: int, endpoint: str) -> int:
        validate_position(position)
        validate_int(distance, "distance", minimum=0)
        validate_choice(endpoint, ENDPOINTS, "endpoint")
        total = 0
        for o in self._orders.values():
            point = o.starting_position if endpoint == "START" else o.finishing_position
            if manhattan(point, position) <= distance:
                total += 1
        return total

    def get_nearest_pending_order(self, position: tuple) -> int | None:
        validate_position(position)
        best = self._nearest_pending(position, None)
        return None if best is None else best.order_id

    def get_company_credit(self) -> Decimal:
        return self._company_credit

    # ---- helpers ----
    def _get_driver_or_raise(self, username: str) -> Driver:
        try:
            return self._drivers[username]
        except KeyError:
            raise KeyError(f"unknown driver: {username}") from None

    def _nearest_pending(self, position: tuple, category: str | None) -> Order | None:
        best, best_dist = None, None
        for o in self._orders.values():  # creation order -> strict '<' keeps the older one on ties
            if not o.is_pending():
                continue
            if category is not None and o.service_category != category:
                continue
            dist = manhattan(o.starting_position, position)
            if best is None or dist < best_dist:
                best, best_dist = o, dist
        return best
    
    # ---- bonus ----
    def give_driver_score(self, username: str, score: int) -> bool:
        validate_username(username)
        validate_int(score, "score", minimum=SCORE_MIN)
        if score > SCORE_MAX:
            raise ValueError("score out of range")
        driver = self._get_driver_or_raise(username)
        driver._add_score(score)
        return True

    def get_driver_score(self, username: str) -> float | None:
        validate_username(username)
        driver = self._get_driver_or_raise(username)
        return driver.score
