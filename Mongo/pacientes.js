// Colección: pacientes
// Un documento por paciente. El contacto de emergencia y las alergias van
// embebidos porque son pocos datos, se leen siempre junto con el perfil
// y no crecen sin límite.
// Requerimientos: RF-M01, RF-M03, RF-M06
// Ejecutar en mongosh:  use healthlink  y después  load("Mongo/pacientes.js")

db.createCollection("pacientes")

// Documento de ejemplo (RF-M01: se guarda todo en una sola operación)
db.pacientes.insertOne({
  _id: "pac_0001",                       // paciente_id (mismo id en Dgraph y Cassandra)
  curp: "LOGA900215HJCPRN04",
  nombre: "Ana",
  apellidos: "López García",
  fecha_nacimiento: ISODate("1990-02-15T00:00:00Z"),
  sexo: "F",
  tipo_sangre: "O+",
  telefono: "3311223344",
  email: "ana.lopez@mail.com",
  direccion: {
    calle: "Av. Vallarta 1500",
    ciudad: "Guadalajara",
    estado: "Jalisco",
    cp: "44100"
  },
  contacto_emergencia: {
    nombre: "Luis López",
    parentesco: "Hermano",
    telefono: "3399887766"
  },
  alergias: [
    { sustancia: "Penicilina", severidad: "alta", reaccion: "Anafilaxia" },
    { sustancia: "Polen", severidad: "baja", reaccion: "Rinitis" }
  ],
  fecha_registro: ISODate("2026-11-01T10:30:00Z")
})

// Índices

// RF-M01: no puede haber dos pacientes con la misma CURP.
db.pacientes.createIndex({ curp: 1 }, { unique: true })

// RF-M06: pacientes con alergia severa a una sustancia ($elemMatch).
// Índice compuesto multikey sobre el arreglo alergias.
db.pacientes.createIndex({ "alergias.sustancia": 1, "alergias.severidad": 1 })
