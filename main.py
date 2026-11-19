"""HealthLink: menú de consultas.

Uso:  python main.py   (con los tres contenedores arriba y después de correr populate.py)
"""

from Cassandra import telemetria as cassandra
from Dgraph import relaciones as dgraph
from Mongo import expedientes as mongo

OPCIONES = {
    "1": ("[Mongo] Registrar paciente", mongo.m01_registrar_paciente),
    "2": ("[Mongo] Registrar consulta", mongo.m02_registrar_consulta),
    "3": ("[Mongo] Expediente completo", mongo.m03_expediente_completo),
    "4": ("[Mongo] Buscar consultas por palabra", mongo.m04_buscar_por_palabra),
    "5": ("[Mongo] Consultas de un médico por periodo", mongo.m05_consultas_por_periodo),
    "6": ("[Mongo] Pacientes con alergia severa", mongo.m06_alergia_severa),
    "7": ("[Mongo] Top 10 diagnósticos del mes", mongo.m07_top_diagnosticos),
    "8": ("[Dgraph] Registrar medicamento", dgraph.d01_registrar_medicamento),
    "9": ("[Dgraph] Asignar doctor tratante", dgraph.d02_asignar_doctor),
    "10": ("[Dgraph] Registrar prescripción", dgraph.d03_registrar_prescripcion),
    "11": ("[Dgraph] Revisar interacción de medicamentos", dgraph.d04_revisar_interaccion),
    "12": ("[Dgraph] Red médica del paciente", dgraph.d05_red_medica_paciente),
    "13": ("[Dgraph] Pacientes de un doctor", dgraph.d06_pacientes_de_doctor),
    "14": ("[Dgraph] Interacciones de un medicamento", dgraph.d07_interacciones_medicamento),
    "15": ("[Cassandra] Registrar lectura de signos", cassandra.c01_registrar_lectura),
    "16": ("[Cassandra] Lecturas recientes del paciente", cassandra.c02_lecturas_recientes),
    "17": ("[Cassandra] Registrar alerta", cassandra.c03_registrar_alerta),
    "18": ("[Cassandra] Alertas por área", cassandra.c04_alertas_por_area),
    "19": ("[Cassandra] Registrar llegada", cassandra.c05_registrar_llegada),
    "20": ("[Cassandra] Historial de batería", cassandra.c06_historial_bateria),
    "21": ("[Cassandra] Historial de temperatura", cassandra.c07_historial_temperatura),
}


def cerrar_conexiones():
    mongo.db.client.close()
    dgraph.client_stub.close()
    cassandra.session.cluster.shutdown()


def menu():
    while True:
        print("\n========== HealthLink ==========")
        for clave, (texto, _) in OPCIONES.items():
            print(f"{clave}. {texto}")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()
        if opcion == "0":
            print("Cerrando conexiones...")
            cerrar_conexiones()
            break
        if opcion not in OPCIONES:
            print("Opción no válida.")
            continue

        try:
            OPCIONES[opcion][1]()
        except ValueError:
            # Fecha, número u opción de lista mal escrita: se regresa al menú.
            print("Dato no válido, intenta de nuevo.")


if __name__ == "__main__":
    menu()
