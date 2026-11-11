"""HealthLink: pasos para poblar las bases de datos (solo comentarios por ahora)."""

# -------------------
"""
MONGODB
"""

# 1. Conectarse con conectar_mongo() de connect.py (base "healthlink").
#
# 2. Borrar las colecciones pacientes y consultas si ya existen, para poder
#    correr el script varias veces sin duplicar datos.
#
# 3. Crear las colecciones e índices del modelo de datos (ver reporte):
#      pacientes: { curp: 1 } único
#                 { "alergias.sustancia": 1, "alergias.severidad": 1 }
#      consultas: { paciente_id: 1, fecha: -1 }
#                 { diagnostico: "text", notas: "text" } en español
#                 { doctor_id: 1, fecha: -1 }
#                 { fecha: 1 }
#    Los índices se crean antes de insertar para que la CURP repetida
#    se rechace desde el primer registro.
#
# 4. Generar los datos de prueba con Faker (locale es_MX) y guardarlos en
#    data/pacientes.json y data/consultas.json:
#      - 50 pacientes con _id "pac_0001", "pac_0002", ..., CURP, contacto de
#        emergencia y de 0 a 3 alergias (sustancia y severidad alta/media/baja).
#        Al menos un paciente con alergia alta y otro con alergia baja a la
#        penicilina, para probar RF-M06.
#      - 300 consultas repartidas entre los pacientes y entre los doctores
#        doc_01 ... doc_10, con fechas de septiembre a noviembre de 2026,
#        diagnósticos con su código CIE-10 (E11, I10, G43.0, J06.9, ...) y
#        algunas notas que mencionen "migraña", para probar RF-M04 y RF-M07.
#    Los paciente_id y doctor_id son los mismos que se usarán en Dgraph y
#    Cassandra, así las tres bases quedan enlazadas.
#
# 5. Leer data/pacientes.json e insertarlos con insert_many en pacientes.
#
# 6. Leer data/consultas.json, convertir las fechas de texto a datetime e
#    insertarlas con insert_many en consultas.
#
# 7. Imprimir cuántos documentos quedaron en cada colección con
#    count_documents({}) para confirmar la carga.

# -------------------
"""
CASSANDRA
"""

# ==========================================
# PLAN DE POBLAMIENTO PARA CASSANDRA
# ==========================================
# 1. Crear un script generador (mock) que simule dispositivos IoT enviando telemetría.
# 2. RF-C01 y C07: Iterar sobre una lista de 5 pacientes e insertar cientos de lecturas 
#    de frecuencia cardíaca y temperatura en 'signos_por_paciente' y 'signos_por_tipo'.
# 3. RF-C03 y C04: Insertar un evento simulado de anomalía (ej. ritmo bajo) en 
#    'alertas_por_paciente' y 'alertas_por_area'.
# 4. RF-C05: Insertar manualmente 3 registros en 'llegadas_por_doctor' para simular 
#    la sala de espera.
# 5. RF-C06: Generar un ciclo que inserte "pings" de batería del 100% al 10% en 
#    'bateria_dispositivos'.

# -------------------
"""
DGRAPH
"""

# 1. Conectarse con conectar_dgraph() de connect.py.
#
# 2. Borrar todos los datos y el esquema con client.alter(Operation(drop_all=True)),
#    para poder correr el script varias veces sin duplicar nodos.
#
# 3. Cargar el esquema del modelo de datos
#
# 4. Generar los datos de prueba y guardarlos en data/:
#      - data/doctores.json: doc_01 ... doc_10 con nombre y especialidad (los
#        mismos doctor_id que usa MongoDB).
#      - data/medicamentos.json: unos 30 medicamentos med_001 ... con nombre y
#        principio activo (warfarina, ibuprofeno, paracetamol, metformina, ...).
#      - data/interacciones.json: pares de medicamento_id que interactúan, por
#        ejemplo warfarina-ibuprofeno y warfarina-aspirina, para probar RF-D04
#        y RF-D07.
#
# 5. Insertar en una transacción los nodos Doctor, Medicamento y Paciente
#    (solo id y nombre), usando nodos en blanco (_:doc_01, _:med_001, ...)
#    para poder conectarlos en el mismo paso.
#
# 6. Crear las aristas:
#      - interactua_con entre cada par de data/interacciones.json (una sola vez
#        por par; la reversa permite consultarlo en ambos sentidos).
#      - atendido_por: a cada paciente se le asignan 1 a 3 doctores al azar.
#        El paciente pac_0001 queda con un cardiólogo y un internista (RF-D05).
#      - Prescripcion: 1 a 4 por paciente, con dosis, fecha_inicio y activa, y
#        sus aristas tiene_prescripcion, medicamento y prescrita_por. El paciente
#        pac_0001 toma warfarina, para probar la alerta de RF-D04.
#
# 7. Confirmar la carga contando los nodos de cada tipo con una consulta
#    count(uid) por dgraph.type