from __future__ import annotations

import re
import sys
from decimal import Decimal

# ============================================================
# validators
# ============================================================
CATEGORIES = ("BIKE", "VAN", "TRUCK")
_USERNAME_RE = re.compile(r"[A-Za-z0-9]{1,25}")


def validate_username(value):
    if not isinstance(value, str):
        raise TypeError("username must be a str")
    if not _USERNAME_RE.fullmatch(value):
        raise ValueError("username must be 1-25 English letters/digits")
    return value


def validate_choice(value, allowed, name="value"):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {tuple(allowed)}")
    return value


def validate_category(value):
    return validate_choice(value, CATEGORIES, "service_category")


def validate_position(value):
    if not isinstance(value, tuple):
        raise TypeError("position must be a tuple")
    if len(value) != 2:
        raise ValueError("position must have exactly two coordinates")
    for coord in value:
        if isinstance(coord, bool) or not isinstance(coord, int):
            raise TypeError("coordinates must be int (bool not allowed)")
    return value


def validate_int(value, name="value", minimum=0):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int (bool not allowed)")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def validate_positive_decimal(value, name="value"):
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal")
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{name} must be a finite positive Decimal")
    return value


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ============================================================
# order
# ============================================================
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

    def _mark_arrived(self, driver: "Driver") -> None:
        self._assigned_driver = driver
        self._status = ARRIVED

    def _mark_pickup(self) -> None:
        self._status = PICKUP

    def _mark_delivered(self) -> None:
        self._status = DELIVERED


# ============================================================
# driver
# ============================================================
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


# ============================================================
# delivery_system
# ============================================================
DRIVER_SHARE = Decimal("0.8")
COMPANY_SHARE = Decimal("0.2")
ENDPOINTS = ("START", "FINISH")
SCORE_MIN = 1
SCORE_MAX = 5


class DeliverySystem:
    """Owns all drivers/orders of one independent system instance."""

    def __init__(self):
        self._drivers: dict[str, Driver] = {}
        self._orders: dict[int, Order] = {}
        self._company_credit = Decimal("0")
        self._next_order_id = 1

    @property
    def company_credit(self) -> Decimal:
        return self._company_credit

    @property
    def total_drivers(self) -> int:
        return len(self._drivers)

    def add_driver(self, username: str, position: tuple, service_category: str) -> bool:
        driver = Driver(username, position, service_category)
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
        k = pending_same + 1
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
        free.sort(key=lambda d: manhattan(d.position, position))
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

    def _get_driver_or_raise(self, username: str) -> Driver:
        try:
            return self._drivers[username]
        except KeyError:
            raise KeyError(f"unknown driver: {username}") from None

    def _nearest_pending(self, position: tuple, category: str | None) -> Order | None:
        best, best_dist = None, None
        for o in self._orders.values():
            if not o.is_pending():
                continue
            if category is not None and o.service_category != category:
                continue
            dist = manhattan(o.starting_position, position)
            if best is None or dist < best_dist:
                best, best_dist = o, dist
        return best

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


# ============================================================
# main / CLI
# ============================================================
ERROR = "ERROR: unknown command"


def _pos(a, b):
    combined = f"{a} {b}"
    cleaned = combined.replace("(", "").replace(")", "").replace(",", "")
    parts = cleaned.split()
    return (int(parts[0]), int(parts[1]))


def process_command(system: DeliverySystem, line: str):
    parts = line.split()
    if not parts:
        return None
    cmd, args = parts[0].upper(), parts[1:]
    try:
        if cmd == "ADD-DRIVER":
            u, x, y, cat = args
            success = system.add_driver(u, _pos(x, y), cat)
            return "user added successfully" if success else "user previously added"

        if cmd == "CREATE-ORDER":
            cat, sx, sy, fx, fy = args
            order_id = system.create_order(cat, _pos(sx, sy), _pos(fx, fy))
            return "invalid order" if order_id is None else str(order_id)

        if cmd == "ASSIGN-NEXT-ORDER":
            (u,) = args
            try:
                order_id = system.assign_next_order(u)
                if order_id is None:
                    return "there is no order right now"
                return f"{order_id} assigned to {u}"
            except KeyError:
                return "invalid driver name"
            except RuntimeError:
                return "driver is already busy"

        if cmd == "GET-DRIVER":
            (u,) = args
            r = system.get_driver(u)
            if r is None:
                return "invalid driver name"
            status, pos, credit = r
            return f"{status} ({pos[0]}, {pos[1]}) {int(credit)}"

        if cmd == "ORDER-UPDATE":
            status, u, oid_str = args
            try:
                driver = system._get_driver_or_raise(u)
            except KeyError:
                return "invalid driver name"
            try:
                oid = int(oid_str)
                order = system._orders.get(oid)
                if order is None or order.assigned_driver is not driver:
                    return "wrong order-id"
                success = system.update_order_status(u, oid, status)
                if success:
                    return "status changed successfully"
                else:
                    return "invalid status"
            except (TypeError, ValueError):
                return ERROR

        if cmd == "GET-ORDER":
            (oid,) = args
            r = system.get_order(int(oid))
            if r is None:
                return "invalid order"
            status, driver_name, cost = r
            d_str = "None" if driver_name is None else driver_name
            return f"{status} {d_str} {cost}"

        if cmd == "GET-ORDER-LIST":
            (s,) = args
            order_ids = system.get_order_list(s)
            return "None" if not order_ids else " ".join(str(x) for x in order_ids)

        if cmd == "GET-DRIVER-LIST":
            (s,) = args
            driver_names = system.get_driver_list(s)
            return "None" if not driver_names else " ".join(str(x) for x in driver_names)

        if cmd == "GET-NEAR-DRIVER":
            x, y, n_str = args
            n = int(n_str)
            driver_names = system.get_near_drivers(_pos(x, y), int(n))
            return "None" if not driver_names else " ".join(str(x) for x in driver_names)

        if cmd == "GET-CNT-ORDER":
            x, y, d, e = args
            return str(system.count_orders(_pos(x, y), int(d), e))

        if cmd == "GET-NEAREST-PENDING-ORDER":
            x, y = args
            order_id = system.get_nearest_pending_order(_pos(x, y))
            return "None" if order_id is None else str(order_id)

        if cmd == "GET-COMPANY":
            return str(int(system.get_company_credit()))

        if cmd == "GET-DRIVER-SCORE":
            (u,) = args
            try:
                score = system.get_driver_score(u)
            except KeyError:
                return "invalid driver name"
            return "no score" if score is None else f"{score:.1f}"

        if cmd == "GIVE-DRIVER-SCORE":
            u, s_str = args
            try:
                score = int(s_str)
            except ValueError:
                return "invalid score"
            try:
                system.give_driver_score(u, score)
            except KeyError:
                return "invalid driver name"
            except ValueError:
                return "score out of range"
            return "score added successfully"

        if cmd == "END":
            return None

    except (TypeError, ValueError, KeyError, RuntimeError) as e:
        return f"ERROR: {e}"

    return ERROR


def main(stdin=None, stdout=None):
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    system = DeliverySystem()
    for line in stdin:
        if line.split()[:1] == ["END"]:
            break
        out = process_command(system, line)
        if out is not None:
            print(out, file=stdout)


if __name__ == "__main__":
    main()