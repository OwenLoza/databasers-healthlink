"""HealthLink: módulo de Relaciones Clínicas (Dgraph). RF-D01 a RF-D07.

Cada nodo usa su propio uid de Dgraph. Paciente y Doctor se enlazan con
MongoDB por curp y cedula_profesional: MongoDB es la fuente del perfil y
Dgraph solo guarda lo necesario para recorrer relaciones (nombre y la llave).
Si un paciente o doctor todavía no tiene nodo, se crea con los datos de MongoDB.
"""

import json
from datetime import datetime, timedelta

from connect import conectar_dgraph
from Mongo.expedientes import db as mongo

client_stub, client = conectar_dgraph()


# -------------------
"""
AUXILIARES
"""

def consultar(query, variables=None):
    """Consulta de solo lectura. Regresa el resultado como diccionario."""
    res = client.txn(read_only=True).query(query, variables=variables)
    return json.loads(res.json)


def mutar(datos):
    """Guarda un nodo (o lista de nodos) en una transacción. Regresa los uids nuevos."""
    txn = client.txn()
    try:
        res = txn.mutate(set_obj=datos)
        txn.commit()
        return res.uids
    finally:
        txn.discard()


def obtener_o_crear(llave, valor, nodo):
    """Regresa el uid del nodo con llave = valor; si no existe lo crea con los datos de `nodo`.

    La consulta y la mutación van en la misma transacción: como la llave tiene
    @upsert, si dos escrituras intentan crear el mismo nodo a la vez una falla
    y no quedan nodos duplicados.
    """
    query = f"query q($valor: string) {{ nodo(func: eq({llave}, $valor)) {{ uid }} }}"
    txn = client.txn()
    try:
        res = json.loads(txn.query(query, variables={"$valor": valor}).json)
        if res["nodo"]:
            return res["nodo"][0]["uid"]
        uids = txn.mutate(set_obj={"uid": "_:nuevo", **nodo}).uids
        txn.commit()
        return uids["nuevo"]
    finally:
        txn.discard()


def uid_paciente(curp):
    """Enlace con MongoDB por CURP: regresa el uid del Paciente en el grafo."""
    paciente = mongo.pacientes.find_one({"curp": curp})
    if not paciente:
        print("No existe un paciente con esa CURP en MongoDB.")
        return None
    return obtener_o_crear("curp", curp, {
        "dgraph.type": "Paciente",
        "curp": curp,
        "nombre": f"{paciente['nombre']} {paciente['apellidos']}",
    })


def uid_doctor(cedula):
    """Enlace con MongoDB por cédula profesional: regresa el uid del Doctor en el grafo."""
    doctor = mongo.doctores.find_one({"cedula_profesional": cedula})
    if not doctor:
        print("No existe un médico con esa cédula en MongoDB.")
        return None
    return obtener_o_crear("cedula_profesional", cedula, {
        "dgraph.type": "Doctor",
        "cedula_profesional": cedula,
        "nombre": f"{doctor['nombre']} {doctor['apellidos']}",
        "especialidad": doctor["especialidad"],
    })


def buscar_medicamento(nombre):
    """Busca un Medicamento por nombre con el índice term. Regresa {uid, nombre} o None."""
    query = """
    query q($nombre: string) {
        medicamento(func: allofterms(nombre, $nombre)) @filter(type(Medicamento)) {
            uid
            nombre
        }
    }
    """
    res = consultar(query, {"$nombre": nombre})["medicamento"]
    return res[0] if res else None


def interacciones_con_activos(curp, nombre_medicamento):
    """RF-D04: medicamentos activos del paciente que interactúan con el medicamento nuevo."""
    query = """
    query q($curp: string, $nombre: string) {
        paciente(func: eq(curp, $curp)) {
            tiene_prescripcion @filter(eq(activa, true)) {
                prescribe { uid nombre }
            }
        }
        nuevo(func: allofterms(nombre, $nombre)) @filter(type(Medicamento)) {
            nombre
            interactua_con { uid nombre }
            ~interactua_con { uid nombre }
        }
    }
    """
    res = consultar(query, {"$curp": curp, "$nombre": nombre_medicamento})
    if not res["nuevo"]:
        return []

    # Pasos 1 a 3: los medicamentos que el paciente toma hoy.
    activos = set()
    for paciente in res["paciente"]:
        for receta in paciente.get("tiene_prescripcion", []):
            if "prescribe" in receta:
                activos.add(receta["prescribe"]["uid"])

    # Paso 4: interacciones del medicamento nuevo en ambos sentidos.
    nuevo = res["nuevo"][0]
    vecinos = nuevo.get("interactua_con", []) + nuevo.get("~interactua_con", [])

    # Paso 5: los que coinciden son los que hay que advertir.
    return [m["nombre"] for m in vecinos if m["uid"] in activos]


# -------------------
"""
REQUERIMIENTOS
"""

def d01_registrar_medicamento():
    """RF-D01: registrar medicamento en el catálogo (y sus interacciones conocidas)."""
    print("\n--- REGISTRAR MEDICAMENTO ---")
    nombre = input("Nombre: ").strip()
    if buscar_medicamento(nombre):
        print("Ese medicamento ya está en el catálogo.")
        return

    medicamento = {
        "uid": "_:med",
        "dgraph.type": "Medicamento",
        "nombre": nombre,
        "principio_activo": input("Principio activo: ").strip(),
        "interactua_con": [],
    }
    texto = input("Interactúa con (nombres separados por coma, Enter si ninguno): ")
    for otro in [n.strip() for n in texto.split(",") if n.strip()]:
        encontrado = buscar_medicamento(otro)
        if encontrado:
            medicamento["interactua_con"].append({"uid": encontrado["uid"]})
        else:
            print(f"  {otro} no está en el catálogo, se omite.")

    uids = mutar(medicamento)
    print("\nMedicamento registrado. uid:", uids["med"])


def d02_asignar_doctor():
    """RF-D02: asignar doctor tratante a un paciente (arista atendido_por)."""
    print("\n--- ASIGNAR DOCTOR TRATANTE ---")
    paciente = uid_paciente(input("CURP del paciente: ").strip().upper())
    doctor = uid_doctor(input("Cédula del médico: ").strip())
    if not paciente or not doctor:
        return

    mutar({"uid": paciente, "atendido_por": [{"uid": doctor}]})
    print("\nDoctor asignado.")


def d03_registrar_prescripcion():
    """RF-D03: registrar prescripción (nodo Prescripcion y sus aristas en una transacción)."""
    print("\n--- REGISTRAR PRESCRIPCIÓN ---")
    curp = input("CURP del paciente: ").strip().upper()
    paciente = uid_paciente(curp)
    doctor = uid_doctor(input("Cédula del médico que receta: ").strip())
    if not paciente or not doctor:
        return

    medicamento = buscar_medicamento(input("Medicamento: ").strip())
    if not medicamento:
        print("Ese medicamento no está en el catálogo.")
        return

    # RF-D04: se revisa la interacción antes de guardar la receta.
    conflictos = interacciones_con_activos(curp, medicamento["nombre"])
    if conflictos:
        print(f"\n¡ALERTA! {medicamento['nombre']} interactúa con: {', '.join(conflictos)}")
        if input("¿Recetar de todos modos? (s/n): ").strip().lower() != "s":
            print("Prescripción cancelada.")
            return

    dosis = input("Dosis (ej. 5 mg cada 24 h): ").strip()
    dias = int(input("Días de tratamiento: "))
    inicio = datetime.now()
    fin = inicio + timedelta(days=dias)

    # El nodo Prescripcion se crea anidado dentro del paciente: una sola mutación
    # crea el nodo y sus tres aristas (tiene_prescripcion, prescribe, prescrita_por).
    mutar({
        "uid": paciente,
        "tiene_prescripcion": [{
            "uid": "_:receta",
            "dgraph.type": "Prescripcion",
            "dosis": dosis,
            "fecha_inicio": inicio.isoformat(timespec="seconds"),
            "fecha_final": fin.isoformat(timespec="seconds"),
            "activa": True,
            "prescribe": {"uid": medicamento["uid"]},
            "prescrita_por": {"uid": doctor},
        }],
    })
    print(f"\nPrescripción registrada: {medicamento['nombre']} {dosis} hasta {fin:%Y-%m-%d}.")


def d04_revisar_interaccion():
    """RF-D04: advertir si un medicamento interactúa con la medicación activa del paciente."""
    print("\n--- REVISAR INTERACCIÓN ---")
    curp = input("CURP del paciente: ").strip().upper()
    medicamento = buscar_medicamento(input("Medicamento a recetar: ").strip())
    if not medicamento:
        print("Ese medicamento no está en el catálogo.")
        return

    conflictos = interacciones_con_activos(curp, medicamento["nombre"])
    if conflictos:
        print(f"\n¡ALERTA! {medicamento['nombre']} interactúa con: {', '.join(conflictos)}")
    else:
        print("\nSin interacciones con la medicación activa del paciente.")


def d05_red_medica_paciente():
    """RF-D05: doctores que atienden a un paciente."""
    print("\n--- RED MÉDICA DEL PACIENTE ---")
    query = """
    query q($curp: string) {
        paciente(func: eq(curp, $curp)) {
            nombre
            atendido_por {
                nombre
                especialidad
                cedula_profesional
            }
        }
    }
    """
    res = consultar(query, {"$curp": input("CURP del paciente: ").strip().upper()})["paciente"]
    if not res:
        print("Ese paciente no está en el grafo.")
        return

    print(f"\nDoctores de {res[0]['nombre']}:")
    for d in res[0].get("atendido_por", []):
        print(f"  {d['nombre']} | {d['especialidad']} | Cédula: {d['cedula_profesional']}")


def d06_pacientes_de_doctor():
    """RF-D06: pacientes asignados a un doctor (atendido_por en reversa)."""
    print("\n--- PACIENTES DE UN DOCTOR ---")
    query = """
    query q($cedula: string) {
        doctor(func: eq(cedula_profesional, $cedula)) {
            nombre
            especialidad
            ~atendido_por {
                nombre
                curp
            }
        }
    }
    """
    res = consultar(query, {"$cedula": input("Cédula del médico: ").strip()})["doctor"]
    if not res:
        print("Ese médico no está en el grafo.")
        return

    pacientes = res[0].get("~atendido_por", [])
    print(f"\n{res[0]['nombre']} ({res[0]['especialidad']}) atiende a {len(pacientes)} pacientes:")
    for p in pacientes:
        print(f"  {p['nombre']} | CURP: {p['curp']}")


def d07_interacciones_medicamento():
    """RF-D07: medicamentos con los que interactúa un fármaco (en ambos sentidos)."""
    print("\n--- INTERACCIONES DE UN MEDICAMENTO ---")
    query = """
    query q($nombre: string) {
        medicamento(func: allofterms(nombre, $nombre)) @filter(type(Medicamento)) {
            nombre
            principio_activo
            interactua_con { nombre principio_activo }
            ~interactua_con { nombre principio_activo }
        }
    }
    """
    res = consultar(query, {"$nombre": input("Medicamento: ").strip()})["medicamento"]
    if not res:
        print("Ese medicamento no está en el catálogo.")
        return

    m = res[0]
    vecinos = m.get("interactua_con", []) + m.get("~interactua_con", [])
    print(f"\n{m['nombre']} ({m['principio_activo']}) interactúa con {len(vecinos)} medicamentos:")
    for v in vecinos:
        print(f"  {v['nombre']} ({v['principio_activo']})")
