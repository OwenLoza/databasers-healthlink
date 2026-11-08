# HealthLink | Plataforma de Integración de Datos de Salud

Proyecto final de Bases de Datos No Relacionales (ITESO, Otoño 2026). Equipo **Databasers**.

## Integrantes

| Nombre | Expediente |
|---|---|
| Emilio Maciel Bracamontes | 746522 |
| Owen David Loza Quirarte | 751563 |
| Emiliano Del Toro Alvarez | 758031 |
| Santiago Ayón Sánchez | 757190 |

## Descripción

HealthLink es una aplicación en Python que centraliza la información de un paciente que hoy está dispersa en varios sistemas. Sirve para que el personal médico consulte en un solo lugar el expediente, la medicación y los signos vitales de un paciente, y detecte a tiempo interacciones de medicamentos y alertas. Usa tres bases de datos NoSQL, cada una para el tipo de consulta que mejor resuelve:

- **MongoDB:** expedientes médicos, perfiles de pacientes y consultas.
- **Dgraph:** relaciones entre pacientes, doctores, medicamentos y prescripciones (por ejemplo, interacciones entre fármacos).
- **Cassandra:** lecturas de signos vitales de dispositivos portables, alertas y llegadas a consulta, ordenadas por tiempo.

Las tres bases se enlazan por `paciente_id`.

## Flujo de trabajo

1. **Levantar las bases:** MongoDB, Cassandra y Dgraph corren en contenedores de Docker.
2. **Conectar:** `connect.py` abre la conexión a cada base de datos.
3. **Generar datos:** se crean datos sintéticos (pacientes, doctores, medicamentos y lecturas) con Faker y se guardan en `data/`.
4. **Poblar:** `populate.py` crea los esquemas (colecciones e índices en Mongo, tablas en Cassandra y esquema en Dgraph) e inserta los datos de `data/`.
5. **Consultar:** `main.py` muestra un menú con las consultas de cada base y ejecuta la que elija el usuario.

## Estructura

```
├── Cassandra/     # definición de tablas (CQL)
├── Mongo/         # colecciones e índices
├── Dgraph/        # esquema del grafo
├── data/          # datos de prueba
├── connect.py     # conexiones a las bases
├── populate.py    # pasos para poblar las bases
├── main.py        # menú de consultas
└── README.md
```