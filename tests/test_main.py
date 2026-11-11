import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

import main


class MainConfigurationTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "MEMGRAPH_HOST": "db-host",
            "MEMGRAPH_PORT": "7687",
            "MEMGRAPH_USERNAME": "db-user",
            "MEMGRAPH_PASSWORD": "db-password",
            "BOSS_PASSWORD": "boss-password",
            "ASESOR_DEFAULT_PASSWORD": "advisor-default",
        },
    )
    def test_database_and_boss_use_separate_passwords(self):
        gqlalchemy = types.ModuleType("gqlalchemy")
        gqlalchemy.Memgraph = Mock(return_value=object())
        gqlalchemy.__path__ = []
        exceptions = types.ModuleType("gqlalchemy.exceptions")
        exceptions.GQLAlchemyWaitForConnectionError = type(
            "GQLAlchemyWaitForConnectionError", (Exception,), {}
        )
        menu = Mock()

        with (
            patch.dict(
                sys.modules,
                {
                    "gqlalchemy": gqlalchemy,
                    "gqlalchemy.exceptions": exceptions,
                },
            ),
            patch.object(main, "load_dotenv"),
            patch.object(main, "ConsoleMenu", menu),
            patch("builtins.print"),
        ):
            main.main()

        gqlalchemy.Memgraph.assert_called_once_with(
            "db-host",
            7687,
            "db-user",
            "db-password",
            encrypted=True,
        )
        menu.assert_called_once()
        self.assertEqual(menu.call_args.kwargs["boss_password"], "boss-password")
        self.assertNotEqual(
            gqlalchemy.Memgraph.call_args.args[3],
            menu.call_args.kwargs["boss_password"],
        )


if __name__ == "__main__":
    unittest.main()
