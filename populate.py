"""HealthLink: borra y vuelve a poblar las tres bases con datos de prueba.

Uso:  python populate.py   (con los tres contenedores arriba)

Los catálogos fijos están en data/ (doctores, diagnósticos, medicamentos e
interacciones). Los pacientes se generan con Faker y son los MISMOS en las tres
bases: se enlazan por CURP. Los doctores se enlazan por cédula profesional.
Las lecturas de Cassandra usan la fecha de hoy para que las consultas
"del día" regresen datos.
"""

import json
import random
from datetime import datetime, timedelta

import pydgraph
from faker import Faker

from Cassandra import telemetria
from Dgraph import relaciones
from Mongo import expedientes

fake = Faker("es_MX")
Faker.seed(42)
random.seed(42)

NUM_PACIENTES = 40
NUM_CONSULTAS = 300


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


DOCTORES = leer_json("data/doctores.json")
DIAGNOSTICOS = leer_json("data/diagnosticos.json")
CATALOGO = leer_json("data/medicamentos.json")
MEDICAMENTOS = CATALOGO["medicamentos"]
INTERACCIONES = CATALOGO["interacciones"]

# Paciente fijo para la demo: alergia alta a penicilina, toma warfarina y la atiende la Dra. María Ruiz.
ANA = {
    "curp": "LOGA900215MJCPRN04",
    "nombre": "Ana",
    "apellidos": "López García",
    "fecha_nacimiento": datetime(1990, 2, 15),
    "sexo": "F",
    "tipo_sangre": "O+",
    "telefono": "3311223344",
    "email": "ana.lopez@mail.com",
    "direccion": {"calle": "Av. Vallarta 1500", "ciudad": "Guadalajara", "estado": "Jalisco", "cp": "44100"},
    "contacto_emergencia": {"nombre": "Luis López", "parentesco": "Hermano", "telefono": "3399887766"},
    "alergias": [
        {"sustancia": "Penicilina", "severidad": "alta", "reaccion": "Anafilaxia"},
        {"sustancia": "Polen", "severidad": "baja", "reaccion": "Rinitis"},
    ],
    "fecha_registro": datetime(2026, 9, 1),
}
CEDULA_RUIZ = "12345678"        # Medicina interna
CEDULA_HERNANDEZ = "23456789"   # Cardiología

ALERGIAS = [("Penicilina", "Anafilaxia"), ("Polen", "Rinitis"), ("Sulfas", "Urticaria"),
            ("Látex", "Dermatitis"), ("Mariscos", "Edema"), ("Aspirina", "Broncoespasmo")]

# Motivo y nota de ejemplo por diagnóstico (para que la búsqueda por texto tenga resultados).
MOTIVOS = {
    "G43.0": ("Dolor de cabeza intenso desde hace 3 días", "Paciente refiere migraña con sensibilidad a la luz."),
    "G44.2": ("Dolor de cabeza opresivo", "Cefalea en banda asociada a estrés, sin datos de migraña."),
    "I10": ("Control de presión arterial", "Hipertensión en seguimiento, se ajusta dieta baja en sodio."),
    "I48": ("Palpitaciones", "Ritmo irregular en electrocardiograma, se indica anticoagulación."),
    "E11": ("Control de glucosa", "Diabetes en seguimiento, glucosa en ayuno elevada."),
    "E78.0": ("Resultados de laboratorio", "Colesterol LDL elevado, se recomienda ejercicio."),
    "J06.9": ("Dolor de garganta y fiebre", "Cuadro viral de vías respiratorias, reposo e hidratación."),
    "J45": ("Falta de aire", "Crisis asmática leve, se revisa técnica de inhalador."),
    "K29.7": ("Ardor en el estómago", "Gastritis por consumo de antiinflamatorios."),
    "K21.9": ("Acidez después de comer", "Reflujo, se indica no acostarse después de cenar."),
    "M54.5": ("Dolor de espalda baja", "Lumbalgia mecánica sin irradiación."),
    "N39.0": ("Ardor al orinar", "Infección urinaria no complicada."),
}


# -------------------
"""
DATOS
"""

def generar_pacientes():
    pacientes = [ANA]
    for _ in range(NUM_PACIENTES - 1):
        sexo = random.choice(["F", "M"])
        nacimiento = fake.date_of_birth(minimum_age=1, maximum_age=90)
        pacientes.append({
            "curp": fake.unique.curp(),
            "nombre": fake.first_name_female() if sexo == "F" else fake.first_name_male(),
            "apellidos": f"{fake.last_name()} {fake.last_name()}",
            "fecha_nacimiento": datetime(nacimiento.year, nacimiento.month, nacimiento.day),
            "sexo": sexo,
            "tipo_sangre": random.choice(["O+", "O-", "A+", "A-", "B+", "AB+"]),
            "telefono": f"33{random.randint(10000000, 99999999)}",
            "email": fake.email(),
            "direccion": {
                "calle": fake.street_address(),
                "ciudad": fake.city(),
                "estado": fake.state(),
                "cp": fake.postcode(),
            },
            "contacto_emergencia": {
                "nombre": fake.name(),
                "parentesco": random.choice(["Madre", "Padre", "Hermano", "Hermana", "Pareja", "Hijo"]),
                "telefono": f"33{random.randint(10000000, 99999999)}",
            },
            "alergias": [
                {"sustancia": sustancia, "severidad": random.choice(["alta", "media", "baja"]), "reaccion": reaccion}
                for sustancia, reaccion in random.sample(ALERGIAS, k=random.randint(0, 2))
            ],
            "fecha_registro": datetime(2026, random.randint(8, 10), random.randint(1, 28)),
        })
    return pacientes


def fecha_al_azar(desde, hasta):
    segundos = int((hasta - desde).total_seconds())
    return desde + timedelta(seconds=random.randint(0, segundos))


# -------------------
"""
MONGODB
"""

def poblar_mongo(pacientes):
    db = expedientes.db
    for coleccion in ["pacientes", "consultas", "doctores", "diagnosticos"]:
        db.drop_collection(coleccion)

    # Índices antes de insertar: una CURP o cédula repetida se rechaza desde el primer registro.
    expedientes.crear_indices()

    # insert_many agrega el _id a cada dict; se pasan copias para no tocar las listas originales.
    db.doctores.insert_many([dict(d) for d in DOCTORES])
    db.diagnosticos.insert_many([dict(d) for d in DIAGNOSTICOS])
    db.pacientes.insert_many([dict(p) for p in pacientes])

    # Los _id que generó MongoDB, para referenciarlos desde consultas.
    id_paciente = {p["curp"]: p["_id"] for p in db.pacientes.find({}, {"curp": 1})}
    doctores = list(db.doctores.find())
    ruiz = db.doctores.find_one({"cedula_profesional": CEDULA_RUIZ})
    descripciones = {d["codigo_cie10"]: d["descripcion"] for d in DIAGNOSTICOS}

    consultas = []
    for i in range(NUM_CONSULTAS):
        # Las primeras 3 consultas son de Ana con la Dra. Ruiz (fibrilación auricular → warfarina).
        if i < 3:
            curp, doctor, codigo = ANA["curp"], ruiz, "I48"
        else:
            curp, doctor = random.choice(pacientes)["curp"], random.choice(doctores)
            codigo = random.choice(DIAGNOSTICOS)["codigo_cie10"]
        descripcion = descripciones[codigo]
        motivo, nota = MOTIVOS[codigo]

        consultas.append({
            "paciente_id": id_paciente[curp],
            "doctor_id": doctor["_id"],
            "doctor_nombre": f"{doctor['nombre']} {doctor['apellidos']}",
            "especialidad": doctor["especialidad"],
            "fecha": fecha_al_azar(datetime(2026, 9, 1), datetime.now()),
            "motivo": motivo,
            "diagnostico": descripcion,
            "diagnostico_cie10": codigo,
            "notas": nota,
            "signos": {
                "presion": f"{random.randint(105, 150)}/{random.randint(65, 95)}",
                "temperatura": round(random.uniform(36.0, 38.5), 1),
                "peso_kg": round(random.uniform(45, 110), 1),
            },
            "medicamentos_recetados": [
                {"nombre": m["nombre"], "dosis": random.choice(["5 mg", "50 mg", "500 mg"]),
                 "frecuencia": random.choice(["cada 8 horas", "cada 12 horas", "cada 24 horas"]),
                 "dias": random.choice([5, 7, 14, 30])}
                for m in random.sample(MEDICAMENTOS, k=random.randint(0, 2))
            ],
        })
    db.consultas.insert_many(consultas)

    print("MongoDB:")
    for coleccion in ["pacientes", "consultas", "doctores", "diagnosticos"]:
        print(f"  {coleccion}: {db[coleccion].count_documents({})}")


# -------------------
"""
DGRAPH
"""

def prescripcion(medicamento, cedula, dias_atras, dias_tratamiento):
    """Nodo Prescripcion anidado (con nodos en blanco para el medicamento y el doctor)."""
    inicio = datetime.now() - timedelta(days=dias_atras)
    fin = inicio + timedelta(days=dias_tratamiento)
    return {
        "dgraph.type": "Prescripcion",
        "dosis": random.choice(["5 mg cada 24 h", "50 mg cada 12 h", "500 mg cada 8 h"]),
        "fecha_inicio": inicio.strftime("%Y-%m-%dT%H:%M:%S"),
        "fecha_final": fin.strftime("%Y-%m-%dT%H:%M:%S"),
        "activa": fin > datetime.now(),
        "prescribe": {"uid": "_:med" + str(MEDICAMENTOS.index(medicamento))},
        "prescrita_por": {"uid": "_:doc" + cedula},
    }


def poblar_dgraph(pacientes):
    client = relaciones.client
    client.alter(pydgraph.Operation(drop_all=True))
    with open("Dgraph/esquema.dql", encoding="utf-8") as f:
        client.alter(pydgraph.Operation(schema=f.read()))

    # Nodos en blanco (_:docXXXX, _:medN) para conectar todo en una sola mutación.
    nodos = []
    for d in DOCTORES:
        nodos.append({
            "uid": "_:doc" + d["cedula_profesional"],
            "dgraph.type": "Doctor",
            "cedula_profesional": d["cedula_profesional"],
            "nombre": f"{d['nombre']} {d['apellidos']}",
            "especialidad": d["especialidad"],
        })

    por_nombre = {m["nombre"]: m for m in MEDICAMENTOS}
    for i, m in enumerate(MEDICAMENTOS):
        nodos.append({
            "uid": f"_:med{i}",
            "dgraph.type": "Medicamento",
            "nombre": m["nombre"],
            "principio_activo": m["principio_activo"],
        })
    # Cada interacción se guarda una sola vez; @reverse permite verla desde los dos fármacos.
    for a, b in INTERACCIONES:
        nodos.append({
            "uid": "_:med" + str(MEDICAMENTOS.index(por_nombre[a])),
            "interactua_con": [{"uid": "_:med" + str(MEDICAMENTOS.index(por_nombre[b]))}],
        })

    cedulas = [d["cedula_profesional"] for d in DOCTORES]
    for p in pacientes:
        if p is ANA:
            doctores = [CEDULA_RUIZ, CEDULA_HERNANDEZ]
            recetas = [prescripcion(por_nombre["Warfarina"], CEDULA_RUIZ, 20, 90)]
        else:
            doctores = random.sample(cedulas, k=random.randint(1, 3))
            recetas = [
                prescripcion(m, random.choice(doctores), random.randint(0, 90), random.choice([7, 14, 30, 60, 90]))
                for m in random.sample(MEDICAMENTOS, k=random.randint(0, 3))
            ]
        nodos.append({
            "uid": "_:" + p["curp"],
            "dgraph.type": "Paciente",
            "curp": p["curp"],
            "nombre": f"{p['nombre']} {p['apellidos']}",
            "atendido_por": [{"uid": "_:doc" + c} for c in doctores],
            "tiene_prescripcion": recetas,
        })

    relaciones.mutar(nodos)

    conteo = relaciones.consultar("""
    {
        pacientes(func: type(Paciente)) { total: count(uid) }
        doctores(func: type(Doctor)) { total: count(uid) }
        medicamentos(func: type(Medicamento)) { total: count(uid) }
        prescripciones(func: type(Prescripcion)) { total: count(uid) }
    }
    """)
    print("Dgraph:")
    for tipo, resultado in conteo.items():
        print(f"  {tipo}: {resultado[0]['total']}")


# -------------------
"""
CASSANDRA
"""

TABLAS_CASSANDRA = ["signos_por_paciente", "signos_por_tipo", "alertas_por_paciente",
                    "alertas_por_area", "llegadas_por_doctor", "bateria_dispositivos"]

TEXTOS_ALERTA = ["Frecuencia cardiaca elevada", "Ritmo cardiaco bajo", "Fiebre",
                 "Oxigenación baja", "Presión arterial elevada"]


def crear_tablas_cassandra(session):
    """Ejecuta cada CREATE TABLE de esquema.cql (sin las líneas de comentario)."""
    texto = ""
    with open("Cassandra/esquema.cql", encoding="utf-8") as f:
        for linea in f:
            if not linea.strip().startswith("--"):
                texto += linea

    for sentencia in texto.split(";"):
        if sentencia.strip():
            session.execute(sentencia)


def poblar_cassandra(pacientes):
    session = telemetria.session

    # DROP y no TRUNCATE: así, si cambia el esquema, las tablas se crean con la versión nueva.
    for tabla in TABLAS_CASSANDRA:
        session.execute(f"DROP TABLE IF EXISTS {tabla}")
    crear_tablas_cassandra(session)

    ahora = datetime.now().replace(microsecond=0)
    con_dispositivo = pacientes[:10]   # Ana es la primera, con pulsera_01

    # RF-C01, C02, C07: una lectura de cada tipo cada 20 minutos durante las últimas 8 horas.
    lecturas = 0
    numero = 1
    for p in con_dispositivo:
        dispositivo = f"pulsera_{numero:02d}"
        for k in range(24):
            ts = ahora - timedelta(minutes=20 * k)
            if ts.date() != ahora.date():
                break   # solo lecturas de hoy, para que las consultas "del día" tengan datos
            telemetria.guardar_lectura(p["curp"], "frecuencia_cardiaca", round(random.gauss(78, 12)), dispositivo, ts)
            telemetria.guardar_lectura(p["curp"], "temperatura", round(random.gauss(36.8, 0.5), 1), dispositivo, ts)
            telemetria.guardar_lectura(p["curp"], "oxigenacion", round(random.uniform(92, 99)), dispositivo, ts)
            lecturas += 3
        numero += 1

    # RF-C03, C04: alerta crítica de Ana en Urgencias (para la demo) y 12 alertas al azar, solo de hoy.
    alertas = [(ANA["curp"], "Ritmo cardiaco bajo", 1, "Urgencias", ahora - timedelta(hours=2))]
    for _ in range(12):
        p = random.choice(con_dispositivo)
        alertas.append((p["curp"], random.choice(TEXTOS_ALERTA), random.randint(1, 3),
                        random.choice(telemetria.AREAS), ahora - timedelta(minutes=random.randint(0, 480))))

    total_alertas = 0
    for curp, texto, severidad, area, ts in alertas:
        if ts.date() == ahora.date():
            telemetria.guardar_alerta(curp, texto, severidad, area, ts)
            total_alertas += 1

    print("Cassandra:")
    print(f"  lecturas: {lecturas} (en signos_por_paciente y signos_por_tipo)")
    print(f"  dispositivos: {len(con_dispositivo)} (pulsera_01 a pulsera_{len(con_dispositivo):02d})")
    print(f"  alertas: {total_alertas} (en alertas_por_paciente y alertas_por_area)")


if __name__ == "__main__":
    pacientes = generar_pacientes()
    poblar_mongo(pacientes)
    poblar_dgraph(pacientes)
    poblar_cassandra(pacientes)

    print(f"\nListo. Paciente de prueba: {ANA['nombre']} {ANA['apellidos']} | CURP {ANA['curp']}")
    print(f"Doctora de prueba: María Ruiz Pérez | Cédula {CEDULA_RUIZ}")

    expedientes.db.client.close()
    relaciones.client_stub.close()
    telemetria.session.cluster.shutdown()
