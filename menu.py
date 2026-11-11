import getpass
import hmac

from menu_asesores import ConsoleMenu as AdvisorsMenu
from menu_clientes import ConsoleMenu as ClientsMenu
from menu_propiedades import ConsoleMenu as PropertiesMenu
from menu_relaciones import ConsoleMenu as RelationsMenu
#Existen 4 tipos de menus, aquí solo los importo como su propia variable

class ConsoleMenu:
    def __init__(
        self,
        operations,
        boss_password=None,
        authenticate_advisor=None,
    ):
        self._operations = operations
        self._boss_password = boss_password
        self._authenticate_advisor = authenticate_advisor
        #El menú de consola se inicia como objeto con estos parámetros.
    def run(self):
        print("¡Bienvenido al portal de la Inmobiliaria Mendoza!")
        while True:
            print("\nSeleccione su tipo de usuario:")
            print("1. Asesor")
            print("2. Jefe / Captador")
            print("0. Salir")
            role = input("Opción: ").strip()
            #Aquí pedimos el rol del usuario y le pediremos contraseaña, el ID igual si es asesor.
            if role == "0":
                print("Hasta luego.")
                return
            if role == "1":
                self._run_advisor_menu()
            elif role == "2":
                password = getpass.getpass("Contraseña: ")
                if self._boss_password is not None and hmac.compare_digest(
                    password, self._boss_password
                ):
                    self._run_boss_menu()
                else:
                    print("Contraseña incorrecta.")
            else:
                print("Opción inválida. Intente de nuevo.")

    def _run_advisor_menu(self):
        advisor_id = input("ID del asesor: ").strip()
        advisor = self._operations.get_advisor(advisor_id)
        if advisor is None:
            print(f"No se encontró asesor con ID {advisor_id}.")
            return

        password = getpass.getpass("Contraseña: ")
        if (
            self._authenticate_advisor is None
            or not self._authenticate_advisor(advisor_id, password)
        ):
            print("No se pudo iniciar sesión. Verifique la contraseña y la conexión.")
            return

        while True:
            print(f"\nMenú de Asesor: {advisor.get('nombre', advisor_id)}")
            print("1. Mi perfil")
            print("2. Clientes")
            print("3. Mis propiedades asignadas")
            print("4. Cambiar mi contraseña")
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
            elif choice == "4":
                self._change_advisor_password(advisor_id)
            else:
                print("Opción inválida. Intente de nuevo.")

    def _change_advisor_password(self, advisor_id):
        new_password = getpass.getpass("Nueva contraseña: ")
        confirmation = getpass.getpass("Confirme la nueva contraseña: ")
        if not new_password or not new_password.isprintable():
            print("La contraseña debe contener caracteres imprimibles.")
            return
        if new_password != confirmation:
            print("Las contraseñas no coinciden.")
            return
        self._operations.change_advisor_password(advisor_id, new_password)
        print("Contraseña actualizada correctamente.")

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
