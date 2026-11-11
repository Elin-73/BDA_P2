import os
from pathlib import Path

from dotenv import load_dotenv

from controllers import MemgraphController
from menu import ConsoleMenu


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta la variable de entorno requerida '{name}'.")
    return value


def main():
    load_dotenv(Path(__file__).with_name(".env"))

    try:
        from gqlalchemy import Memgraph
        from gqlalchemy.exceptions import GQLAlchemyWaitForConnectionError
    except ModuleNotFoundError as exc:
        if exc.name != "gqlalchemy":
            raise
        raise RuntimeError(
            "Falta la dependencia 'gqlalchemy'. Instálala con: "
            "python -m pip install -r requirements.txt"
        ) from exc

    try:
        port = int(required_env("MEMGRAPH_PORT"))
    except ValueError as exc:
        raise RuntimeError("La variable MEMGRAPH_PORT debe ser un entero.") from exc

    host = required_env("MEMGRAPH_HOST")
    connection = Memgraph(
        host,
        port,
        required_env("MEMGRAPH_USERNAME"),
        required_env("MEMGRAPH_PASSWORD"),
        encrypted=True,
    )
    advisor_default_password = required_env("ASESOR_DEFAULT_PASSWORD")

    def authenticate_advisor(identifier, password):
        try:
            Memgraph(
                host,
                port,
                identifier,
                password,
                encrypted=True,
            )
        except GQLAlchemyWaitForConnectionError:
            return False
        return True

    print("Conexión a Memgraph configurada.")
    ConsoleMenu(
        MemgraphController(connection, advisor_default_password),
        boss_password=required_env("BOSS_PASSWORD"),
        authenticate_advisor=authenticate_advisor,
    ).run()


if __name__ == "__main__":
    main()