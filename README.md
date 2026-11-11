# CLI de la Inmobiliaria Mendoza

CLI en Python para administrar propiedades, clientes y asesores en Memgraph.

## Requisitos

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Una instancia accesible de Memgraph

En Windows, crea el entorno e instala las dependencias desde PowerShell:

```
uv venv --python 3.14 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

Copia `.env.example` a un nuevo archivo `.env` y configura las credenciales de tu instancia.
`MEMGRAPH_USERNAME` y `MEMGRAPH_PASSWORD` son exclusivamente para conectar con la base de datos.
Configura un `BOSS_PASSWORD` distinto para entrar al menú de jefe/enlistador.
`ASESOR_DEFAULT_PASSWORD` será la contraseña inicial de las nuevas cuentas de asesor; cada asesor puede cambiarla desde su menú.
Después, en CLI de powershell en el cual iniciaste el venv, inicia el programa con:

```
.\.venv\Scripts\python.exe main.py
```

## Estructura

- `main.py`: carga la configuración y conecta las dependencias.
- `menu.py`: presenta el menú y solicita datos al usuario.
- `controllers.py`: ejecuta las operaciones CRUD de Memgraph.

El menú también permite relacionar dos propiedades con su distancia, consultar
propiedades dentro de un radio y mostrar la ruta de distancia total mínima entre
dos propiedades, incluidos los puntos intermedios en caso de que se quiera hacer un recorrido.

Al iniciar sesión, el jefe o enlistador ingresa la contraseña configurada en
`BOSS_PASSWORD`; esta es independiente de `MEMGRAPH_PASSWORD`, que solo se usa
para la conexión a Memgraph. De ser asesor, ingresará su ID y la contraseña de su cuenta.
Las nuevas cuentas de asesor reciben `ASESOR_DEFAULT_PASSWORD`.
Los asesores pueden cambiar su contraseña desde su menú.
El enlistador puede administrar todas las propiedades, los asesores
y los clientes, así asignar propiedades a asesores desde el menú de relaciones.

Los clientes guardan quién los creó. Estos son solo modificados por quién
lo creo o quién le haya sido asignado y el enlistador. Los clientes pueden
tener un asesor responsable y al momento de creación este será
quién haya creado el cliente.
El creador puede asignar o cambiar al asesor responsable desde el menú de clientes.
La relación `RESPONSIBLE_FOR` representa un único asesor responsable por cliente.

Los IDs se generan automáticamente con prefijos por entidad (`p` para
propiedades, `c` para clientes y `a` para asesores), asignados de manera
automática dependiendo del último disponible.
El correo de un asesor se genera como `Nombre@Mendoza.mx`.

Para cargar un ejemplo de asesores, propiedades y clientes con relaciones,
pega el contenido de [seed.cypher] en Memgraph Lab.

Ejecuta las pruebas en tu powershell para confirmar
que esté el entorno correcto con:

```
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```