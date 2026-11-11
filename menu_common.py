import math


class EntityMenu:
    def __init__(self, operations, entity, role, advisor_id=None):
        self._operations = operations
        self._entity = entity
        self._role = role
        self._advisor_id = advisor_id

    def run(self):
        entity = self._entity
        is_advisor_profile = self._role == "advisor" and entity["label"] == "Asesor"
        can_delete = self._role == "boss" or entity["label"] == "Cliente"
        can_create = not is_advisor_profile
        can_assign_client = entity["label"] == "Cliente"

        while True:
            print(f"\nMenú de {entity['plural'].title()}:")
            options = []
            if is_advisor_profile:
                options = ["Actualizar mi perfil"]
            else:
                if can_create:
                    options.append("Crear")
                options.extend(["Actualizar", "Consultar"])
                if can_delete:
                    options.append("Eliminar")
                if can_assign_client:
                    options.append("Asignar asesor responsable")
            for index, option in enumerate(options, start=1):
                print(f"{index}. {option}")
            print("0. Volver")

            choice = input("Opción: ").strip()
            if choice == "0":
                return
            if not choice.isdigit() or not 1 <= int(choice) <= len(options):
                print("Opción inválida. Intente de nuevo.")
                continue

            action = options[int(choice) - 1]
            if action == "Crear":
                self._create()
            elif action in {"Actualizar", "Actualizar mi perfil"}:
                self._update(is_advisor_profile)
            elif action == "Consultar":
                self._read()
            elif action == "Eliminar":
                self._delete()
            elif action == "Asignar asesor responsable":
                self._assign_responsible_advisor()

    def _create(self):
        latest_id = self._operations.get_latest_id(self._entity)
        next_number = latest_id + 1 if latest_id is not None else 1
        properties = {}
        for field in self._entity["fields"]:
            name = field["name"]
            if name == "id":
                continue
            if self._entity["label"] == "Asesor" and name == "correo_electronico":
                continue
            properties[name] = self._read_field(field)
        properties["id"] = f"{self._entity['id_prefix']}{next_number}"
        if self._entity["label"] == "Asesor":
            properties["correo_electronico"] = (
                f"{properties['nombre']}@Mendoza.mx"
            )
        if self._entity["label"] == "Cliente":
            actor_id = (
                self._advisor_id
                if self._role == "advisor"
                else "boss"
            )
            created = self._operations.create(
                self._entity,
                properties,
                actor_id=actor_id,
                responsible_advisor_id=(
                    self._advisor_id if self._role == "advisor" else None
                ),
            )
        elif self._entity["label"] == "Propiedad" and self._role == "advisor":
            created = self._operations.create(
                self._entity, properties, advisor_id=self._advisor_id
            )
        else:
            created = self._operations.create(self._entity, properties)
        if created:
            print(f"{self._entity['singular'].title()} creada correctamente.")
        else:
            print(f"No se pudo crear la {self._entity['singular']}.")

    def _read(self):
        if self._entity["label"] == "Cliente":
            records = self._operations.read(
                self._entity,
                actor_id=self._advisor_id if self._role == "advisor" else "boss",
            )
        elif self._entity["label"] == "Propiedad" and self._role == "advisor":
            records = self._operations.read(
                self._entity, advisor_id=self._advisor_id
            )
        else:
            records = self._operations.read(self._entity)
        if not records:
            print(f"No hay {self._entity['plural']} registradas.")
            return
        for record in records:
            print(" | ".join(f"{key}: {value}" for key, value in record.items()))

    def _update(self, own_advisor_profile=False):
        if own_advisor_profile:
            identifier = self._advisor_id
        else:
            identifier = input(
                f"ID de la {self._entity['singular']}: "
            ).strip()
        editable_fields = [
            field
            for field in self._entity["fields"]
            if field["name"] != "id"
            and not (
                self._entity["label"] == "Asesor"
                and field["name"] == "correo_electronico"
            )
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
        updates = {field["name"]: value}
        if self._entity["label"] == "Asesor" and field["name"] == "nombre":
            updates["correo_electronico"] = f"{value}@Mendoza.mx"
        if self._entity["label"] == "Cliente":
            updated = self._operations.update(
                self._entity,
                identifier,
                updates,
                actor_id=self._advisor_id if self._role == "advisor" else "boss",
            )
        elif self._entity["label"] == "Propiedad" and self._role == "advisor":
            updated = self._operations.update(
                self._entity,
                identifier,
                updates,
                advisor_id=self._advisor_id,
            )
        else:
            updated = self._operations.update(
                self._entity, identifier, updates
            )
        if updated is None:
            print(f"No se encontró {self._entity['singular']} con ID {identifier}.")
        else:
            print(f"{self._entity['singular'].title()} actualizada correctamente.")

    def _delete(self):
        identifier = input(
            f"ID de la {self._entity['singular']}: "
        ).strip()
        if self._entity["label"] == "Cliente":
            deleted = self._operations.delete(
                self._entity,
                identifier,
                actor_id=self._advisor_id if self._role == "advisor" else "boss",
            )
        else:
            deleted = self._operations.delete(self._entity, identifier)
        if deleted:
            print(f"{self._entity['singular'].title()} eliminada correctamente.")
        else:
            print(f"No se encontró {self._entity['singular']} con ID {identifier}.")

    def _assign_responsible_advisor(self):
        client_id = input("ID del cliente: ").strip()
        advisor_id = input("ID del asesor responsable: ").strip()
        actor_id = self._advisor_id if self._role == "advisor" else "boss"
        if self._operations.assign_client_to_advisor(
            client_id, advisor_id, actor_id
        ):
            print("Asesor responsable asignado correctamente.")
        else:
            print("No se pudo asignar: verifique los IDs y sus permisos.")

    @staticmethod
    def _read_field(field):
        while True:
            value = input(f"{field['prompt']}: ").strip()
            try:
                return field["value_type"](value)
            except ValueError:
                print(f"'{value}' no es un valor válido para {field['prompt']}.")


class RelationsMenu:
    def __init__(self, operations):
        self._operations = operations

    def run(self):
        while True:
            print("\nMenú de Relaciones:")
            print("1. Asignar propiedad a un asesor")
            print("2. Establecer distancia entre propiedades")
            print("3. Consultar propiedades dentro de un radio")
            print("4. Encontrar la ruta más corta entre propiedades")
            print("0. Volver")
            choice = input("Opción: ").strip()
            if choice == "0":
                return
            if choice == "1":
                self._assign_property()
            elif choice == "2":
                self._set_distance()
            elif choice == "3":
                self._query_radius()
            elif choice == "4":
                self._find_shortest_path()
            else:
                print("Opción inválida. Intente de nuevo.")

    def _assign_property(self):
        property_id = input("ID de la propiedad: ").strip()
        advisor_id = input("ID del asesor: ").strip()
        if self._operations.assign_property_to_advisor(property_id, advisor_id):
            print("Propiedad asignada correctamente.")
        else:
            print("No se pudo asignar: verifique los IDs.")

    def _set_distance(self):
        property1_id = input("ID de la primera propiedad: ").strip()
        property2_id = input("ID de la segunda propiedad: ").strip()
        distance = self._read_nonnegative_number(
            "Distancia entre propiedades (en metros): "
        )
        if distance is None:
            return
        if self._operations.set_distance_between_properties(
            property1_id, property2_id, distance
        ):
            print("Distancia establecida correctamente.")
        else:
            print("No se pudo establecer la distancia entre las propiedades.")

    def _query_radius(self):
        property_id = input("ID de la propiedad: ").strip()
        radius = self._read_nonnegative_number("Radio (en metros): ")
        if radius is None:
            return
        properties = self._operations.query_properties_within_radius(
            property_id, radius
        )
        if not properties:
            print("No se encontraron propiedades dentro del radio especificado.")
            return
        for record in properties:
            print(" | ".join(f"{key}: {value}" for key, value in record.items()))

    def _find_shortest_path(self):
        start_id = input("ID de la propiedad de origen: ").strip()
        end_id = input("ID de la propiedad de destino: ").strip()
        result = self._operations.find_shortest_property_path(start_id, end_id)
        if result is None:
            print("No se encontró una ruta entre las propiedades.")
            return
        print("Ruta: " + " -> ".join(result["properties"]))
        print(f"Distancia total: {result['distance']}")

    @staticmethod
    def _read_nonnegative_number(prompt):
        value = input(prompt).strip()
        try:
            number = float(value)
            if not math.isfinite(number) or number < 0:
                raise ValueError
            return number
        except ValueError:
            print("El valor debe ser un número finito no negativo.")
            return None
