from dataclasses import dataclass
from typing import Iterable, Protocol


class QueryConnection(Protocol):
    def execute_and_fetch(
        self, query: str, parameters: dict[str, object] | None = None
    ) -> Iterable[dict[str, object]]: ...


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    prompt: str
    value_type: type[str] | type[int] | type[float] = str


@dataclass(frozen=True)
class EntityDefinition:
    label: str
    singular: str
    plural: str
    fields: tuple[FieldDefinition, ...]


ENTITY_TYPES = (
    EntityDefinition(
        "Propiedad",
        "propiedad",
        "propiedades",
        (
            FieldDefinition("id", "ID"),
            FieldDefinition("direccion", "Dirección"),
            FieldDefinition("precio", "Precio", float),
            FieldDefinition("habitaciones", "Número de habitaciones", int),
            FieldDefinition("baños", "Número de baños", int),
            FieldDefinition("metros_cuadrados", "Metros cuadrados", float),
        ),
    ),
    EntityDefinition(
        "Cliente",
        "cliente",
        "clientes",
        (
            FieldDefinition("id", "ID"),
            FieldDefinition("nombre", "Nombre"),
            FieldDefinition("correo_electronico", "Correo electrónico"),
            FieldDefinition("telefono", "Teléfono"),
        ),
    ),
    EntityDefinition(
        "Asesor",
        "asesor",
        "asesores",
        (
            FieldDefinition("id", "ID"),
            FieldDefinition("nombre", "Nombre"),
            FieldDefinition("correo_electronico", "Correo electrónico"),
            FieldDefinition("telefono", "Teléfono"),
        ),
    ),
)


class MemgraphController:
    def __init__(self, connection: QueryConnection) -> None:
        self._connection = connection

    def create(
        self, entity: EntityDefinition, properties: dict[str, object]
    ) -> bool:
        self._validate_properties(entity, properties)
        query = (
            f"CREATE (node:{entity.label}) "
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

    def read(self, entity: EntityDefinition) -> list[dict[str, object]]:
        query = (
            f"MATCH (node:{entity.label}) "
            "RETURN properties(node) AS properties "
            "ORDER BY node.id"
        )
        return [
            dict(record["properties"])
            for record in self._connection.execute_and_fetch(query)
        ]

    def update(
        self,
        entity: EntityDefinition,
        identifier: str,
        updates: dict[str, object],
    ) -> dict[str, object] | None:
        allowed_fields = {field.name for field in entity.fields} - {"id"}
        if not updates or not updates.keys() <= allowed_fields:
            raise ValueError("Seleccione al menos un campo válido para actualizar.")

        query = (
            f"MATCH (node:{entity.label} {{id: $id}}) "
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

    def delete(self, entity: EntityDefinition, identifier: str) -> bool:
        query = (
            f"MATCH (node:{entity.label} {{id: $id}}) "
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
    def _validate_properties(
        entity: EntityDefinition, properties: dict[str, object]
    ) -> None:
        expected_fields = {field.name for field in entity.fields}
        if properties.keys() != expected_fields:
            raise ValueError(
                f"Los campos para {entity.singular} no coinciden con el modelo."
            )
