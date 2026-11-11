import unittest
from unittest.mock import Mock, patch

from controllers import ENTITY_TYPES
from menu import ConsoleMenu
from menu_asesores import ConsoleMenu as AdvisorsMenu
from menu_clientes import ConsoleMenu as ClientsMenu
from menu_propiedades import ConsoleMenu as PropertiesMenu


class ConsoleMenuTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["2", "2", "3", "0", "0", "0"])
    @patch("menu.getpass.getpass", return_value="secret")
    @patch("builtins.print")
    def test_read_action_uses_injected_operations(self, _print, _password, _input):
        operations = Mock()
        operations.read.return_value = []

        ConsoleMenu(operations, boss_password="secret").run()

        operations.read.assert_called_once_with(ENTITY_TYPES[1], actor_id="boss")

    @patch("builtins.input", side_effect=["1", "a1", "3", "3", "0", "0", "0"])
    @patch("menu.getpass.getpass", return_value="secret")
    @patch("builtins.print")
    def test_advisor_reads_only_assigned_properties(self, _print, _password, _input):
        operations = Mock()
        operations.get_advisor.return_value = {"id": "a1", "nombre": "Ana"}
        operations.read.return_value = []

        ConsoleMenu(
            operations,
            authenticate_advisor=lambda identifier, password: password == "secret",
        ).run()

        operations.read.assert_called_once_with(ENTITY_TYPES[0], advisor_id="a1")

    @patch("builtins.input", side_effect=["2", "0"])
    @patch("menu.getpass.getpass", return_value="wrong")
    @patch("builtins.print")
    def test_boss_menu_requires_env_password(self, _print, _password, _input):
        operations = Mock()

        ConsoleMenu(operations, boss_password="correct").run()

        operations.read.assert_not_called()
        operations.create.assert_not_called()

    @patch("builtins.input", side_effect=["1", "a1", "0", "0"])
    @patch("menu.getpass.getpass", return_value="wrong")
    @patch("builtins.print")
    def test_advisor_menu_requires_account_password(self, _print, _password, _input):
        operations = Mock()
        operations.get_advisor.return_value = {"id": "a1", "nombre": "Ana"}

        ConsoleMenu(
            operations,
            authenticate_advisor=lambda _identifier, password: password == "correct",
        ).run()

        operations.read.assert_not_called()

    @patch("builtins.input", side_effect=["0"])
    @patch("builtins.print")
    def test_advisor_property_menu_does_not_offer_delete(self, print_mock, _input):
        operations = Mock()

        PropertiesMenu(operations, "advisor", "a1").run()

        displayed_options = [call.args[0] for call in print_mock.call_args_list]
        self.assertNotIn("Eliminar", displayed_options)

    @patch("builtins.input", side_effect=["1", "Ana", "555", "0"])
    @patch("builtins.print")
    def test_advisor_creation_generates_id_and_email(self, _print, _input):
        operations = Mock()
        operations.get_latest_id.return_value = 2
        operations.create.return_value = True

        AdvisorsMenu(operations).run()

        operations.create.assert_called_once_with(
            ENTITY_TYPES[2],
            {
                "nombre": "Ana",
                "telefono": "555",
                "id": "a3",
                "correo_electronico": "Ana@Mendoza.mx",
            },
        )

    @patch("builtins.input", side_effect=["1", "Nora", "nora@example.mx", "555", "0"])
    @patch("builtins.print")
    def test_advisor_client_creation_records_creator_and_assigns_self(
        self, _print, _input
    ):
        operations = Mock()
        operations.get_latest_id.return_value = 1
        operations.create.return_value = True

        ClientsMenu(operations, "advisor", "a1").run()

        operations.create.assert_called_once_with(
            ENTITY_TYPES[1],
            {
                "nombre": "Nora",
                "correo_electronico": "nora@example.mx",
                "telefono": "555",
                "id": "c2",
            },
            actor_id="a1",
            responsible_advisor_id="a1",
        )

    @patch("builtins.input", side_effect=["5", "c1", "a2", "0"])
    @patch("builtins.print")
    def test_advisor_can_assign_responsible_advisor_to_own_client(
        self, _print, _input
    ):
        operations = Mock()
        operations.assign_client_to_advisor.return_value = True

        ClientsMenu(operations, "advisor", "a1").run()

        operations.assign_client_to_advisor.assert_called_once_with(
            "c1", "a2", "a1"
        )

    @patch("builtins.input", side_effect=["1", "a1", "4", "0", "0"])
    @patch("menu.getpass.getpass", side_effect=["current", "new-password", "new-password"])
    @patch("builtins.print")
    def test_advisor_can_change_own_password(self, _print, _password, _input):
        operations = Mock()
        operations.get_advisor.return_value = {"id": "a1", "nombre": "Ana"}

        ConsoleMenu(
            operations,
            authenticate_advisor=lambda identifier, password: password == "current",
        ).run()

        operations.change_advisor_password.assert_called_once_with(
            "a1", "new-password"
        )


if __name__ == "__main__":
    unittest.main()
