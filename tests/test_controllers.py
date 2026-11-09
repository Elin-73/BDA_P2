import unittest

from controllers import ENTITY_TYPES, MemgraphController


class FakeConnection:
    def __init__(self, records=None):
        self.records = records or []
        self.query = ""
        self.parameters = None

    def execute_and_fetch(self, query, parameters=None):
        self.query = query
        self.parameters = parameters
        return self.records


class MemgraphControllerTests(unittest.TestCase):
    def test_create_passes_values_as_query_parameters(self):
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

    def test_read_returns_records_for_selected_entity(self):
        connection = FakeConnection([{"properties": {"id": "c1", "nombre": "Ana"}}])
        controller = MemgraphController(connection)

        records = controller.read(ENTITY_TYPES[1])

        self.assertEqual(records, [{"id": "c1", "nombre": "Ana"}])
        self.assertIn("MATCH (node:Cliente)", connection.query)

    def test_update_rejects_id_and_unknown_fields(self):
        controller = MemgraphController(FakeConnection())

        with self.assertRaises(ValueError):
            controller.update(ENTITY_TYPES[1], "c1", {"id": "c2"})

        with self.assertRaises(ValueError):
            controller.update(ENTITY_TYPES[1], "c1", {"unknown": "value"})

    def test_delete_uses_id_parameter_and_reports_missing_records(self):
        connection = FakeConnection([{"deleted": 0}])
        controller = MemgraphController(connection)

        deleted = controller.delete(ENTITY_TYPES[2], "a' OR true //")

        self.assertFalse(deleted)
        self.assertNotIn("a' OR true", connection.query)
        self.assertEqual(connection.parameters, {"id": "a' OR true //"})

    def test_set_distance_uses_property_ids_as_parameters(self):
        connection = FakeConnection([{"distance": 5.0}])
        controller = MemgraphController(connection)

        created = controller.set_distance_between_properties("p1", "p2")

        self.assertTrue(created)
        self.assertNotIn("'p1'", connection.query)
        self.assertEqual(
            connection.parameters, {"property1_id": "p1", "property2_id": "p2"}
        )

    def test_shortest_property_path_uses_total_distance(self):
        class PathConnection:
            def execute_and_fetch(self, query, parameters=None):
                if "RETURN p.id AS id" in query:
                    return [{"id": property_id} for property_id in ("p1", "p2", "p3")]
                return [
                    {"source_id": "p1", "target_id": "p2", "distance": 3},
                    {"source_id": "p1", "target_id": "p3", "distance": 1},
                    {"source_id": "p3", "target_id": "p2", "distance": 1},
                ]

        result = MemgraphController(PathConnection()).find_shortest_property_path(
            "p1", "p2"
        )

        self.assertEqual(result, {"properties": ["p1", "p3", "p2"], "distance": 2})

    def test_shortest_property_path_returns_none_when_unreachable(self):
        class PathConnection:
            def execute_and_fetch(self, query, parameters=None):
                if "RETURN p.id AS id" in query:
                    return [{"id": "p1"}, {"id": "p2"}]
                return []

        result = MemgraphController(PathConnection()).find_shortest_property_path(
            "p1", "p2"
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
