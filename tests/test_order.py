import unittest
from decimal import Decimal

from order import Order


class TestOrder(unittest.TestCase):
    def make(self, **kw):
        args = dict(order_id=1, service_category="VAN", starting_position=(0, 0),
                    finishing_position=(2, 3), cost=Decimal("500"))
        args.update(kw)
        return Order(**args)

    def test_initial_values(self):
        o = self.make()
        self.assertEqual(o.status, "PENDING")
        self.assertIsNone(o.assigned_driver)
        self.assertTrue(o.is_pending())
        self.assertEqual(o.cost, Decimal("500"))

    def test_properties_are_read_only(self):
        o = self.make()
        for attr in ("order_id", "status", "cost", "assigned_driver"):
            with self.assertRaises(AttributeError):
                setattr(o, attr, 1)

    def test_invalid_id_and_cost(self):
        with self.assertRaises(ValueError):
            self.make(order_id=0)
        with self.assertRaises(TypeError):
            self.make(order_id=True)
        with self.assertRaises(TypeError):
            self.make(cost=500)
        with self.assertRaises(ValueError):
            self.make(cost=Decimal("-1"))

    def test_invalid_positions(self):
        with self.assertRaises(TypeError):
            self.make(starting_position="00")
        with self.assertRaises(ValueError):
            self.make(finishing_position=(1,))


if __name__ == "__main__":
    unittest.main()
