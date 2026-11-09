ENTITY_TYPES = [
    {
        "label": "Propiedad",
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


class MemgraphController:
    def __init__(self, connection):
        self._connection = connection

    def create(self, entity, properties):
        self._validate_properties(entity, properties)
        query = (
            f"CREATE (node:{entity['label']}) "
            "SET node += $properties "
            "RETURN node.id AS id"
        )
        return next(
            iter(
                self._connection.execute_and_fetch(
                    query, {"properties": properties}
                )
            ),
            None,
        ) is not None

    def read(self, entity):
        query = (
            f"MATCH (node:{entity['label']}) "
            "RETURN properties(node) AS properties "
            "ORDER BY node.id"
        )
        return [
            dict(record["properties"])
            for record in self._connection.execute_and_fetch(query)
        ]

    def update(self, entity, identifier, updates):
        allowed_fields = {
            field["name"] for field in entity["fields"] if field["name"] != "id"
        }
        if not updates or not updates.keys() <= allowed_fields:
            raise ValueError("Seleccione al menos un campo válido para actualizar.")

        query = (
            f"MATCH (node:{entity['label']} {{id: $id}}) "
            "SET node += $updates "
            "RETURN properties(node) AS properties"
        )
        record = next(
            iter(
                self._connection.execute_and_fetch(
                    query, {"id": identifier, "updates": updates}
                )
            ),
            None,
        )
        return dict(record["properties"]) if record is not None else None

    def delete(self, entity, identifier):
        query = (
            f"MATCH (node:{entity['label']} {{id: $id}}) "
            "WITH collect(node) AS matches "
            "FOREACH (node IN matches | DETACH DELETE node) "
            "RETURN size(matches) AS deleted"
        )
        record = next(
            iter(self._connection.execute_and_fetch(query, {"id": identifier})),
            None,
        )
        return record is not None and record["deleted"] > 0

    @staticmethod
    def _validate_properties(entity, properties):
        expected_fields = {field["name"] for field in entity["fields"]}
        if properties.keys() != expected_fields:
            raise ValueError(
                f"Los campos para {entity['singular']} no coinciden con el modelo."
            )
