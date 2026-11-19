-- HealthLink: tablas de Cassandra (keyspace healthlink).
-- Cada tabla responde a un requerimiento y se consulta leyendo una sola partición.
-- Se enlaza con MongoDB y Dgraph por curp (paciente) y cedula_profesional (doctor).
-- Los uuid (lectura_id, alerta_id, llegada_id) evitan que dos filas con el mismo ts
-- se sobrescriban, porque en Cassandra un INSERT con la misma llave reemplaza la fila.

-- RF-C01 y RF-C02: lecturas de un paciente en un día, la más reciente primero.
CREATE TABLE IF NOT EXISTS signos_por_paciente (
    curp           TEXT,
    fecha          DATE,
    ts             TIMESTAMP,
    lectura_id     UUID,
    tipo           TEXT,
    valor          DOUBLE,
    dispositivo_id TEXT,
    PRIMARY KEY ((curp, fecha), ts, lectura_id)
) WITH CLUSTERING ORDER BY (ts DESC, lectura_id ASC);

-- RF-C01 y RF-C07: la misma lectura, separada por tipo para no usar ALLOW FILTERING.
CREATE TABLE IF NOT EXISTS signos_por_tipo (
    curp       TEXT,
    tipo       TEXT,
    fecha      DATE,
    ts         TIMESTAMP,
    lectura_id UUID,
    valor      DOUBLE,
    PRIMARY KEY ((curp, tipo, fecha), ts, lectura_id)
) WITH CLUSTERING ORDER BY (ts DESC, lectura_id ASC);

-- RF-C03: bitácora de alertas de un paciente (solo se inserta, nunca se actualiza).
CREATE TABLE IF NOT EXISTS alertas_por_paciente (
    curp      TEXT,
    fecha     DATE,
    ts        TIMESTAMP,
    alerta_id UUID,
    alerta    TEXT,
    severidad INT,
    area      TEXT,
    PRIMARY KEY ((curp, fecha), ts, alerta_id)
) WITH CLUSTERING ORDER BY (ts DESC, alerta_id ASC);

-- RF-C03 y RF-C04: tablero de alertas de un área, severidad 1 (crítica) primero.
CREATE TABLE IF NOT EXISTS alertas_por_area (
    area      TEXT,
    fecha     DATE,
    severidad INT,
    ts        TIMESTAMP,
    alerta_id UUID,
    curp      TEXT,
    alerta    TEXT,
    PRIMARY KEY ((area, fecha), severidad, ts, alerta_id)
) WITH CLUSTERING ORDER BY (severidad ASC, ts DESC, alerta_id ASC);

-- RF-C05: fila de espera de un doctor en un día, por orden de llegada.
-- nombre_paciente se copia de MongoDB para mostrar la fila sin consultar otra base.
CREATE TABLE IF NOT EXISTS llegadas_por_doctor (
    cedula_profesional TEXT,
    fecha              DATE,
    hora_llegada       TIMESTAMP,
    llegada_id         UUID,
    curp               TEXT,
    nombre_paciente    TEXT,
    PRIMARY KEY ((cedula_profesional, fecha), hora_llegada, llegada_id)
) WITH CLUSTERING ORDER BY (hora_llegada ASC, llegada_id ASC);

-- RF-C06: historial de batería de un dispositivo, el nivel más reciente primero.
CREATE TABLE IF NOT EXISTS bateria_dispositivos (
    dispositivo_id TEXT,
    fecha          DATE,
    ts             TIMESTAMP,
    nivel_bateria  INT,
    PRIMARY KEY ((dispositivo_id, fecha), ts)
) WITH CLUSTERING ORDER BY (ts DESC);
