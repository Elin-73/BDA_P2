import os
from pathlib import Path

from dotenv import load_dotenv

from controllers import MemgraphController
from menu import ConsoleMenu


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta la variable de entorno requerida '{name}'.")
    return value


def main() -> None:
    load_dotenv(Path(__file__).with_name(".env"))

    try:
        from gqlalchemy import Memgraph
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

    connection = Memgraph(
        required_env("MEMGRAPH_HOST"),
        port,
        required_env("MEMGRAPH_USERNAME"),
        required_env("MEMGRAPH_PASSWORD"),
        encrypted=True,
    )
    print("Conexión a Memgraph configurada.")
    ConsoleMenu(MemgraphController(connection)).run()


if __name__ == "__main__":
    main()