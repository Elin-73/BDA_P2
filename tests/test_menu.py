import unittest
from unittest.mock import Mock, patch

from controllers import ENTITY_TYPES
from menu import ConsoleMenu
from menu_propiedades import ConsoleMenu as PropertiesMenu


class ConsoleMenuTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["2", "2", "3", "0", "0", "0"])
    @patch("builtins.print")
    def test_read_action_uses_injected_operations(self, _print, _input):
        operations = Mock()
        operations.read.return_value = []

        ConsoleMenu(operations).run()

        operations.read.assert_called_once_with(ENTITY_TYPES[1])

    @patch("builtins.input", side_effect=["1", "a1", "3", "3", "0", "0", "0"])
    @patch("builtins.print")
    def test_advisor_reads_only_assigned_properties(self, _print, _input):
        operations = Mock()
        operations.get_advisor.return_value = {"id": "a1", "nombre": "Ana"}
        operations.read.return_value = []

        ConsoleMenu(operations).run()

        operations.read.assert_called_once_with(ENTITY_TYPES[0], advisor_id="a1")

    @patch("builtins.input", side_effect=["0"])
    @patch("builtins.print")
    def test_advisor_property_menu_does_not_offer_delete(self, print_mock, _input):
        operations = Mock()

        PropertiesMenu(operations, "advisor", "a1").run()

        displayed_options = [call.args[0] for call in print_mock.call_args_list]
        self.assertNotIn("Eliminar", displayed_options)


if __name__ == "__main__":
    unittest.main()
