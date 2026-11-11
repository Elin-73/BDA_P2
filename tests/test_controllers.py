import unittest

from controllers import ENTITY_TYPES, MemgraphController


class FakeConnection:
    def __init__(self, records=None):
        self.records = records or []
        self.query = ""
        self.parameters = None
        self.executed_queries = []

    def execute_and_fetch(self, query, parameters=None):
        self.query = query
        self.parameters = parameters
        return self.records

    def execute(self, query, parameters=None):
        self.executed_queries.append((query, parameters))


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

    def test_create_advisor_issues_create_user_with_configured_password(self):
        connection = FakeConnection([{"id": "a1"}])
        controller = MemgraphController(connection, "default'pass")
        properties = {
            "id": "a1",
            "nombre": "Ana",
            "correo_electronico": "Ana@Mendoza.mx",
            "telefono": "555",
        }

        self.assertTrue(controller.create(ENTITY_TYPES[2], properties))

        self.assertEqual(
            connection.executed_queries[0][0],
            "CREATE USER a1 IDENTIFIED BY 'default\\'pass'",
        )
        self.assertIn("CREATE (node:Asesor)", connection.query)

    def test_get_latest_id_returns_highest_numeric_suffix(self):
        connection = FakeConnection(
            [{"id": "p9"}, {"id": "p12"}, {"id": "p2"}, {"id": "other"}]
        )

        latest_id = MemgraphController(connection).get_latest_id(ENTITY_TYPES[0])

        self.assertEqual(latest_id, 12)
        self.assertIn("MATCH (node:Propiedad)", connection.query)

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

    def test_create_client_records_creator_and_responsible_advisor(self):
        connection = FakeConnection([{"id": "c1"}])
        properties = {
            "id": "c1",
            "nombre": "Nora",
            "correo_electronico": "nora@example.mx",
            "telefono": "555",
        }

        created = MemgraphController(connection).create(
            ENTITY_TYPES[1],
            properties,
            actor_id="a1",
            responsible_advisor_id="a1",
        )

        self.assertTrue(created)
        self.assertIn("node.created_by = $actor_id", connection.query)
        self.assertIn("CREATE (node)-[:RESPONSIBLE_FOR]->(advisor)", connection.query)
        self.assertEqual(
            connection.parameters,
            {
                "properties": properties,
                "actor_id": "a1",
                "responsible_advisor_id": "a1",
            },
        )

    def test_create_client_requires_creator(self):
        with self.assertRaises(ValueError):
            MemgraphController(FakeConnection()).create(
                ENTITY_TYPES[1], {"id": "c1"}
            )

    def test_read_returns_records_for_selected_entity(self):
        connection = FakeConnection([{"properties": {"id": "c1", "nombre": "Ana"}}])
        controller = MemgraphController(connection)

        records = controller.read(ENTITY_TYPES[1], actor_id="boss")

        self.assertEqual(
            records,
            [
                {
                    "id": "c1",
                    "nombre": "Ana",
                    "asesor_responsable": "Sin asignar",
                }
            ],
        )
        self.assertIn("MATCH (node:Cliente)", connection.query)

    def test_read_client_only_returns_records_created_by_advisor(self):
        connection = FakeConnection(
            [
                {
                    "properties": {
                        "id": "c1",
                        "nombre": "Ana",
                        "created_by": "a1",
                    },
                    "advisor_id": "a2",
                    "advisor_nombre": "Luis",
                }
            ]
        )

        records = MemgraphController(connection).read(
            ENTITY_TYPES[1], actor_id="a1"
        )

        self.assertEqual(
            records,
            [
                {
                    "id": "c1",
                    "nombre": "Ana",
                    "asesor_responsable": "Luis (a2)",
                }
            ],
        )
        self.assertIn("WHERE node.created_by = $actor_id", connection.query)
        self.assertEqual(connection.parameters, {"actor_id": "a1"})

    def test_update_rejects_id_and_unknown_fields(self):
        controller = MemgraphController(FakeConnection())

        with self.assertRaises(ValueError):
            controller.update(ENTITY_TYPES[1], "c1", {"id": "c2"})

        with self.assertRaises(ValueError):
            controller.update(ENTITY_TYPES[1], "c1", {"unknown": "value"})

    def test_update_client_is_scoped_to_creator(self):
        connection = FakeConnection([{"properties": {"id": "c1"}}])

        MemgraphController(connection).update(
            ENTITY_TYPES[1],
            "c1",
            {"nombre": "Nuevo"},
            actor_id="a1",
        )

        self.assertIn("WHERE node.created_by = $actor_id", connection.query)
        self.assertEqual(
            connection.parameters,
            {"id": "c1", "updates": {"nombre": "Nuevo"}, "actor_id": "a1"},
        )

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

        deleted = controller.delete(ENTITY_TYPES[0], "p' OR true //")

        self.assertFalse(deleted)
        self.assertNotIn("p' OR true", connection.query)
        self.assertEqual(connection.parameters, {"id": "p' OR true //"})

    def test_delete_client_is_scoped_to_creator(self):
        connection = FakeConnection([{"deleted": 0}])

        deleted = MemgraphController(connection).delete(
            ENTITY_TYPES[1], "c1", actor_id="a1"
        )

        self.assertFalse(deleted)
        self.assertIn("WHERE node.created_by = $actor_id", connection.query)
        self.assertEqual(connection.parameters, {"id": "c1", "actor_id": "a1"})

    def test_assign_client_replaces_responsible_advisor_and_checks_creator(self):
        connection = FakeConnection([{"id": "c1"}])

        assigned = MemgraphController(connection).assign_client_to_advisor(
            "c1", "a2", "a1"
        )

        self.assertTrue(assigned)
        self.assertIn("WHERE client.created_by = $actor_id", connection.query)
        self.assertIn("collect(previous) AS previous_relations", connection.query)
        self.assertIn("MERGE (client)-[:RESPONSIBLE_FOR]->(advisor)", connection.query)
        self.assertEqual(
            connection.parameters,
            {"client_id": "c1", "advisor_id": "a2", "actor_id": "a1"},
        )

    def test_delete_legacy_numeric_advisor_without_user_account(self):
        connection = FakeConnection([{"deleted": 1}])

        deleted = MemgraphController(connection).delete(ENTITY_TYPES[2], 1)

        self.assertTrue(deleted)
        self.assertIn("MATCH (node:Asesor", connection.query)
        self.assertEqual(connection.parameters, {"id": 1})
        self.assertEqual(connection.executed_queries, [])

    def test_delete_advisor_with_non_username_id_does_not_run_user_command(self):
        connection = FakeConnection([{"deleted": 1}])

        deleted = MemgraphController(connection).delete(
            ENTITY_TYPES[2], "a' OR true //"
        )

        self.assertTrue(deleted)
        self.assertNotIn("a' OR true", connection.query)
        self.assertEqual(connection.parameters, {"id": "a' OR true //"})
        self.assertEqual(connection.executed_queries, [])

    def test_delete_advisor_drops_user_after_deleting_node(self):
        connection = FakeConnection([{"deleted": 1}])

        deleted = MemgraphController(connection).delete(ENTITY_TYPES[2], "a1")

        self.assertTrue(deleted)
        self.assertEqual(connection.executed_queries, [("DROP USER a1", None)])

    def test_change_advisor_password_escapes_password_and_validates_id(self):
        connection = FakeConnection()
        controller = MemgraphController(connection)

        controller.change_advisor_password("a1", "new'pass")

        self.assertEqual(
            connection.executed_queries,
            [("SET PASSWORD FOR a1 TO 'new\\'pass'", None)],
        )
        with self.assertRaises(ValueError):
            controller.change_advisor_password("a1' OR true //", "password")

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
