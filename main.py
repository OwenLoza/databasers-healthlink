"""HealthLink: menú de consultas planeadas."""

# -------------------
"""
MONGODB
"""

def m01_registrar_paciente():
    """RF-M01: registrar paciente con contacto de emergencia y alergias embebidos."""
    pass


def m02_registrar_consulta():
    """RF-M02: registrar consulta médica en la colección consultas."""
    pass


def m03_expediente_completo():
    """RF-M03: perfil del paciente + consultas ($lookup, $unwind, $sort)."""
    pass


def m04_buscar_por_palabra():
    """RF-M04: buscar consultas por palabra clave (índice de texto)."""
    pass


def m05_consultas_por_periodo():
    """RF-M05: consultas de un médico entre dos fechas (índice compuesto)."""
    pass


def m06_alergia_severa():
    """RF-M06: pacientes con alergia severa a una sustancia ($elemMatch)."""
    pass


def m07_top_diagnosticos():
    """RF-M07: top 10 diagnósticos del mes (pipeline de agregación)."""
    pass

# -------------------
"""
DGRAPH
"""

def d01_registrar_medicamento():
    """RF-D01: registrar medicamento en el catálogo."""
    pass


def d02_asignar_doctor():
    """RF-D02: asignar doctor tratante (arista atendido_por)."""
    pass


def d03_registrar_prescripcion():
    """RF-D03: registrar prescripción (nodo Prescripcion y sus aristas)."""
    pass


def d04_revisar_interaccion():
    """RF-D04: advertir interacción con la medicación activa."""
    pass


def d05_red_medica_paciente():
    """RF-D05: doctores que atienden a un paciente."""
    pass


def d06_pacientes_de_doctor():
    """RF-D06: pacientes de un doctor (~atendido_por)."""
    pass


def d07_interacciones_medicamento():
    """RF-D07: medicamentos con los que interactúa un fármaco."""
    pass

# -------------------
"""
CASSANDRA 
"""

def c01_registrar_lectura():
    """RF-C01: registrar lectura de signos vitales."""
    pass


def c02_lecturas_recientes():
    """RF-C02: últimas 50 lecturas del día de un paciente."""
    pass


def c03_registrar_alerta():
    """RF-C03: registrar alerta biométrica."""
    pass


def c04_alertas_por_area():
    """RF-C04: alertas del día de un área, más graves primero."""
    pass


def c05_registrar_llegada():
    """RF-C05: registrar llegada de paciente a la sala de espera."""
    pass


def c06_historial_bateria():
    """RF-C06: historial de batería de un dispositivo."""
    pass


def c07_historial_temperatura():
    """RF-C07: historial de temperatura del día de un paciente."""
    pass

# -------------------
"""
MENÚ
"""

OPCIONES = {
    "1": ("[Mongo] Registrar paciente", m01_registrar_paciente),
    "2": ("[Mongo] Registrar consulta", m02_registrar_consulta),
    "3": ("[Mongo] Expediente completo", m03_expediente_completo),
    "4": ("[Mongo] Buscar consultas por palabra", m04_buscar_por_palabra),
    "5": ("[Mongo] Consultas de un médico por periodo", m05_consultas_por_periodo),
    "6": ("[Mongo] Pacientes con alergia severa", m06_alergia_severa),
    "7": ("[Mongo] Top 10 diagnósticos del mes", m07_top_diagnosticos),
    "8": ("[Dgraph] Registrar medicamento", d01_registrar_medicamento),
    "9": ("[Dgraph] Asignar doctor tratante", d02_asignar_doctor),
    "10": ("[Dgraph] Registrar prescripción", d03_registrar_prescripcion),
    "11": ("[Dgraph] Revisar interacción de medicamentos", d04_revisar_interaccion),
    "12": ("[Dgraph] Red médica del paciente", d05_red_medica_paciente),
    "13": ("[Dgraph] Pacientes de un doctor", d06_pacientes_de_doctor),
    "14": ("[Dgraph] Interacciones de un medicamento", d07_interacciones_medicamento),
    "15": ("[Cassandra] Registrar lectura de signos", c01_registrar_lectura),
    "16": ("[Cassandra] Lecturas recientes del paciente", c02_lecturas_recientes),
    "17": ("[Cassandra] Registrar alerta", c03_registrar_alerta),
    "18": ("[Cassandra] Alertas por área", c04_alertas_por_area),
    "19": ("[Cassandra] Registrar llegada", c05_registrar_llegada),
    "20": ("[Cassandra] Historial de batería", c06_historial_bateria),
    "21": ("[Cassandra] Historial de temperatura", c07_historial_temperatura),
}


def menu():
    while True:
        print("\n========== HealthLink ==========")
        for clave, (texto, _) in OPCIONES.items():
            print(f"{clave}. {texto}")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()
        if opcion == "0":
            print("Saliendo...")
            break
        if opcion in OPCIONES:
            OPCIONES[opcion][1]()
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu()