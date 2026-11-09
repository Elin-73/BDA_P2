import unittest
from unittest.mock import Mock, patch

from controllers import ENTITY_TYPES
from menu import ConsoleMenu


class ConsoleMenuTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["3", "1", "8"])
    @patch("builtins.print")
    def test_read_action_uses_injected_operations(self, _print, _input):
        operations = Mock()
        operations.read.return_value = []

        ConsoleMenu(operations).run()

        operations.read.assert_called_once_with(ENTITY_TYPES[0])

    @patch("builtins.input", side_effect=["7", "p1", "p2", "8"])
    @patch("builtins.print")
    def test_shortest_path_option_uses_property_ids(self, _print, _input):
        operations = Mock()
        operations.find_shortest_property_path.return_value = {
            "properties": ["p1", "p3", "p2"],
            "distance": 12,
        }

        ConsoleMenu(operations).run()

        operations.find_shortest_property_path.assert_called_once_with("p1", "p2")

    @patch("builtins.input", side_effect=["5", "p1", "p2", "8"])
    @patch("builtins.print")
    def test_distance_option_uses_two_property_ids(self, _print, _input):
        operations = Mock()

        ConsoleMenu(operations).run()

        operations.set_distance_between_properties.assert_called_once_with(
            "p1", "p2"
        )


if __name__ == "__main__":
    unittest.main()
