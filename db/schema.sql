-- Schema para Base de Datos de RenovaFit
-- Versión 1.0
-- Base de datos para gestión de fichas médicas de pacientes con cirugía bariátrica

-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS renovafit_medical CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE renovafit_medical;

-- --------------------------------------------------------
-- Tabla: profesionales
-- Descripción: Almacena información sobre los profesionales de la salud del centro
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS profesionales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rut VARCHAR(15) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    especialidad VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    imagen_perfil VARCHAR(255),
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso DATETIME,
    activo BOOLEAN DEFAULT TRUE,
    role VARCHAR(30) DEFAULT 'profesional' COMMENT 'Rol del usuario: admin, profesional'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: pacientes
-- Descripción: Almacena información sobre los pacientes
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS pacientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rut VARCHAR(15) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE,
    edad INT,
    sexo VARCHAR(15),
    telefono VARCHAR(20),
    email VARCHAR(150),
    direccion TEXT,
    contacto_emergencia_nombre VARCHAR(200),
    contacto_emergencia_telefono VARCHAR(20),
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME ON UPDATE CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: fichas_medicas
-- Descripción: Almacena las fichas médicas generales de los pacientes
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS fichas_medicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    fecha_ingreso DATE NOT NULL,
    motivo_consulta TEXT NOT NULL,
    profesional_deriva_id INT,
    prevision_salud VARCHAR(100),
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_actualizacion DATETIME ON UPDATE CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'Activa' COMMENT 'Estados: Activa, Archivada, Borrador',
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (profesional_deriva_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: antecedentes_medicos
-- Descripción: Almacena los antecedentes médicos de los pacientes asociados a una ficha
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS antecedentes_medicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    diagnostico_principal VARCHAR(255),
    diagnosticos_secundarios TEXT,
    antecedentes_relevantes TEXT,
    alergias TEXT,
    medicamentos_actuales TEXT,
    tipo_cirugia VARCHAR(50) COMMENT 'Tipos: by_pass, sleeve, balon, otro, ninguna',
    fecha_cirugia DATE,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: evaluaciones_medicas
-- Descripción: Almacena las evaluaciones médicas de los pacientes
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluaciones_medicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_evaluacion DATETIME NOT NULL,
    examen_fisico TEXT,
    indicaciones_medicas TEXT,
    examenes_solicitados TEXT,
    fecha_proxima_evaluacion DATE,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: evaluaciones_enfermeria
-- Descripción: Almacena las evaluaciones de enfermería
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluaciones_enfermeria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_evaluacion DATETIME NOT NULL,
    tension_arterial VARCHAR(20),
    frecuencia_cardiaca VARCHAR(20),
    frecuencia_respiratoria VARCHAR(20),
    temperatura VARCHAR(20),
    saturacion_o2 VARCHAR(20),
    observaciones_generales TEXT,
    cuidado_heridas TEXT,
    medicamentos_administrados TEXT,
    comentarios_adicionales TEXT,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: evaluaciones_kinesicas
-- Descripción: Almacena las evaluaciones kinésicas y de ejercicio
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluaciones_kinesicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_evaluacion DATETIME NOT NULL,
    motivo_atencion TEXT,
    evaluacion_funcional TEXT,
    objetivos_tratamiento TEXT,
    intervenciones_realizadas TEXT,
    evolucion_respuesta TEXT,
    sugerencias_equipo TEXT,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: notas_evolucion
-- Descripción: Almacena notas de evolución de los pacientes
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS notas_evolucion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    observacion TEXT NOT NULL,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: altas_medicas
-- Descripción: Almacena las altas médicas de los pacientes
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS altas_medicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL UNIQUE,
    profesional_id INT NOT NULL,
    fecha_alta DATE NOT NULL,
    motivo_alta TEXT NOT NULL,
    indicaciones_post_alta TEXT,
    derivaciones_sugeridas TEXT,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: archivos_ficha
-- Descripción: Almacena referencias a archivos adjuntos a las fichas
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS archivos_ficha (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(255) NOT NULL,
    tipo_archivo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: citas
-- Descripción: Almacena información sobre las citas programadas
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS citas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    tipo_servicio VARCHAR(50) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Programada' COMMENT 'Estados: Programada, Completada, Cancelada, No Asistió',
    observaciones TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: mediciones_antropometricas
-- Descripción: Almacena las mediciones físicas del paciente
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS mediciones_antropometricas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_medicion DATETIME NOT NULL,
    peso DECIMAL(5,2),
    talla DECIMAL(5,2),
    imc DECIMAL(5,2),
    circunferencia_cintura DECIMAL(5,2),
    circunferencia_cadera DECIMAL(5,2),
    indice_cintura_cadera DECIMAL(5,2),
    porcentaje_grasa DECIMAL(5,2),
    porcentaje_masa_muscular DECIMAL(5,2),
    observaciones TEXT,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: sesiones_entrenamiento
-- Descripción: Almacena información sobre las sesiones de entrenamiento realizadas
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS sesiones_entrenamiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ficha_id INT NOT NULL,
    profesional_id INT NOT NULL,
    fecha_sesion DATETIME NOT NULL,
    tipo_entrenamiento VARCHAR(100),
    descripcion_ejercicios TEXT,
    intensidad VARCHAR(50),
    duracion INT COMMENT 'Duración en minutos',
    respuesta_paciente TEXT,
    observaciones TEXT,
    FOREIGN KEY (ficha_id) REFERENCES fichas_medicas(id),
    FOREIGN KEY (profesional_id) REFERENCES profesionales(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Tabla: agendamientos
-- Descripción: Almacena los agendamientos realizados a través del sitio web
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS agendamientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    edad INT,
    tipo_cirugia VARCHAR(50),
    fecha_cirugia DATE,
    condiciones_medicas TEXT,
    servicio_seleccionado VARCHAR(50) NOT NULL,
    profesional_seleccionado VARCHAR(50) NOT NULL,
    fecha_cita DATE NOT NULL,
    horario_seleccionado TIME NOT NULL,
    comentarios TEXT,
    metodo_pago VARCHAR(50),
    fecha_agendamiento DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'Pendiente' COMMENT 'Estados: Pendiente, Confirmada, Cancelada, Completada'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------
-- Insertar datos iniciales - Profesional administrador
-- --------------------------------------------------------
INSERT INTO profesionales (
    rut, 
    nombre, 
    apellido, 
    email, 
    password_hash, 
    especialidad, 
    telefono, 
    role
) VALUES (
    '12345678-9',
    'Juan',
    'Pérez',
    'juan.perez@renovafit.cl',
    '$2a$12$HXN7ZcqzfLK.VJ8ox9Y8/.uYp6v5xSQoOXcJR11xNKnGVk/6oIf9a', -- Contraseña: password123
    'Kinesiología',
    '+56912345678',
    'admin'
);

-- Crear índices para optimizar búsquedas
CREATE INDEX idx_paciente_nombre_apellido ON pacientes(apellido, nombre);
CREATE INDEX idx_ficha_paciente ON fichas_medicas(paciente_id);
CREATE INDEX idx_ficha_fecha ON fichas_medicas(fecha_ingreso);
CREATE INDEX idx_antecedentes_ficha ON antecedentes_medicos(ficha_id);
CREATE INDEX idx_evaluaciones_medicas_ficha ON evaluaciones_medicas(ficha_id);
CREATE INDEX idx_citas_fecha ON citas(fecha_hora);
CREATE INDEX idx_citas_paciente ON citas(paciente_id);
CREATE INDEX idx_citas_profesional ON citas(profesional_id);