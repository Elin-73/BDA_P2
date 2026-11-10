# CLI de la Inmobiliaria Mendoza

CLI en Python para administrar propiedades, clientes y asesores en Memgraph.

## Requisitos

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Una instancia accesible de Memgraph

En Windows, crea el entorno e instala las dependencias desde PowerShell:

```powershell
uv venv --python 3.14 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

Copia `.env.example` a `.env` y configura las credenciales de tu instancia.
Después inicia el CLI con:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Estructura

- `main.py`: carga la configuración y conecta las dependencias.
- `menu.py`: presenta el menú y solicita datos al usuario.
- `controllers.py`: ejecuta las operaciones CRUD de Memgraph.

El menú también permite relacionar dos propiedades con su distancia, consultar
propiedades dentro de un radio y mostrar la ruta de distancia total mínima entre
dos propiedades, incluidos los puntos intermedios. Para encontrar una ruta,
primero deben existir las relaciones de distancia necesarias.

Al iniciar sesión, se elige entre asesor y jefe/captador. El asesor se identifica
por su ID y puede editar su perfil, administrar clientes y consultar, crear o
actualizar únicamente las propiedades asignadas; no se agrega autenticación por
contraseña. El jefe/captador puede administrar todas las entidades y asignar
propiedades a asesores desde el menú de relaciones.

El menú depende de una interfaz CRUD y recibe sus operaciones por inyección; así
la interacción y el acceso a datos se pueden cambiar o probar por separado.

Ejecuta las pruebas con:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```