from controllers import ENTITY_TYPES


class ConsoleMenu:
    def __init__(self, operations):
        self._operations = operations

    def run(self):
        print("¡Bienvenido al portal de la Inmobiliaria Mendoza!")
        while True:
            print("\nSeleccione una opción:")
            print("1. Crear")
            print("2. Actualizar")
            print("3. Leer")
            print("4. Eliminar")
            print("5. Salir")

            choice = input("Opción: ").strip()
            if choice == "5":
                print("Hasta luego.")
                return
            if choice not in {"1", "2", "3", "4"}:
                print("Opción inválida. Intente de nuevo.")
                continue

            entity = self._select_entity()
            if entity is None:
                continue

            if choice == "1":
                self._create(entity)
            elif choice == "2":
                self._update(entity)
            elif choice == "3":
                self._read(entity)
            else:
                self._delete(entity)

    def _select_entity(self):
        print("\nSeleccione el tipo de registro:")
        for index, entity in enumerate(ENTITY_TYPES, start=1):
            print(f"{index}. {entity['singular'].title()}")
        print("0. Volver")

        choice = input("Opción: ").strip()
        if choice == "0":
            return None
        if not choice.isdigit() or not 1 <= int(choice) <= len(ENTITY_TYPES):
            print("Tipo de registro inválido.")
            return None
        return ENTITY_TYPES[int(choice) - 1]

    def _create(self, entity):
        properties = {}
        for field in entity["fields"]:
            properties[field["name"]] = self._read_field(field)

        if self._operations.create(entity, properties):
            print(f"{entity['singular'].title()} creada correctamente.")
        else:
            print(f"No se pudo crear la {entity['singular']}.")

    def _read(self, entity):
        records = self._operations.read(entity)
        if not records:
            print(f"No hay {entity['plural']} registradas.")
            return
        for record in records:
            print(" | ".join(f"{key}: {value}" for key, value in record.items()))

    def _update(self, entity):
        identifier = input(f"ID de la {entity['singular']}: ").strip()
        editable_fields = [
            field for field in entity["fields"] if field["name"] != "id"
        ]

        print("Campos disponibles:")
        for index, field in enumerate(editable_fields, start=1):
            print(f"{index}. {field['prompt']}")

        choice = input("Campo a actualizar: ").strip()
        if not choice.isdigit() or not 1 <= int(choice) <= len(editable_fields):
            print("Campo inválido.")
            return

        field = editable_fields[int(choice) - 1]
        value = self._read_field(field)
        updated = self._operations.update(
            entity, identifier, {field["name"]: value}
        )
        if updated is None:
            print(f"No se encontró {entity['singular']} con ID {identifier}.")
        else:
            print(f"{entity['singular'].title()} actualizada correctamente.")

    def _delete(self, entity):
        identifier = input(f"ID de la {entity['singular']}: ").strip()
        if self._operations.delete(entity, identifier):
            print(f"{entity['singular'].title()} eliminada correctamente.")
        else:
            print(f"No se encontró {entity['singular']} con ID {identifier}.")

    @staticmethod
    def _read_field(field):
        while True:
            value = input(f"{field['prompt']}: ").strip()
            try:
                return field["value_type"](value)
            except ValueError:
                print(f"'{value}' no es un valor válido para {field['prompt']}.")
