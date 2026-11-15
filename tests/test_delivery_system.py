import unittest
from decimal import Decimal

from delivery_system import DeliverySystem


class TestDeliverySystem(unittest.TestCase):
    def setUp(self):
        self.s = DeliverySystem()

    def test_initial_state(self):
        self.assertEqual(self.s.total_drivers, 0)
        self.assertEqual(self.s.company_credit, Decimal("0"))
        self.assertEqual(self.s.get_order_list("PENDING"), [])

    def test_systems_are_independent(self):
        other = DeliverySystem()
        self.s.add_driver("a", (0, 0), "BIKE")
        self.assertEqual(other.total_drivers, 0)

    def test_add_driver_and_duplicate(self):
        self.assertTrue(self.s.add_driver("a", (0, 0), "BIKE"))
        self.assertFalse(self.s.add_driver("a", (5, 5), "VAN"))
        self.assertEqual(self.s.total_drivers, 1)
        self.assertEqual(self.s.get_driver("a")[1], (0, 0))
        self.assertTrue(self.s.add_driver("A", (0, 0), "BIKE"))  # case-sensitive

    def test_add_driver_validation(self):
        with self.assertRaises(ValueError):
            self.s.add_driver("bad name", (0, 0), "BIKE")
        with self.assertRaises(TypeError):
            self.s.add_driver("a", (0, 0), 5)
        self.assertEqual(self.s.total_drivers, 0)

    def test_create_order_ids_and_same_points(self):
        self.assertEqual(self.s.create_order("BIKE", (0, 0), (1, 0)), 1)
        self.assertIsNone(self.s.create_order("BIKE", (2, 2), (2, 2)))
        self.assertEqual(self.s.create_order("BIKE", (0, 0), (0, 1)), 2)  # id not consumed

    def test_cost_includes_new_order_and_is_fixed(self):
        o1 = self.s.create_order("BIKE", (0, 0), (3, 4))   # k=1,d=7
        o2 = self.s.create_order("BIKE", (0, 0), (1, 0))   # k=2,d=1
        o3 = self.s.create_order("VAN", (0, 0), (1, 0))    # k=1,d=1
        self.assertEqual(self.s.get_order(o1)[2], Decimal("800"))
        self.assertEqual(self.s.get_order(o2)[2], Decimal("300"))
        self.assertEqual(self.s.get_order(o3)[2], Decimal("200"))

    def test_assign_nearest_compatible_order(self):
        self.s.add_driver("a", (0, 0), "BIKE")
        self.s.create_order("VAN", (1, 0), (5, 5))     # 1: wrong category
        self.s.create_order("BIKE", (5, 5), (6, 6))    # 2: far
        self.s.create_order("BIKE", (1, 1), (2, 2))    # 3: near
        self.assertEqual(self.s.assign_next_order("a"), 3)
        st, name, _ = self.s.get_order(3)
        self.assertEqual((st, name), ("ARRIVED", "a"))
        self.assertEqual(self.s.get_driver("a")[0], "BUSY")
        self.assertEqual(self.s.get_driver("a")[1], (0, 0))  # position unchanged

    def test_assign_tie_prefers_older_order(self):
        self.s.add_driver("a", (0, 0), "BIKE")
        self.s.create_order("BIKE", (2, 0), (9, 9))
        self.s.create_order("BIKE", (0, 2), (9, 9))
        self.assertEqual(self.s.assign_next_order("a"), 1)

    def test_assign_none_busy_and_unknown(self):
        self.s.add_driver("a", (0, 0), "BIKE")
        self.assertIsNone(self.s.assign_next_order("a"))
        self.s.create_order("BIKE", (1, 1), (2, 2))
        self.s.create_order("BIKE", (3, 3), (4, 4))
        self.s.assign_next_order("a")
        with self.assertRaises(RuntimeError):
            self.s.assign_next_order("a")
        with self.assertRaises(KeyError):
            self.s.assign_next_order("ghost")

    def _delivered_flow(self):
        self.s.add_driver("a", (0, 0), "BIKE")
        oid = self.s.create_order("BIKE", (1, 1), (3, 3))  # cost 100*(1+4)=500
        self.s.assign_next_order("a")
        return oid

    def test_full_lifecycle_and_payment(self):
        oid = self._delivered_flow()
        self.assertTrue(self.s.update_order_status("a", oid, "PICKUP"))
        self.assertEqual(self.s.get_driver("a")[1], (1, 1))
        self.assertTrue(self.s.update_order_status("a", oid, "DELIVERED"))
        status, pos, credit = self.s.get_driver("a")
        self.assertEqual((status, pos, credit), ("FREE", (3, 3), Decimal("400")))
        self.assertEqual(self.s.get_company_credit(), Decimal("100"))
        self.assertEqual(self.s.get_order(oid), ("DELIVERED", "a", Decimal("500")))

    def test_invalid_transitions_change_nothing(self):
        oid = self._delivered_flow()
        self.assertFalse(self.s.update_order_status("a", oid, "DELIVERED"))  # skip step
        self.assertFalse(self.s.update_order_status("a", oid, "ARRIVED"))
        self.s.update_order_status("a", oid, "PICKUP")
        self.s.update_order_status("a", oid, "DELIVERED")
        self.assertFalse(self.s.update_order_status("a", oid, "DELIVERED"))  # repeat
        self.assertEqual(self.s.get_driver("a")[2], Decimal("400"))
        self.assertEqual(self.s.get_company_credit(), Decimal("100"))

    def test_other_drivers_order_and_errors(self):
        oid = self._delivered_flow()
        self.s.add_driver("b", (0, 0), "BIKE")
        self.assertFalse(self.s.update_order_status("b", oid, "PICKUP"))
        self.assertFalse(self.s.update_order_status("a", 99, "PICKUP"))
        with self.assertRaises(KeyError):
            self.s.update_order_status("ghost", oid, "PICKUP")
        with self.assertRaises(ValueError):
            self.s.update_order_status("a", oid, "FLYING")

    def test_lists_keep_registration_order(self):
        for n in ("c", "a", "b"):
            self.s.add_driver(n, (0, 0), "BIKE")
        self.assertEqual(self.s.get_driver_list("FREE"), ["c", "a", "b"])
        self.s.create_order("BIKE", (1, 1), (2, 2))
        self.s.assign_next_order("a")
        self.assertEqual(self.s.get_driver_list("BUSY"), ["a"])
        self.assertEqual(self.s.get_order_list("ARRIVED"), [1])
        with self.assertRaises(ValueError):
            self.s.get_driver_list("ARRIVED")

    def test_get_near_drivers(self):
        self.s.add_driver("far", (9, 9), "BIKE")
        self.s.add_driver("n1", (1, 0), "BIKE")
        self.s.add_driver("n2", (0, 1), "VAN")
        self.s.add_driver("busy", (0, 0), "BIKE")
        self.s.create_order("BIKE", (0, 0), (5, 5))
        self.s.assign_next_order("busy")
        self.assertEqual(self.s.get_near_drivers((0, 0), 2), ["n1", "n2"])
        self.assertEqual(self.s.get_near_drivers((0, 0), 10), ["n1", "n2", "far"])
        self.assertEqual(self.s.get_near_drivers((0, 0), 0), [])
        with self.assertRaises(ValueError):
            self.s.get_near_drivers((0, 0), -1)

    def test_count_orders_inclusive_any_status(self):
        self.s.create_order("BIKE", (0, 0), (0, 5))
        self.s.create_order("VAN", (3, 0), (0, 6))
        self.assertEqual(self.s.count_orders((0, 0), 3, "START"), 2)  # d == 3 included
        self.assertEqual(self.s.count_orders((0, 0), 2, "START"), 1)
        self.assertEqual(self.s.count_orders((0, 5), 0, "FINISH"), 1)
        with self.assertRaises(ValueError):
            self.s.count_orders((0, 0), 1, "MIDDLE")

    def test_nearest_pending_order(self):
        self.assertIsNone(self.s.get_nearest_pending_order((0, 0)))
        self.s.create_order("BIKE", (5, 5), (6, 6))
        self.s.create_order("VAN", (1, 1), (2, 2))
        self.s.create_order("BIKE", (1, 1), (3, 3))
        self.assertEqual(self.s.get_nearest_pending_order((0, 0)), 2)  # tie -> older

    def test_unknown_lookups_return_none(self):
        self.assertIsNone(self.s.get_driver("nobody"))
        self.assertIsNone(self.s.get_order(7))
        with self.assertRaises(TypeError):
            self.s.get_order(True)
        with self.assertRaises(ValueError):
            self.s.get_order(0)


if __name__ == "__main__":
    unittest.main()
