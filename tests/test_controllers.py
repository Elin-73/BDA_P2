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

    def test_create_for_advisor_assigns_property_to_existing_advisor(self):
        connection = FakeConnection([{"id": "p1"}])
        controller = MemgraphController(connection)
        properties = {
            "id": "p1",
            "direccion": "Calle 1",
            "precio": 100.0,
            "habitaciones": 2,
            "baños": 1,
            "metros_cuadrados": 80.0,
        }

        created = controller.create(ENTITY_TYPES[0], properties, advisor_id="a1")

        self.assertTrue(created)
        self.assertIn("MATCH (advisor:Asesor", connection.query)
        self.assertIn("CREATE (advisor)-[:ASSIGNED_TO]->(node)", connection.query)
        self.assertEqual(
            connection.parameters, {"advisor_id": "a1", "properties": properties}
        )

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

    def test_advisor_property_read_and_update_are_scoped_to_assignment(self):
        connection = FakeConnection([{"properties": {"id": "p1"}}])
        controller = MemgraphController(connection)

        controller.read(ENTITY_TYPES[0], advisor_id="a1")
        self.assertIn("(advisor:Asesor {id: $advisor_id})-[:ASSIGNED_TO]", connection.query)
        self.assertEqual(connection.parameters, {"advisor_id": "a1"})

        controller.update(
            ENTITY_TYPES[0], "p1", {"precio": 200.0}, advisor_id="a1"
        )
        self.assertIn("(advisor:Asesor {id: $advisor_id})-[:ASSIGNED_TO]", connection.query)
        self.assertEqual(
            connection.parameters,
            {"id": "p1", "updates": {"precio": 200.0}, "advisor_id": "a1"},
        )

    def test_get_advisor_uses_parameterized_identifier(self):
        connection = FakeConnection([{"properties": {"id": "a1"}}])

        advisor = MemgraphController(connection).get_advisor("a1")

        self.assertEqual(advisor, {"id": "a1"})
        self.assertEqual(connection.parameters, {"id": "a1"})

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

        created = controller.set_distance_between_properties("p1", "p2", 5.0)

        self.assertTrue(created)
        self.assertIn("MATCH (p1:Propiedad", connection.query)
        self.assertIn("MATCH (p2:Propiedad", connection.query)
        self.assertIn("MERGE (p1)-[r:DISTANCE_TO]-(p2)", connection.query)
        self.assertNotIn("CREATE", connection.query)
        self.assertEqual(
            connection.parameters,
            {"property1_id": "p1", "property2_id": "p2", "distance": 5.0},
        )

    def test_property_assignment_links_existing_nodes(self):
        connection = FakeConnection([{"id": "p1"}])

        assigned = MemgraphController(connection).assign_property_to_advisor(
            "p1", "a1"
        )

        self.assertTrue(assigned)
        self.assertIn("MATCH (property:Propiedad", connection.query)
        self.assertIn("MATCH (advisor:Asesor", connection.query)
        self.assertIn("MERGE (advisor)-[:ASSIGNED_TO]->(property)", connection.query)
        self.assertEqual(
            connection.parameters, {"property_id": "p1", "advisor_id": "a1"}
        )

    def test_set_distance_returns_false_when_properties_do_not_exist(self):
        controller = MemgraphController(FakeConnection())

        self.assertFalse(
            controller.set_distance_between_properties("missing1", "missing2", 5)
        )

    def test_set_distance_rejects_negative_or_non_finite_values(self):
        controller = MemgraphController(FakeConnection())

        for distance in (-1, float("inf"), float("nan")):
            with self.subTest(distance=distance):
                with self.assertRaises(ValueError):
                    controller.set_distance_between_properties("p1", "p2", distance)

    def test_radius_query_uses_stored_distance_relationship(self):
        connection = FakeConnection([{"id": "p2", "direccion": "Calle 2"}])
        controller = MemgraphController(connection)

        properties = controller.query_properties_within_radius("p1", 6.0)

        self.assertEqual(properties, [{"id": "p2", "direccion": "Calle 2"}])
        self.assertIn("-[r:DISTANCE_TO]-(other:Propiedad)", connection.query)
        self.assertIn("r.distance <= $radius", connection.query)
        self.assertNotIn("distance(", connection.query)
        self.assertEqual(connection.parameters, {"entity_id": "p1", "radius": 6.0})

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
