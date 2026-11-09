from importlib import import_module
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

try:
    Memgraph = import_module("gqlalchemy").Memgraph
except ModuleNotFoundError as exc:
    if exc.name != "gqlalchemy":
        raise
    raise RuntimeError(
        "Missing dependency 'gqlalchemy'. Install it with: python -m pip install gqlalchemy"
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


def hello_memgraph(host: str, port: int, username: str, password: str):
    connection = Memgraph(host, port, username, password, encrypted=True)
    results = connection.execute_and_fetch(
        'CREATE (n:Second { message: "Hello Memgraph from Python!" }) RETURN n.message AS message'
    )
    print("Created node with message:", next(results)["message"])


if __name__ == "__main__":
    hello_memgraph(MEMGRAPH_HOST, MEMGRAPH_PORT, MEMGRAPH_USERNAME, MEMGRAPH_PASSWORD)