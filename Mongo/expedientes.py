"""HealthLink: módulo de Expedientes (MongoDB). RF-M01 a RF-M07.

Colecciones: pacientes, consultas, doctores y diagnosticos.
Cada documento usa el _id (ObjectId) de MongoDB. Para enlazar con Dgraph y
Cassandra se usan la CURP del paciente y la cédula profesional del doctor.
"""

from datetime import datetime, timedelta

from connect import conectar_mongo

db = conectar_mongo()


def crear_indices():
    """Crea los índices del modelo de datos. Cada uno responde a un requerimiento."""
    # Igual que en mongosh: 1 = ascendente, -1 = descendente, "text" = índice de texto.
    db.pacientes.create_index([("curp", 1)], unique=True)                              # RF-M01
    db.pacientes.create_index([("alergias.sustancia", 1), ("alergias.severidad", 1)])  # RF-M06
    db.consultas.create_index([("paciente_id", 1), ("fecha", -1)])                     # RF-M02, M03
    db.consultas.create_index([("diagnostico", "text"), ("notas", "text")])            # RF-M04
    db.consultas.create_index([("doctor_id", 1), ("fecha", -1)])                       # RF-M05
    db.consultas.create_index([("fecha", 1)])                                          # RF-M07
    db.doctores.create_index([("cedula_profesional", 1)], unique=True)                 # RF-M02, M05
    db.diagnosticos.create_index([("codigo_cie10", 1)], unique=True)                   # RF-M02, M07


# -------------------
"""
AUXILIARES
"""

def pedir_fecha(texto):
    """Pide una fecha AAAA-MM-DD y la regresa como datetime."""
    return datetime.strptime(input(texto).strip(), "%Y-%m-%d")


def nombre_completo(doc):
    return f"{doc['nombre']} {doc['apellidos']}"


def imprimir_consulta(c):
    print(f"  {c['fecha']:%Y-%m-%d %H:%M} | {c['doctor_nombre']} ({c['especialidad']})")
    print(f"    Motivo: {c['motivo']}")
    print(f"    Diagnóstico: {c['diagnostico']} [{c['diagnostico_cie10']}]")
    print(f"    Notas: {c['notas']}")
    for m in c.get("medicamentos_recetados", []):
        print(f"    Receta: {m['nombre']} {m['dosis']}, {m['frecuencia']}, {m['dias']} días")


# -------------------
"""
REQUERIMIENTOS
"""

def m01_registrar_paciente():
    """RF-M01: registrar paciente con contacto de emergencia y alergias embebidos."""
    print("\n--- REGISTRAR PACIENTE ---")
    curp = input("CURP: ").strip().upper()
    if db.pacientes.find_one({"curp": curp}):
        print("Ya existe un paciente con esa CURP.")
        return

    paciente = {
        "curp": curp,
        "nombre": input("Nombre: ").strip(),
        "apellidos": input("Apellidos: ").strip(),
        "fecha_nacimiento": pedir_fecha("Fecha de nacimiento (AAAA-MM-DD): "),
        "sexo": input("Sexo (F/M): ").strip().upper(),
        "tipo_sangre": input("Tipo de sangre: ").strip().upper(),
        "telefono": input("Teléfono: ").strip(),
        "email": input("Email: ").strip(),
        "direccion": {
            "calle": input("Calle y número: ").strip(),
            "ciudad": input("Ciudad: ").strip(),
            "estado": input("Estado: ").strip(),
            "cp": input("Código postal: ").strip(),
        },
        "contacto_emergencia": {
            "nombre": input("Contacto de emergencia - nombre: ").strip(),
            "parentesco": input("Contacto de emergencia - parentesco: ").strip(),
            "telefono": input("Contacto de emergencia - teléfono: ").strip(),
        },
        "alergias": [],
        "fecha_registro": datetime.now(),
    }

    while input("¿Agregar alergia? (s/n): ").strip().lower() == "s":
        paciente["alergias"].append({
            "sustancia": input("  Sustancia: ").strip().capitalize(),
            "severidad": input("  Severidad (alta/media/baja): ").strip().lower(),
            "reaccion": input("  Reacción: ").strip(),
        })

    resultado = db.pacientes.insert_one(paciente)
    print("\nPaciente registrado. _id:", resultado.inserted_id)


def m02_registrar_consulta():
    """RF-M02: registrar consulta médica en la colección consultas."""
    print("\n--- REGISTRAR CONSULTA ---")
    paciente = db.pacientes.find_one({"curp": input("CURP del paciente: ").strip().upper()})
    if not paciente:
        print("No existe un paciente con esa CURP.")
        return

    doctor = db.doctores.find_one({"cedula_profesional": input("Cédula del médico: ").strip()})
    if not doctor:
        print("No existe un médico con esa cédula.")
        return

    codigo = input("Código CIE-10 del diagnóstico: ").strip().upper()
    catalogo = db.diagnosticos.find_one({"codigo_cie10": codigo})
    if not catalogo:
        print("Ese código no está en el catálogo de diagnósticos.")
        return

    consulta = {
        "paciente_id": paciente["_id"],
        "doctor_id": doctor["_id"],
        "doctor_nombre": nombre_completo(doctor),
        "especialidad": doctor["especialidad"],
        "fecha": datetime.now(),
        "motivo": input("Motivo: ").strip(),
        # Texto libre; si se deja vacío se usa la descripción del catálogo.
        "diagnostico": input(f"Diagnóstico [{catalogo['descripcion']}]: ").strip() or catalogo["descripcion"],
        "diagnostico_cie10": codigo,
        "notas": input("Notas: ").strip(),
        "signos": {
            "presion": input("Presión (ej. 120/80): ").strip(),
            "temperatura": float(input("Temperatura (°C): ")),
            "peso_kg": float(input("Peso (kg): ")),
        },
        "medicamentos_recetados": [],
    }

    while input("¿Agregar medicamento recetado? (s/n): ").strip().lower() == "s":
        consulta["medicamentos_recetados"].append({
            "nombre": input("  Nombre: ").strip(),
            "dosis": input("  Dosis: ").strip(),
            "frecuencia": input("  Frecuencia: ").strip(),
            "dias": int(input("  Días: ")),
        })

    resultado = db.consultas.insert_one(consulta)
    print("\nConsulta registrada. _id:", resultado.inserted_id)
    if consulta["medicamentos_recetados"]:
        print("Recuerda registrar la prescripción vigente en Dgraph (revisa interacciones).")


def m03_expediente_completo():
    """RF-M03: perfil del paciente + sus consultas, de la más reciente a la más antigua."""
    print("\n--- EXPEDIENTE COMPLETO ---")
    curp = input("CURP del paciente: ").strip().upper()
    p = db.pacientes.find_one({"curp": curp})
    if not p:
        print("No existe un paciente con esa CURP.")
        return

    pipeline = [
        {"$match": {"curp": curp}},
        {"$lookup": {
            "from": "consultas",
            "localField": "_id",
            "foreignField": "paciente_id",
            "as": "historial",
        }},
        {"$unwind": "$historial"},
        {"$sort": {"historial.fecha": -1}},
    ]
    resultado = list(db.pacientes.aggregate(pipeline))

    print(f"\n{nombre_completo(p)} | CURP: {p['curp']}")
    print(f"Nacimiento: {p['fecha_nacimiento']:%Y-%m-%d} | Sexo: {p['sexo']} | Sangre: {p['tipo_sangre']}")
    print(f"Teléfono: {p['telefono']} | Email: {p['email']}")
    d = p["direccion"]
    print(f"Dirección: {d['calle']}, {d['ciudad']}, {d['estado']}, {d['cp']}")
    c = p["contacto_emergencia"]
    print(f"Contacto de emergencia: {c['nombre']} ({c['parentesco']}) {c['telefono']}")
    print("Alergias:", ", ".join(f"{a['sustancia']} ({a['severidad']})" for a in p["alergias"]) or "ninguna")

    print(f"\nConsultas ({len(resultado)}):")
    for doc in resultado:
        imprimir_consulta(doc["historial"])


def m04_buscar_por_palabra():
    """RF-M04: buscar consultas por palabra clave en diagnóstico y notas (índice de texto)."""
    print("\n--- BUSCAR CONSULTAS POR PALABRA ---")
    palabra = input("Palabra clave: ").strip()

    consultas = db.consultas.find({"$text": {"$search": palabra}}).sort("fecha", -1).limit(20)

    encontradas = 0
    for consulta in consultas:
        imprimir_consulta(consulta)
        encontradas += 1
    print(f"\n{encontradas} consultas encontradas (máximo 20, las más recientes primero).")


def m05_consultas_por_periodo():
    """RF-M05: consultas atendidas por un médico entre dos fechas (índice doctor_id + fecha)."""
    print("\n--- CONSULTAS DE UN MÉDICO POR PERIODO ---")
    doctor = db.doctores.find_one({"cedula_profesional": input("Cédula del médico: ").strip()})
    if not doctor:
        print("No existe un médico con esa cédula.")
        return
    inicio = pedir_fecha("Desde (AAAA-MM-DD): ")
    fin = pedir_fecha("Hasta (AAAA-MM-DD): ") + timedelta(days=1)  # incluye todo el último día

    consultas = list(db.consultas.find(
        {"doctor_id": doctor["_id"], "fecha": {"$gte": inicio, "$lt": fin}}
    ).sort("fecha", -1))

    print(f"\n{nombre_completo(doctor)} atendió {len(consultas)} consultas:")
    for consulta in consultas:
        imprimir_consulta(consulta)


def m06_alergia_severa():
    """RF-M06: pacientes con alergia de severidad alta a una sustancia ($elemMatch)."""
    print("\n--- PACIENTES CON ALERGIA SEVERA ---")
    sustancia = input("Sustancia: ").strip().capitalize()

    # $elemMatch: la sustancia y la severidad tienen que estar en la MISMA alergia.
    pacientes = db.pacientes.find(
        {"alergias": {"$elemMatch": {"sustancia": sustancia, "severidad": "alta"}}},
        {"curp": 1, "nombre": 1, "apellidos": 1, "telefono": 1, "alergias": 1, "_id": 0},
    )

    total = 0
    for p in pacientes:
        for alergia in p["alergias"]:
            if alergia["sustancia"] == sustancia and alergia["severidad"] == "alta":
                print(f"  {nombre_completo(p)} | CURP: {p['curp']} | Tel: {p['telefono']} | Reacción: {alergia['reaccion']}")
        total += 1
    print(f"\n{total} pacientes con alergia alta a {sustancia}.")


def m07_top_diagnosticos():
    """RF-M07: top 10 diagnósticos de un mes (pipeline de agregación)."""
    print("\n--- TOP 10 DIAGNÓSTICOS DEL MES ---")
    anio = int(input("Año (AAAA): "))
    mes = int(input("Mes (1-12): "))
    inicio = datetime(anio, mes, 1)
    fin = datetime(anio + 1, 1, 1) if mes == 12 else datetime(anio, mes + 1, 1)

    pipeline = [
        {"$match": {"fecha": {"$gte": inicio, "$lt": fin}}},
        {"$group": {"_id": "$diagnostico_cie10", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
        {"$lookup": {
            "from": "diagnosticos",
            "localField": "_id",
            "foreignField": "codigo_cie10",
            "as": "catalogo",
        }},
        {"$unwind": "$catalogo"},
    ]

    print(f"\nDiagnósticos más frecuentes de {mes:02d}/{anio}:")
    lugar = 1
    for d in db.consultas.aggregate(pipeline):
        print(f"  {lugar}. [{d['_id']}] {d['catalogo']['descripcion']}: {d['total']} consultas")
        lugar += 1
