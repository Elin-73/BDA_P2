import heapq
import math
import re


ENTITY_TYPES = [
    {
        "label": "Propiedad",
        "id_prefix": "p",
        "singular": "propiedad",
        "plural": "propiedades",
        "fields": [
            {"name": "id", "prompt": "ID", "value_type": str},
            {"name": "direccion", "prompt": "Dirección", "value_type": str},
            {"name": "precio", "prompt": "Precio", "value_type": float},
            {
                "name": "habitaciones",
                "prompt": "Número de habitaciones",
                "value_type": int,
            },
            {"name": "baños", "prompt": "Número de baños", "value_type": int},
            {
                "name": "metros_cuadrados",
                "prompt": "Metros cuadrados",
                "value_type": float,
            },
        ],
    },
    {
        "label": "Cliente",
        "id_prefix": "c",
        "singular": "cliente",
        "plural": "clientes",
        "fields": [
            {"name": "id", "prompt": "ID", "value_type": str},
            {"name": "nombre", "prompt": "Nombre", "value_type": str},
            {
                "name": "correo_electronico",
                "prompt": "Correo electrónico",
                "value_type": str,
            },
            {"name": "telefono", "prompt": "Teléfono", "value_type": str},
        ],
    },
    {
        "label": "Asesor",
        "id_prefix": "a",
        "singular": "asesor",
        "plural": "asesores",
        "fields": [
            {"name": "id", "prompt": "ID", "value_type": str},
            {"name": "nombre", "prompt": "Nombre", "value_type": str},
            {
                "name": "correo_electronico",
                "prompt": "Correo electrónico",
                "value_type": str,
            },
            {"name": "telefono", "prompt": "Teléfono", "value_type": str},
        ],
    },
]

CLIENT_BOSS_CREATOR = "boss"


class MemgraphController:
    def __init__(self, connection, advisor_default_password=None):
        self._connection = connection
        self._advisor_default_password = advisor_default_password

    def create(
        self,
        entity,
        properties,
        advisor_id=None,
        actor_id=None,
        responsible_advisor_id=None,
    ):
        self._validate_properties(entity, properties)
        if entity["label"] == "Cliente":
            if not actor_id:
                raise ValueError("Se requiere identificar quién creó el cliente.")
            if actor_id != CLIENT_BOSS_CREATOR:
                responsible_advisor_id = actor_id
            query = "CREATE (node:Cliente) SET node += $properties, node.created_by = $actor_id "
            parameters = {"properties": properties, "actor_id": actor_id}
            if responsible_advisor_id is not None:
                query = (
                    "MATCH (advisor:Asesor {id: $responsible_advisor_id}) "
                    + query
                    + "CREATE (node)-[:RESPONSIBLE_FOR]->(advisor) "
                )
                parameters["responsible_advisor_id"] = responsible_advisor_id
            query += "RETURN node.id AS id"
            return next(
                iter(self._connection.execute_and_fetch(query, parameters)),
                None,
            ) is not None
        if entity["label"] == "Asesor":
            if self._advisor_default_password is None:
                raise RuntimeError("Falta configurar la contraseña inicial de asesores.")
            self._connection.execute(
                f"CREATE USER {self._format_username(properties['id'])} "
                f"IDENTIFIED BY {self._format_password(self._advisor_default_password)}"
            )
        if entity["label"] == "Propiedad" and advisor_id is not None:
            query = (
                "MATCH (advisor:Asesor {id: $advisor_id}) "
                "CREATE (node:Propiedad) "
                "SET node += $properties "
                "CREATE (advisor)-[:ASSIGNED_TO]->(node) "
                "RETURN node.id AS id"
            )
            parameters = {"advisor_id": advisor_id, "properties": properties}
        else:
            query = (
                f"CREATE (node:{entity['label']}) "
                "SET node += $properties "
                "RETURN node.id AS id"
            )
            parameters = {"properties": properties}
        return next(
            iter(
                self._connection.execute_and_fetch(query, parameters)
            ),
            None,
        ) is not None

    def get_latest_id(self, entity):
        query = f"MATCH (node:{entity['label']}) RETURN node.id AS id"
        identifiers = self._connection.execute_and_fetch(query)
        prefix = entity["id_prefix"]
        suffixes = []
        for record in identifiers:
            match = re.fullmatch(rf"{re.escape(prefix)}(\d+)", str(record["id"]))
            if match:
                suffixes.append(int(match.group(1)))
        return max(suffixes, default=None)

    def read(self, entity, advisor_id=None, actor_id=None):
        if entity["label"] == "Propiedad" and advisor_id is not None:
            query = (
                "MATCH (advisor:Asesor {id: $advisor_id})"
                "-[:ASSIGNED_TO]->(node:Propiedad) "
                "RETURN properties(node) AS properties "
                "ORDER BY node.id"
            )
            records = self._connection.execute_and_fetch(
                query, {"advisor_id": advisor_id}
            )
            return [dict(record["properties"]) for record in records]

        if entity["label"] == "Cliente":
            if not actor_id:
                raise ValueError("Se requiere identificar quién consulta los clientes.")
            parameters = {}
            owner_filter = ""
            if actor_id != CLIENT_BOSS_CREATOR:
                owner_filter = "WHERE node.created_by = $actor_id "
                parameters["actor_id"] = actor_id
            query = (
                "MATCH (node:Cliente) "
                + owner_filter
                + "OPTIONAL MATCH (node)-[:RESPONSIBLE_FOR]->(advisor:Asesor) "
                "RETURN properties(node) AS properties, "
                "advisor.id AS advisor_id, advisor.nombre AS advisor_nombre "
                "ORDER BY node.id"
            )
            records = self._connection.execute_and_fetch(query, parameters)
            clients = []
            for record in records:
                client = dict(record["properties"])
                client.pop("created_by", None)
                advisor_id = record.get("advisor_id")
                advisor_name = record.get("advisor_nombre")
                client["asesor_responsable"] = (
                    f"{advisor_name} ({advisor_id})"
                    if advisor_id is not None
                    else "Sin asignar"
                )
                clients.append(client)
            return clients

        query = (
            f"MATCH (node:{entity['label']}) "
            "RETURN properties(node) AS properties "
            "ORDER BY node.id"
        )
        return [
            dict(record["properties"])
            for record in self._connection.execute_and_fetch(query)
        ]

    def get_advisor(self, identifier):
        query = (
            "MATCH (node:Asesor {id: $id}) "
            "RETURN properties(node) AS properties"
        )
        record = next(
            iter(self._connection.execute_and_fetch(query, {"id": identifier})),
            None,
        )
        return dict(record["properties"]) if record is not None else None

    def update(self, entity, identifier, updates, advisor_id=None, actor_id=None):
        allowed_fields = {
            field["name"] for field in entity["fields"] if field["name"] != "id"
        }
        if not updates or not updates.keys() <= allowed_fields:
            raise ValueError("Seleccione al menos un campo válido para actualizar.")

        parameters = {"id": identifier, "updates": updates}
        if entity["label"] == "Cliente":
            if not actor_id:
                raise ValueError("Se requiere identificar quién actualiza el cliente.")
            query = f"MATCH (node:Cliente {{id: $id}}) "
            if actor_id != CLIENT_BOSS_CREATOR:
                query += "WHERE node.created_by = $actor_id "
                parameters["actor_id"] = actor_id
            query += "SET node += $updates RETURN properties(node) AS properties"
        elif entity["label"] == "Propiedad" and advisor_id is not None:
            query = (
                "MATCH (advisor:Asesor {id: $advisor_id})"
                "-[:ASSIGNED_TO]->(node:Propiedad {id: $id}) "
                "SET node += $updates "
                "RETURN properties(node) AS properties"
            )
            parameters["advisor_id"] = advisor_id
        else:
            query = (
                f"MATCH (node:{entity['label']} {{id: $id}}) "
                "SET node += $updates "
                "RETURN properties(node) AS properties"
            )
        record = next(
            iter(
                self._connection.execute_and_fetch(query, parameters)
            ),
            None,
        )
        return dict(record["properties"]) if record is not None else None

    def delete(self, entity, identifier, actor_id=None):
        advisor_username = (
            self._advisor_username(identifier)
            if entity["label"] == "Asesor"
            else None
        )
        query = f"MATCH (node:{entity['label']} {{id: $id}}) "
        parameters = {"id": identifier}
        if entity["label"] == "Cliente":
            if not actor_id:
                raise ValueError("Se requiere identificar quién elimina el cliente.")
            if actor_id != CLIENT_BOSS_CREATOR:
                query += "WHERE node.created_by = $actor_id "
                parameters["actor_id"] = actor_id
        query += (
            "WITH collect(node) AS matches "
            "FOREACH (node IN matches | DETACH DELETE node) "
            "RETURN size(matches) AS deleted"
        )
        record = next(
            iter(self._connection.execute_and_fetch(query, parameters)),
            None,
        )
        deleted = record is not None and record["deleted"] > 0
        if deleted and advisor_username is not None:
            self._connection.execute(f"DROP USER {advisor_username}")
        return deleted

    def assign_client_to_advisor(self, client_id, advisor_id, actor_id):
        if not actor_id:
            raise ValueError("Se requiere identificar quién asigna el cliente.")
        query = (
            "MATCH (client:Cliente {id: $client_id}) "
            "MATCH (advisor:Asesor {id: $advisor_id}) "
        )
        parameters = {"client_id": client_id, "advisor_id": advisor_id}
        if actor_id != CLIENT_BOSS_CREATOR:
            query += "WHERE client.created_by = $actor_id "
            parameters["actor_id"] = actor_id
        query += (
            "OPTIONAL MATCH (client)-[previous:RESPONSIBLE_FOR]->(:Asesor) "
            "WITH client, advisor, collect(previous) AS previous_relations "
            "FOREACH (previous IN previous_relations | DELETE previous) "
            "MERGE (client)-[:RESPONSIBLE_FOR]->(advisor) "
            "RETURN client.id AS id"
        )
        record = next(
            iter(self._connection.execute_and_fetch(query, parameters)),
            None,
        )
        return record is not None

    def change_advisor_password(self, identifier, new_password):
        self._connection.execute(
            f"SET PASSWORD FOR {self._format_username(identifier)} "
            f"TO {self._format_password(new_password)}"
        )

    @staticmethod
    def _format_username(identifier):
        username = MemgraphController._advisor_username(identifier)
        if username is None:
            raise ValueError("El ID del asesor no es válido para una cuenta de usuario.")
        return username

    @staticmethod
    def _advisor_username(identifier):
        if isinstance(identifier, str) and re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_]*", identifier
        ):
            return identifier
        return None

    @staticmethod
    def _format_password(password):
        if not isinstance(password, str) or not password or not password.isprintable():
            raise ValueError("La contraseña debe contener caracteres imprimibles.")
        escaped = password.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"

    def assign_property_to_advisor(self, property_id, advisor_id):
        query = (
            "MATCH (property:Propiedad {id: $property_id}) "
            "MATCH (advisor:Asesor {id: $advisor_id}) "
            "MERGE (advisor)-[:ASSIGNED_TO]->(property) "
            "RETURN property.id AS id"
        )
        record = next(
            iter(
                self._connection.execute_and_fetch(
                    query, {"property_id": property_id, "advisor_id": advisor_id}
                )
            ),
            None,
        )
        return record is not None

    def set_distance_between_properties(self, property1_id, property2_id, distance):
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("La distancia debe ser un número finito no negativo.")
        if property1_id == property2_id:
            return False

        query = (
            "MATCH (p1:Propiedad {id: $property1_id}) "
            "MATCH (p2:Propiedad {id: $property2_id}) "
            "WHERE p1 <> p2 "
            "MERGE (p1)-[r:DISTANCE_TO]-(p2) "
            "SET r.distance = $distance "
            "RETURN r.distance AS distance"
        )
        record = next(
            iter(
                self._connection.execute_and_fetch(
                    query,
                    {
                        "property1_id": property1_id,
                        "property2_id": property2_id,
                        "distance": distance,
                    },
                )
            ),
            None,
        )
        return record is not None

    def query_properties_within_radius(self, entity_id, radius):
        query = (
            "MATCH (p:Propiedad {id: $entity_id})"
            "-[r:DISTANCE_TO]-(other:Propiedad) "
            "WHERE r.distance <= $radius "
            "RETURN other.id AS id, other.direccion AS direccion, "
            "other.precio AS precio, other.habitaciones AS habitaciones, "
            "other.baños AS baños, other.metros_cuadrados AS metros_cuadrados"
        )
        results = self._connection.execute_and_fetch(
            query, {"entity_id": entity_id, "radius": radius}
        )
        return [dict(record) for record in results]

    def find_shortest_property_path(self, start_id, end_id):
        property_records = self._connection.execute_and_fetch(
            "MATCH (p:Propiedad) RETURN p.id AS id"
        )
        property_ids = {record["id"] for record in property_records}
        if start_id not in property_ids or end_id not in property_ids:
            return None
        if start_id == end_id:
            return {"properties": [start_id], "distance": 0}

        query = (
            "MATCH (p1:Propiedad)-[r:DISTANCE_TO]-(p2:Propiedad) "
            "RETURN p1.id AS source_id, p2.id AS target_id, "
            "r.distance AS distance"
        )
        records = self._connection.execute_and_fetch(query)
        adjacency = {}
        for record in records:
            source_id = record["source_id"]
            target_id = record["target_id"]
            distance = record["distance"]
            if distance is None or not math.isfinite(distance) or distance < 0:
                raise ValueError("Las relaciones deben tener una distancia válida.")
            adjacency.setdefault(source_id, []).append((target_id, distance))
            adjacency.setdefault(target_id, []).append((source_id, distance))

        distances = {start_id: 0}
        previous = {}
        queue = [(0, start_id)]
        while queue:
            current_distance, current_id = heapq.heappop(queue)
            if current_distance != distances[current_id]:
                continue
            if current_id == end_id:
                break
            for neighbor_id, edge_distance in adjacency.get(current_id, []):
                candidate_distance = current_distance + edge_distance
                if candidate_distance < distances.get(neighbor_id, float("inf")):
                    distances[neighbor_id] = candidate_distance
                    previous[neighbor_id] = current_id
                    heapq.heappush(queue, (candidate_distance, neighbor_id))

        if end_id not in distances:
            return None

        path = [end_id]
        while path[-1] != start_id:
            path.append(previous[path[-1]])
        path.reverse()
        return {"properties": path, "distance": distances[end_id]}

    @staticmethod
    def _validate_properties(entity, properties):
        expected_fields = {field["name"] for field in entity["fields"]}
        if properties.keys() != expected_fields:
            raise ValueError(
                f"Los campos para {entity['singular']} no coinciden con el modelo."
            )
