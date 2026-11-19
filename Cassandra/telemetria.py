"""HealthLink: módulo de Telemetría IoT (Cassandra). RF-C01 a RF-C07.

En reconstrucción: cada requerimiento se implementa en su propio commit.
Los nombres de las funciones no cambian porque main.py y populate.py los usan.
"""

from connect import conectar_cassandra

session = conectar_cassandra()


def pendiente(requerimiento):
    print(f"\nPendiente: {requerimiento} en reconstrucción.")


# -------------------
"""
REQUERIMIENTOS
"""

def c01_registrar_lectura():
    """RF-C01: registrar lectura de signos vitales enviada por un dispositivo."""
    pendiente("RF-C01")


def c02_lecturas_recientes():
    """RF-C02: últimas 50 lecturas del día de un paciente."""
    pendiente("RF-C02")


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
    """RF-C07: historial de temperatura del día de un paciente."""
    pendiente("RF-C07")
