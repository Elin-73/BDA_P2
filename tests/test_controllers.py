import unittest

from controllers import ENTITY_TYPES, MemgraphController


class FakeConnection:
    def __init__(self, records: list[dict[str, object]] | None = None) -> None:
        self.records = records or []
        self.query = ""
        self.parameters: dict[str, object] | None = None

    def execute_and_fetch(
        self,
        query: str,
        parameters: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        self.query = query
        self.parameters = parameters
        return self.records


class MemgraphControllerTests(unittest.TestCase):
    def test_create_passes_values_as_query_parameters(self) -> None:
        connection = FakeConnection([{"id": "p1"}])
        controller = MemgraphController(connection)
        properties = {
            "id": "p1",
            "direccion": "Calle 1' RETURN node //",
            "precio": 100.0,
            "habitaciones": 2,
            "baños": 1,
            "metros_cuadrados": 80.0,
        }

        created = controller.create(ENTITY_TYPES[0], properties)

        self.assertTrue(created)
        self.assertNotIn("Calle 1", connection.query)
        self.assertEqual(connection.parameters, {"properties": properties})

    def test_read_returns_records_for_selected_entity(self) -> None:
        connection = FakeConnection([{"properties": {"id": "c1", "nombre": "Ana"}}])
        controller = MemgraphController(connection)

        records = controller.read(ENTITY_TYPES[1])

        self.assertEqual(records, [{"id": "c1", "nombre": "Ana"}])
        self.assertIn("MATCH (node:Cliente)", connection.query)

    def test_update_rejects_id_and_unknown_fields(self) -> None:
        controller = MemgraphController(FakeConnection())

        with self.assertRaises(ValueError):
            controller.update(ENTITY_TYPES[1], "c1", {"id": "c2"})

        with self.assertRaises(ValueError):
            controller.update(ENTITY_TYPES[1], "c1", {"unknown": "value"})

    def test_delete_uses_id_parameter_and_reports_missing_records(self) -> None:
        connection = FakeConnection([{"deleted": 0}])
        controller = MemgraphController(connection)

        deleted = controller.delete(ENTITY_TYPES[2], "a' OR true //")

        self.assertFalse(deleted)
        self.assertNotIn("a' OR true", connection.query)
        self.assertEqual(connection.parameters, {"id": "a' OR true //"})


if __name__ == "__main__":
    unittest.main()
