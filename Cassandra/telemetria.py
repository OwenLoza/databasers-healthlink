"""HealthLink: módulo de Telemetría IoT (Cassandra). RF-C01 a RF-C07.

En reconstrucción: cada requerimiento se implementa en su propio commit.
Los nombres de las funciones no cambian porque main.py y populate.py los usan.
"""

import uuid
from datetime import date, datetime

from connect import conectar_cassandra

session = conectar_cassandra()

TIPOS = ["frecuencia_cardiaca", "temperatura", "oxigenacion"]


def pendiente(requerimiento):
    print(f"\nPendiente: {requerimiento} en reconstrucción.")


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
    """RF-C03: registrar alerta biométrica en la bitácora inmutable."""
    pendiente("RF-C03")


def c04_alertas_por_area():
    """RF-C04: tablero de alertas del día de un área, las más graves primero."""
    pendiente("RF-C04")


def c05_registrar_llegada():
    """RF-C05: registrar llegada de un paciente a la sala de espera."""
    pendiente("RF-C05")


def c06_historial_bateria():
    """RF-C06: historial de batería de un dispositivo."""
    pendiente("RF-C06")


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
