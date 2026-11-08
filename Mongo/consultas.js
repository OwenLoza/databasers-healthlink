// Colección: consultas
// Un documento por consulta médica. Va en una colección aparte y referencia
// al paciente con paciente_id, porque las consultas de un paciente crecen
// sin límite y embebidas harían cada vez más grande el documento del paciente.
// Requerimientos: RF-M02, RF-M03, RF-M04, RF-M05, RF-M07
// Ejecutar en mongosh:  use healthlink  y después  load("Mongo/consultas.js")

db.createCollection("consultas")

// Documento de ejemplo (RF-M02)
db.consultas.insertOne({
  _id: "con_0001",
  paciente_id: "pac_0001",              // referencia a pacientes._id
  doctor_id: "doc_07",                  // mismo id que el nodo Doctor en Dgraph
  doctor_nombre: "Dra. María Ruiz",     // copia para mostrar el historial sin otra consulta
  especialidad: "Medicina interna",
  fecha: ISODate("2026-10-15T09:00:00Z"),
  motivo: "Dolor de cabeza intenso desde hace 3 días",
  diagnostico: "Migraña sin aura",
  diagnostico_cie10: "G43.0",
  notas: "Paciente refiere migraña con sensibilidad a la luz. Se indica reposo e hidratación.",
  signos: { presion: "120/80", temperatura: 36.7, peso_kg: 62.5 },
  medicamentos_recetados: [             // copia de solo lectura; la prescripción vigente vive en Dgraph (RF-D03)
    { nombre: "Paracetamol", dosis: "500 mg", frecuencia: "cada 8 horas", dias: 5 }
  ]
})

// Índices

// RF-M02 y RF-M03: historial de un paciente ordenado por fecha.
// También lo usa el $lookup del expediente (foreignField: paciente_id).
db.consultas.createIndex({ paciente_id: 1, fecha: -1 })

// RF-M04: buscar consultas por palabra en el diagnóstico o en las notas.
db.consultas.createIndex(
  { diagnostico: "text", notas: "text" },
  { default_language: "spanish" }
)

// RF-M05: consultas de un médico entre dos fechas.
db.consultas.createIndex({ doctor_id: 1, fecha: -1 })

// RF-M07: el $match del reporte mensual filtra por rango de fechas.
db.consultas.createIndex({ fecha: 1 })
