from importlib import import_module
import os
from pathlib import Path
from dotenv import load_dotenv

from userControllers import create_memgraph, update_memgraph, read_memgraph, delete_memgraph

load_dotenv(Path(__file__).with_name(".env"))

try:
    Memgraph = import_module("gqlalchemy").Memgraph
except ModuleNotFoundError as exc:
    if exc.name != "gqlalchemy":
        raise
    raise RuntimeError(
        "Dependencia faltante 'gqlalchemy'. Instalala con: python -m pip install gqlalchemy"
    ) from exc


def required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable '{name}'.")
    return value


MEMGRAPH_HOST = required_env("MEMGRAPH_HOST")
MEMGRAPH_PORT = int(required_env("MEMGRAPH_PORT"))
MEMGRAPH_USERNAME = required_env("MEMGRAPH_USERNAME")
MEMGRAPH_PASSWORD = required_env("MEMGRAPH_PASSWORD")


def user_menu():
    print("Bienvenid@ al portal en línea de la Inmobiliaria Mendoza!")
    print("Introduzca sus credenciales para entrar.")
    input("Correo:", MEMGRAPH_USERNAME)
    input("Contraseña:", MEMGRAPH_PASSWORD)

    connection = Memgraph(MEMGRAPH_HOST, MEMGRAPH_PORT, MEMGRAPH_USERNAME, MEMGRAPH_PASSWORD, encrypted=True)
    print("\nConexión a Memgraph establecida en {}:{}".format(MEMGRAPH_HOST, MEMGRAPH_PORT))


    print("\nPor favor, eliga una opcion:")
    print("1. Crear un nodo")
    print("2. Actualizar un nodo")
    print("3. Leer nodos actuales")
    print("4. Eliminar un nodo")
    print("5. Salir")

    choice = input("Opcion: ")

    if choice == "1":
        create_memgraph(connection)
    elif choice == "2":
        update_memgraph(connection)
    elif choice == "3":
        read_memgraph(connection)
    elif choice == "4":
        delete_memgraph(connection)
    elif choice == "5":
        exit(0)
    else:
        print("Opción Inválida. Por favor, intente de nuevo.")
        user_menu()

if __name__ == "__main__":

    while True:
        user_menu()