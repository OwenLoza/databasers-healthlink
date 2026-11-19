"""HealthLink: módulo de Telemetría IoT (Cassandra). RF-C01 a RF-C07.

Tablas en esquema.cql. Cada consulta lee una sola partición (sin ALLOW FILTERING).
Se enlaza con MongoDB y Dgraph por curp (paciente) y cedula_profesional (doctor).
"""

import uuid
from datetime import date, datetime

from connect import conectar_cassandra
from Mongo.expedientes import db as mongo

session = conectar_cassandra()

TIPOS = ["frecuencia_cardiaca", "temperatura", "oxigenacion"]
AREAS = ["Urgencias", "Piso 3", "Terapia intensiva"]
SEVERIDADES = {1: "crítica", 2: "alta", 3: "moderada"}


# -------------------
"""
ESCRITURAS (las usan el menú y populate.py)
"""

def guardar_lectura(curp, tipo, valor, dispositivo_id, ts):
    """RF-C01: guarda la lectura en sus dos tablas con un BATCH (se guardan las dos o ninguna)."""
    lectura_id = uuid.uuid4()
    fecha = ts.date()

    stmt = session.prepare("""
        BEGIN BATCH
            INSERT INTO signos_por_paciente (curp, fecha, ts, lectura_id, tipo, valor, dispositivo_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            INSERT INTO signos_por_tipo (curp, tipo, fecha, ts, lectura_id, valor)
            VALUES (?, ?, ?, ?, ?, ?);
        APPLY BATCH
    """)
    session.execute(stmt, (curp, fecha, ts, lectura_id, tipo, valor, dispositivo_id,
                           curp, tipo, fecha, ts, lectura_id, valor))


def guardar_alerta(curp, alerta, severidad, area, ts):
    """RF-C03: guarda la alerta en la bitácora del paciente y en el tablero del área (BATCH).
    Solo se inserta: no hay funciones para actualizar ni borrar alertas."""
    alerta_id = uuid.uuid4()
    fecha = ts.date()

    stmt = session.prepare("""
        BEGIN BATCH
            INSERT INTO alertas_por_paciente (curp, fecha, ts, alerta_id, alerta, severidad, area)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            INSERT INTO alertas_por_area (area, fecha, severidad, ts, alerta_id, curp, alerta)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        APPLY BATCH
    """)
    session.execute(stmt, (curp, fecha, ts, alerta_id, alerta, severidad, area,
                           area, fecha, severidad, ts, alerta_id, curp, alerta))


def guardar_llegada(cedula, curp, nombre_paciente, hora_llegada):
    """RF-C05: agrega al paciente a la fila de espera del doctor en ese día (una sola tabla, sin BATCH)."""
    stmt = session.prepare("""
        INSERT INTO llegadas_por_doctor (cedula_profesional, fecha, hora_llegada, llegada_id, curp, nombre_paciente)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    session.execute(stmt, (cedula, hora_llegada.date(), hora_llegada, uuid.uuid4(), curp, nombre_paciente))


def guardar_bateria(dispositivo_id, nivel, ts):
    """RF-C06: guarda el nivel de batería que reporta un dispositivo (una sola tabla, sin BATCH).
    No lleva uuid: un dispositivo no manda dos niveles en el mismo instante."""
    stmt = session.prepare("""
        INSERT INTO bateria_dispositivos (dispositivo_id, fecha, ts, nivel_bateria)
        VALUES (?, ?, ?, ?)
    """)
    session.execute(stmt, (dispositivo_id, ts.date(), ts, nivel))


# -------------------
"""
AUXILIARES
"""

def pedir_fecha(texto="Fecha (AAAA-MM-DD, Enter = hoy): "):
    valor = input(texto).strip()
    if valor == "":
        return date.today()
    return datetime.strptime(valor, "%Y-%m-%d").date()


def elegir(texto, opciones):
    """Muestra una lista numerada y regresa la opción elegida."""
    numero = 1
    for opcion in opciones:
        print(f"  {numero}. {opcion}")
        numero += 1
    numero = int(input(texto))
    if numero < 1 or numero > len(opciones):
        raise ValueError("opción fuera de la lista")
    return opciones[numero - 1]


# -------------------
"""
REQUERIMIENTOS
"""

def c01_registrar_lectura():
    """RF-C01: registrar lectura de signos vitales enviada por un dispositivo."""
    print("\n--- REGISTRAR LECTURA ---")
    curp = input("CURP del paciente: ").strip().upper()
    dispositivo_id = input("Id del dispositivo (ej. pulsera_01): ").strip()
    tipo = elegir("Tipo de signo: ", TIPOS)
    valor = float(input("Valor: "))

    guardar_lectura(curp, tipo, valor, dispositivo_id, datetime.now())
    print("\nLectura registrada.")


def c02_lecturas_recientes():
    """RF-C02: últimas 50 lecturas del día de un paciente (ya vienen ordenadas por ts DESC)."""
    print("\n--- LECTURAS RECIENTES ---")
    curp = input("CURP del paciente: ").strip().upper()
    fecha = pedir_fecha()

    stmt = session.prepare("""
        SELECT ts, tipo, valor, dispositivo_id
        FROM signos_por_paciente
        WHERE curp = ? AND fecha = ?
        LIMIT 50
    """)
    rows = list(session.execute(stmt, (curp, fecha)))

    print(f"\n{len(rows)} lecturas de {curp} el {fecha}:")
    for row in rows:
        print(f"  {row.ts:%H:%M:%S} | {row.tipo} | {row.valor} | {row.dispositivo_id}")


def c03_registrar_alerta():
    """RF-C03: registrar alerta biométrica y mostrar la bitácora del día del paciente."""
    print("\n--- REGISTRAR ALERTA ---")
    curp = input("CURP del paciente: ").strip().upper()
    alerta = input("Descripción de la alerta: ").strip()
    severidad = int(input("Severidad (1 = crítica, 2 = alta, 3 = moderada): "))
    if severidad not in SEVERIDADES:
        print("La severidad debe ser 1, 2 o 3.")
        return
    area = elegir("Área: ", AREAS)

    ahora = datetime.now()
    guardar_alerta(curp, alerta, severidad, area, ahora)
    print("\nAlerta registrada.")

    stmt = session.prepare("""
        SELECT ts, severidad, area, alerta
        FROM alertas_por_paciente
        WHERE curp = ? AND fecha = ?
    """)
    print(f"\nBitácora de alertas de hoy ({curp}):")
    for row in session.execute(stmt, (curp, ahora.date())):
        print(f"  {row.ts:%H:%M:%S} | [{SEVERIDADES[row.severidad]}] | {row.area} | {row.alerta}")


def c04_alertas_por_area():
    """RF-C04: tablero de alertas del día de un área, las más graves primero."""
    print("\n--- ALERTAS POR ÁREA ---")
    area = elegir("Área: ", AREAS)
    fecha = pedir_fecha()

    stmt = session.prepare("""
        SELECT severidad, ts, curp, alerta
        FROM alertas_por_area
        WHERE area = ? AND fecha = ?
    """)
    rows = list(session.execute(stmt, (area, fecha)))

    print(f"\n{len(rows)} alertas en {area} el {fecha}:")
    for row in rows:
        print(f"  [{SEVERIDADES[row.severidad]}] {row.ts:%H:%M:%S} | {row.curp} | {row.alerta}")


def c05_registrar_llegada():
    """RF-C05: registrar llegada a la sala de espera y mostrar la fila del día del doctor.
    La cédula y la CURP se validan en MongoDB; el nombre del paciente se copia de ahí."""
    print("\n--- REGISTRAR LLEGADA ---")
    cedula = input("Cédula profesional del doctor: ").strip()
    doctor = mongo.doctores.find_one({"cedula_profesional": cedula})
    if doctor is None:
        print("No existe un doctor con esa cédula.")
        return

    curp = input("CURP del paciente: ").strip().upper()
    paciente = mongo.pacientes.find_one({"curp": curp})
    if paciente is None:
        print("No existe un paciente con esa CURP.")
        return

    nombre_paciente = f"{paciente['nombre']} {paciente['apellidos']}"
    ahora = datetime.now()
    guardar_llegada(cedula, curp, nombre_paciente, ahora)
    print(f"\nLlegada de {nombre_paciente} registrada.")

    stmt = session.prepare("""
        SELECT hora_llegada, curp, nombre_paciente
        FROM llegadas_por_doctor
        WHERE cedula_profesional = ? AND fecha = ?
    """)
    print(f"\nSala de espera de hoy - {doctor['nombre']} {doctor['apellidos']}:")
    turno = 1
    for row in session.execute(stmt, (cedula, ahora.date())):
        print(f"  {turno}. {row.hora_llegada:%H:%M} | {row.curp} | {row.nombre_paciente}")
        turno += 1


def c06_historial_bateria():
    """RF-C06: historial de batería del día de un dispositivo, el nivel más reciente primero."""
    print("\n--- HISTORIAL DE BATERÍA ---")
    dispositivo_id = input("Id del dispositivo (ej. pulsera_01): ").strip()
    fecha = pedir_fecha()

    stmt = session.prepare("""
        SELECT ts, nivel_bateria
        FROM bateria_dispositivos
        WHERE dispositivo_id = ? AND fecha = ?
    """)
    rows = list(session.execute(stmt, (dispositivo_id, fecha)))

    print(f"\n{len(rows)} reportes de batería de {dispositivo_id} el {fecha}:")
    for row in rows:
        print(f"  {row.ts:%H:%M:%S} | {row.nivel_bateria}%")


def c07_historial_temperatura():
    """RF-C07: historial de temperatura del día de un paciente (partición curp + tipo + fecha)."""
    print("\n--- HISTORIAL DE TEMPERATURA ---")
    curp = input("CURP del paciente: ").strip().upper()
    fecha = pedir_fecha()

    stmt = session.prepare("""
        SELECT ts, valor
        FROM signos_por_tipo
        WHERE curp = ? AND tipo = 'temperatura' AND fecha = ?
    """)
    rows = list(session.execute(stmt, (curp, fecha)))

    print(f"\n{len(rows)} lecturas de temperatura de {curp} el {fecha}:")
    for row in rows:
        print(f"  {row.ts:%H:%M:%S} | {row.valor} °C")
