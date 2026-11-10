from menu_asesores import ConsoleMenu as AdvisorsMenu
from menu_clientes import ConsoleMenu as ClientsMenu
from menu_propiedades import ConsoleMenu as PropertiesMenu
from menu_relaciones import ConsoleMenu as RelationsMenu


class ConsoleMenu:
    def __init__(self, operations):
        self._operations = operations

    def run(self):
        print("¡Bienvenido al portal de la Inmobiliaria Mendoza!")
        while True:
            print("\nSeleccione su tipo de usuario:")
            print("1. Asesor")
            print("2. Jefe / Captador")
            print("0. Salir")
            role = input("Opción: ").strip()
            if role == "0":
                print("Hasta luego.")
                return
            if role == "1":
                self._run_advisor_menu()
            elif role == "2":
                self._run_boss_menu()
            else:
                print("Opción inválida. Intente de nuevo.")

    def _run_advisor_menu(self):
        advisor_id = input("ID del asesor: ").strip()
        advisor = self._operations.get_advisor(advisor_id)
        if advisor is None:
            print(f"No se encontró asesor con ID {advisor_id}.")
            return

        while True:
            print(f"\nMenú de Asesor: {advisor.get('nombre', advisor_id)}")
            print("1. Mi perfil")
            print("2. Clientes")
            print("3. Mis propiedades asignadas")
            print("0. Cerrar sesión")
            choice = input("Opción: ").strip()
            if choice == "0":
                return
            if choice == "1":
                AdvisorsMenu(self._operations, "advisor", advisor_id).run()
            elif choice == "2":
                ClientsMenu(self._operations, "advisor", advisor_id).run()
            elif choice == "3":
                PropertiesMenu(self._operations, "advisor", advisor_id).run()
            else:
                print("Opción inválida. Intente de nuevo.")

    def _run_boss_menu(self):
        while True:
            print("\nMenú de Jefe / Captador:")
            print("1. Asesores")
            print("2. Clientes")
            print("3. Propiedades")
            print("4. Relaciones")
            print("0. Cerrar sesión")
            choice = input("Opción: ").strip()
            if choice == "0":
                return
            if choice == "1":
                AdvisorsMenu(self._operations).run()
            elif choice == "2":
                ClientsMenu(self._operations).run()
            elif choice == "3":
                PropertiesMenu(self._operations).run()
            elif choice == "4":
                RelationsMenu(self._operations).run()
            else:
                print("Opción inválida. Intente de nuevo.")
