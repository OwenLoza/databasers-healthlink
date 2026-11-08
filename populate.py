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
# 3. Crear las colecciones e índices definidos en Mongo/pacientes.js y
#    Mongo/consultas.js:
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

# -------------------
"""
DGRAPH
"""
