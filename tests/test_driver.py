import unittest
from decimal import Decimal

from driver import Driver


class TestDriver(unittest.TestCase):
    def test_initial_values(self):
        d = Driver("ali1", (1, 2), "BIKE")
        self.assertEqual(d.username, "ali1")
        self.assertEqual(d.position, (1, 2))
        self.assertEqual(d.service_category, "BIKE")
        self.assertEqual(d.credit, Decimal("0"))
        self.assertEqual(d.status, "FREE")
        self.assertIsNone(d.current_order)
        self.assertTrue(d.is_available())

    def test_properties_are_read_only(self):
        d = Driver("ali1", (0, 0), "VAN")
        for attr, val in (("credit", Decimal("5")), ("status", "BUSY"),
                          ("position", (1, 1)), ("username", "x"),
                          ("current_order", None)):
            with self.assertRaises(AttributeError):
                setattr(d, attr, val)

    def test_invalid_username(self):
        for bad in ("", "a b", "a" * 26, "علی", "ali_1"):
            with self.assertRaises(ValueError):
                Driver(bad, (0, 0), "BIKE")
        with self.assertRaises(TypeError):
            Driver(123, (0, 0), "BIKE")

    def test_invalid_position(self):
        with self.assertRaises(TypeError):
            Driver("a", [0, 0], "BIKE")
        with self.assertRaises(ValueError):
            Driver("a", (0, 0, 0), "BIKE")
        with self.assertRaises(TypeError):
            Driver("a", (True, 0), "BIKE")
        with self.assertRaises(TypeError):
            Driver("a", (1.5, 0), "BIKE")

    def test_invalid_category(self):
        with self.assertRaises(ValueError):
            Driver("a", (0, 0), "bike")
        with self.assertRaises(TypeError):
            Driver("a", (0, 0), None)


if __name__ == "__main__":
    unittest.main()
