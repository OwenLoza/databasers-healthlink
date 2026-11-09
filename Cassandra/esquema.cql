-- Creación del Keyspace (Base de datos)
CREATE KEYSPACE IF NOT EXISTS healthlink_keyspace 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};

USE healthlink_keyspace;

-- RF-C01 y RF-C02: Historial general de signos por paciente
-- La partición es por paciente y por día para evitar particiones gigantes (hot spots).
CREATE TABLE IF NOT EXISTS signos_por_paciente (
    paciente_id text,
    fecha date,
    ts timestamp,
    tipo text,
    valor float,
    PRIMARY KEY ((paciente_id, fecha), ts, tipo)
) WITH CLUSTERING ORDER BY (ts DESC);

-- RF-C07: Historial filtrado por tipo de signo (ej. temperatura)
-- Duplicamos la información del RF-C01 porque en Cassandra no se usa ALLOW FILTERING.
CREATE TABLE IF NOT EXISTS signos_por_tipo (
    paciente_id text,
    tipo text,
    fecha date,
    ts timestamp,
    valor float,
    PRIMARY KEY ((paciente_id, tipo, fecha), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

-- RF-C03: Bitácora inmutable de alertas por paciente
CREATE TABLE IF NOT EXISTS alertas_por_paciente (
    paciente_id text,
    fecha date,
    ts timestamp,
    alerta text,
    PRIMARY KEY ((paciente_id, fecha), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

-- RF-C04: Tablero de alertas por área, priorizando severidad
-- La clave de clustering ordena primero por severidad ascendente (1=Crítica) y luego por fecha.
CREATE TABLE IF NOT EXISTS alertas_por_area (
    area text,
    fecha date,
    severidad int,
    ts timestamp,
    alerta text,
    PRIMARY KEY ((area, fecha), severidad, ts)
) WITH CLUSTERING ORDER BY (severidad ASC, ts DESC);

-- RF-C05: Registro de llegadas para el flujo de atención
CREATE TABLE IF NOT EXISTS llegadas_por_doctor (
    doctor_id text,
    fecha date,
    hora_llegada timestamp,
    paciente_id text,
    nombre_paciente text,
    PRIMARY KEY ((doctor_id, fecha), hora_llegada, paciente_id)
) WITH CLUSTERING ORDER BY (hora_llegada ASC);

-- RF-C06: Bitácora de batería de dispositivos IoT
CREATE TABLE IF NOT EXISTS bateria_dispositivos (
    dispositivo_id text,
    fecha date,
    ts timestamp,
    nivel_bateria int,
    PRIMARY KEY ((dispositivo_id, fecha), ts)
) WITH CLUSTERING ORDER BY (ts DESC);
