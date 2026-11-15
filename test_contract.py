"""Contract tests: check the exact Quera I/O format.

DO NOT MODIFY THIS FILE.
It is the source of truth for the interface contract between the
implementation and the Quera judge. It only exercises the public
text interface (`main`) — never internal classes directly.
"""
import io
import unittest

from main import main


class TestContract(unittest.TestCase):
    """Contract tests for the text interface.

    Each test feeds a small script through `main` and asserts the
    exact output lines (format, order, and values) that Quera expects.
    """

    def run_io(self, text: str) -> list[str]:
        """Run `text` through main(); return output lines (no trailing '')."""
        out = io.StringIO()
        main(io.StringIO(text), out)
        return out.getvalue().split("\n")[:-1]

    # ------------------------------------------------------------------
    # ADD-DRIVER / duplicate / validation
    # ------------------------------------------------------------------
    def test_add_driver_ok(self):
        self.assertEqual(
            self.run_io("ADD-DRIVER Ali (0, 0) BIKE\nEND\n"),
            ["user added successfully"],
        )

    def test_add_driver_duplicate(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "ADD-DRIVER Ali (5, 5) VAN\n"
                "END\n"),
            ["user added successfully", "user previously added"],
        )

    def test_add_driver_invalid_username(self):
        self.assertEqual(
            self.run_io("ADD-DRIVER bad-name (0, 0) BIKE\nEND\n"),
            ["ERROR: username must be 1-25 English letters/digits"],
        )

    # ------------------------------------------------------------------
    # GET-DRIVER
    # ------------------------------------------------------------------
    def test_get_driver_initial_format(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "GET-DRIVER Ali\n"
                "END\n"),
            ["user added successfully", "FREE (0, 0) 0"],
        )

    def test_get_driver_invalid(self):
        self.assertEqual(
            self.run_io("GET-DRIVER Nobody\nEND\n"),
            ["invalid driver name"],
        )

    # ------------------------------------------------------------------
    # CREATE-ORDER
    # ------------------------------------------------------------------
    def test_create_order_ids(self):
        self.assertEqual(
            self.run_io(
                "CREATE-ORDER BIKE (0, 0) (1, 0)\n"
                "CREATE-ORDER BIKE (0, 0) (0, 1)\n"
                "END\n"),
            ["1", "2"],
        )

    def test_create_order_same_points_is_invalid(self):
        self.assertEqual(
            self.run_io(
                "CREATE-ORDER BIKE (2, 2) (2, 2)\n"
                "CREATE-ORDER BIKE (0, 0) (0, 1)\n"   # id must not be consumed
                "END\n"),
            ["invalid order", "1"],
        )

    # ------------------------------------------------------------------
    # ASSIGN-NEXT-ORDER
    # ------------------------------------------------------------------
    def test_assign_next_order_ok(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (2, 2)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "END\n"),
            ["user added successfully", "1", "1 assigned to Ali"],
        )

    def test_assign_next_order_none(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "END\n"),
            ["user added successfully", "there is no order right now"],
        )

    def test_assign_next_order_busy(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (2, 2)\n"
                "CREATE-ORDER BIKE (3, 3) (4, 4)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "END\n"),
            ["user added successfully", "1", "2",
             "1 assigned to Ali", "driver is already busy"],
        )

    def test_assign_next_order_invalid_driver(self):
        self.assertEqual(
            self.run_io("ASSIGN-NEXT-ORDER Nobody\nEND\n"),
            ["invalid driver name"],
        )

    # ------------------------------------------------------------------
    # ORDER-UPDATE
    # ------------------------------------------------------------------
    def test_order_update_full_cycle(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (3, 3)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "ORDER-UPDATE PICKUP Ali 1\n"
                "ORDER-UPDATE DELIVERED Ali 1\n"
                "END\n"),
            ["user added successfully", "1", "1 assigned to Ali",
             "status changed successfully", "status changed successfully"],
        )

    def test_order_update_invalid_status(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (3, 3)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "ORDER-UPDATE FLYING Ali 1\n"
                "END\n"),
            ["user added successfully", "1", "1 assigned to Ali",
             "ERROR: unknown command"],
        )

    def test_order_update_wrong_order_id(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (3, 3)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "ORDER-UPDATE PICKUP Ali 99\n"
                "END\n"),
            ["user added successfully", "1", "1 assigned to Ali",
             "wrong order-id"],
        )

    def test_order_update_invalid_driver(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (3, 3)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "ORDER-UPDATE PICKUP Nobody 1\n"
                "END\n"),
            ["user added successfully", "1", "1 assigned to Ali",
             "invalid driver name"],
        )

    # ------------------------------------------------------------------
    # GET-ORDER / GET-ORDER-LIST
    # ------------------------------------------------------------------
    def test_get_order_format(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (3, 3)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "GET-ORDER 1\n"
                "END\n"),
            ["user added successfully", "1", "1 assigned to Ali",
             "ARRIVED Ali 500"],
        )

    def test_get_order_invalid(self):
        self.assertEqual(
            self.run_io("GET-ORDER 7\nEND\n"),
            ["invalid order"],
        )

    def test_get_order_list(self):
        self.assertEqual(
            self.run_io(
                "CREATE-ORDER BIKE (0, 0) (1, 0)\n"
                "CREATE-ORDER BIKE (2, 2) (3, 3)\n"
                "GET-ORDER-LIST PENDING\n"
                "END\n"),
            ["1", "2", "1 2"],
        )

    def test_get_order_list_empty(self):
        self.assertEqual(
            self.run_io("GET-ORDER-LIST PENDING\nEND\n"),
            ["None"],
        )

    # ------------------------------------------------------------------
    # GET-DRIVER-LIST
    # ------------------------------------------------------------------
    def test_get_driver_list_free_and_busy(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "ADD-DRIVER Sara (5, 5) VAN\n"
                "CREATE-ORDER BIKE (1, 1) (2, 2)\n"
                "ASSIGN-NEXT-ORDER Ali\n"
                "GET-DRIVER-LIST FREE\n"
                "GET-DRIVER-LIST BUSY\n"
                "END\n"),
            ["user added successfully", "user added successfully",
             "1", "1 assigned to Ali",
             "Sara", "Ali"],
        )

    def test_get_driver_list_empty(self):
        self.assertEqual(
            self.run_io("GET-DRIVER-LIST FREE\nEND\n"),
            ["None"],
        )

    # ------------------------------------------------------------------
    # GET-NEAR-DRIVER
    # ------------------------------------------------------------------
    def test_get_near_driver_ordering(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER far (9, 9) BIKE\n"
                "ADD-DRIVER n1 (1, 0) BIKE\n"
                "ADD-DRIVER n2 (0, 1) VAN\n"
                "GET-NEAR-DRIVER (0, 0) 2\n"
                "END\n"),
            ["user added successfully", "user added successfully",
             "user added successfully", "n1 n2"],
        )

    def test_get_near_driver_count_zero(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER n1 (1, 0) BIKE\n"
                "GET-NEAR-DRIVER (0, 0) 0\n"
                "END\n"),
            ["user added successfully", "None"],
        )

    # ------------------------------------------------------------------
    # GET-CNT-ORDER
    # ------------------------------------------------------------------
    def test_get_cnt_order_start_inclusive(self):
        self.assertEqual(
            self.run_io(
                "CREATE-ORDER BIKE (0, 0) (0, 5)\n"
                "CREATE-ORDER VAN (3, 0) (0, 6)\n"
                "GET-CNT-ORDER (0, 0) 3 START\n"    # d == 3 included
                "GET-CNT-ORDER (0, 0) 2 START\n"
                "END\n"),
            ["1", "2", "2", "1"],
        )

    def test_get_cnt_order_finish(self):
        self.assertEqual(
            self.run_io(
                "CREATE-ORDER BIKE (0, 0) (0, 5)\n"
                "GET-CNT-ORDER (0, 5) 0 FINISH\n"
                "END\n"),
            ["1", "1"],
        )

    # ------------------------------------------------------------------
    # GET-NEAREST-PENDING-ORDER
    # ------------------------------------------------------------------
    def test_get_nearest_pending_order_tie_older(self):
        self.assertEqual(
            self.run_io(
                "CREATE-ORDER BIKE (5, 5) (6, 6)\n"
                "CREATE-ORDER VAN (1, 1) (2, 2)\n"
                "CREATE-ORDER BIKE (1, 1) (3, 3)\n"
                "GET-NEAREST-PENDING-ORDER (0, 0)\n"
                "END\n"),
            ["1", "2", "3", "2"],   # tie -> older (id=2)
        )

    def test_get_nearest_pending_order_none(self):
        self.assertEqual(
            self.run_io("GET-NEAREST-PENDING-ORDER (0, 0)\nEND\n"),
            ["None"],
        )

    # ------------------------------------------------------------------
    # GET-COMPANY
    # ------------------------------------------------------------------
    def test_get_company_initial(self):
        self.assertEqual(
            self.run_io("GET-COMPANY\nEND\n"),
            ["0"],
        )

    def test_get_company_after_delivery(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "CREATE-ORDER BIKE (1, 1) (3, 3)\n"   # cost 100*(1+4)=500
                "ASSIGN-NEXT-ORDER Ali\n"
                "ORDER-UPDATE PICKUP Ali 1\n"
                "ORDER-UPDATE DELIVERED Ali 1\n"
                "GET-COMPANY\n"
                "END\n"),
            ["user added successfully", "1", "1 assigned to Ali",
             "status changed successfully", "status changed successfully",
             "100"],
        )

    # ------------------------------------------------------------------
    # END semantics
    # ------------------------------------------------------------------
    def test_end_stops_processing(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "END\n"
                "GET-DRIVER Ali\n"),   # must not execute after END
            ["user added successfully"],
        )

    # ------------------------------------------------------------------
    # Unknown command
    # ------------------------------------------------------------------
    def test_unknown_command(self):
        self.assertEqual(
            self.run_io("HELLO\nEND\n"),
            ["ERROR: unknown command"],
        )

    # ------------------------------------------------------------------
    # Scores (bonus feature)
    # ------------------------------------------------------------------
    def test_score_no_score_initially(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "GET-DRIVER-SCORE Ali\n"
                "END\n"),
            ["user added successfully", "no score"],
        )

    def test_score_average_one_decimal(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "GIVE-DRIVER-SCORE Ali 5\n"
                "GIVE-DRIVER-SCORE Ali 2\n"
                "GET-DRIVER-SCORE Ali\n"
                "END\n"),
            ["user added successfully", "score added successfully",
             "score added successfully", "3.5"],
        )

    def test_score_out_of_range(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "GIVE-DRIVER-SCORE Ali 0\n"
                "GIVE-DRIVER-SCORE Ali 6\n"
                "END\n"),
            ["user added successfully", "score out of range",
             "score out of range"],
        )

    def test_score_invalid_driver(self):
        self.assertEqual(
            self.run_io(
                "GIVE-DRIVER-SCORE Nobody 5\n"
                "GET-DRIVER-SCORE Nobody\n"
                "END\n"),
            ["invalid driver name", "invalid driver name"],
        )

    def test_score_non_numeric(self):
        self.assertEqual(
            self.run_io(
                "ADD-DRIVER Ali (0, 0) BIKE\n"
                "GIVE-DRIVER-SCORE Ali abc\n"
                "GET-DRIVER-SCORE Ali\n"
                "END\n"),
            ["user added successfully", "invalid score", "no score"],
        )

    # ------------------------------------------------------------------
    # Full scenario (end-to-end)
    # ------------------------------------------------------------------
    def test_full_scenario(self):
        """A small end-to-end scenario that exercises many commands."""
        lines = self.run_io(
            "ADD-DRIVER Ali (0, 0) BIKE\n"
            "ADD-DRIVER Sara (5, 5) VAN\n"
            "GIVE-DRIVER-SCORE Ali 5\n"
            "GIVE-DRIVER-SCORE Ali 3\n"
            "GET-DRIVER-SCORE Ali\n"
            "CREATE-ORDER BIKE (1, 1) (2, 2)\n"
            "ASSIGN-NEXT-ORDER Ali\n"
            "ORDER-UPDATE PICKUP Ali 1\n"
            "ORDER-UPDATE DELIVERED Ali 1\n"
            "GET-DRIVER Ali\n"
            "GET-ORDER 1\n"
            "GET-COMPANY\n"
            "END\n")
        self.assertEqual(lines, [
            "user added successfully",
            "user added successfully",
            "score added successfully",
            "score added successfully",
            "4.0",
            "1",
            "1 assigned to Ali",
            "status changed successfully",
            "status changed successfully",
            "FREE (2, 2) 240",
            "DELIVERED Ali 300",
            "60",
        ])


if __name__ == "__main__":
    unittest.main()