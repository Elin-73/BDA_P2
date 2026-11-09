import unittest
from unittest.mock import Mock, patch

from controllers import ENTITY_TYPES
from menu import ConsoleMenu


class ConsoleMenuTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["3", "1", "5"])
    @patch("builtins.print")
    def test_read_action_uses_injected_operations(self, _print, _input):
        operations = Mock()
        operations.read.return_value = []

        ConsoleMenu(operations).run()

        operations.read.assert_called_once_with(ENTITY_TYPES[0])


if __name__ == "__main__":
    unittest.main()
