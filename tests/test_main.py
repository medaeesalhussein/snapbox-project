import io
import unittest

from main import main


class TestMainCLI(unittest.TestCase):
    def run_cli(self, text):
        out = io.StringIO()
        main(io.StringIO(text), out)
        return out.getvalue().split("\n")[:-1]

    def test_basic_session(self):
        lines = self.run_cli(
            "ADD-DRIVER ali (0, 0) BIKE\n"
            "CREATE-ORDER BIKE (1, 1) (2, 2)\n"
            "ASSIGN-NEXT-ORDER ali\n"
            "ORDER-UPDATE PICKUP ali 1\n"
            "ORDER-UPDATE DELIVERED ali 1\n"
            "GET-DRIVER ali\n"
            "GET-COMPANY\n"
            "END\n"
            "GET-COMPANY\n")
        self.assertEqual(lines, [
            "user added successfully",
            "1",
            "1 assigned to ali",
            "status changed successfully",
            "status changed successfully",
            "FREE (2, 2) 240",
            "60",
        ])

    def test_errors_and_unknown_command(self):
        lines = self.run_cli("ADD-DRIVER bad-name 0 0 BIKE\nHELLO\nGET-ORDER x\nEND\n")
        self.assertEqual(lines, [
            "ERROR: username must be 1-25 English letters/digits",
            "ERROR: unknown command",
            "ERROR: invalid literal for int() with base 10: 'x'",
        ])


if __name__ == "__main__":
    unittest.main()
