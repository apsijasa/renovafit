import datetime
from flask import current_app
import pymysql
import json
from werkzeug.security import generate_password_hash, check_password_hash

# Configuración de la conexión a la base de datos
def get_db_connection():
    """Establece y retorna una conexión a la base de datos MySQL."""
    conn = pymysql.connect(
        host=current_app.config['DB_HOST'],
        user=current_app.config['DB_USER'],
        password=current_app.config['DB_PASSWORD'],
        db=current_app.config['DB_NAME'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

# Clase base para modelos
class Model:
    """Clase base con métodos comunes para todos los modelos."""
    
    @staticmethod
    def execute_query(query, params=None, fetch=True, commit=False):
        """Ejecuta una consulta SQL con los parámetros proporcionados."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    return cursor.lastrowid if cursor.lastrowid else None
        finally:
            conn.close()
    
    @staticmethod
    def execute_transaction(queries):
        """Ejecuta múltiples consultas en una transacción."""
        conn = get_db_connection()
        try:
            conn.begin()
            with conn.cursor() as cursor:
                results = []
                for query, params in queries:
                    cursor.execute(query, params)
                    results.append(cursor.lastrowid if cursor.lastrowid else None)
            conn.commit()
            return results
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

# Modelo para los profesionales (usuarios del sistema)
class Profesional(Model):
    """Modelo para gestionar los profesionales del sistema (usuarios)."""
    
    @staticmethod
    def get_by_email(email):
        """Obtiene un profesional por su email."""
        query = """
        SELECT * FROM profesionales 
        WHERE email = %s AND activo = 1
        """
        result = Profesional.execute_query(query, (email,))
        return result[0] if result else None
    
    @staticmethod
    def get_all():
        """Obtiene todos los profesionales activos."""
        query = """
        SELECT id, nombre, apellido, especialidad, email, telefono, 
               activo, fecha_registro, ultimo_acceso, imagen_perfil
        FROM profesionales
        WHERE activo = 1
        ORDER BY apellido, nombre
        """
        return Profesional.execute_query(query)
    
    @staticmethod
    def get_by_id(profesional_id):
        """Obtiene un profesional por su ID."""
        query = """
        SELECT id, nombre, apellido, especialidad, email, telefono, 
               activo, fecha_registro, ultimo_acceso, imagen_perfil
        FROM profesionales 
        WHERE id = %s AND activo = 1
        """
        result = Profesional.execute_query(query, (profesional_id,))
        return result[0] if result else None
    
    @staticmethod
    def create(data):
        """Crea un nuevo profesional."""
        query = """
        INSERT INTO profesionales (nombre, apellido, email, password_hash, especialidad, telefono, rol)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        password_hash = generate_password_hash(data['password'])
        params = (
            data['nombre'],
            data['apellido'],
            data['email'],
            password_hash,
            data.get('especialidad'),
            data.get('telefono'),
            data.get('rol', 'profesional')
        )
        return Profesional.execute_query(query, params, fetch=False, commit=True)
    
    @staticmethod
    def update(profesional_id, data):
        """Actualiza los datos de un profesional."""
        params = []
        set_clause = []
        
        if 'nombre' in data:
            set_clause.append("nombre = %s")
            params.append(data['nombre'])
        
        if 'apellido' in data:
            set_clause.append("apellido = %s")
            params.append(data['apellido'])
        
        if 'especialidad' in data:
            set_clause.append("especialidad = %s")
            params.append(data['especialidad'])
        
        if 'telefono' in data:
            set_clause.append("telefono = %s")
            params.append(data['telefono'])
        
        if 'rol' in data:
            set_clause.append("rol = %s")
            params.append(data['rol'])
        
        if 'imagen_perfil' in data:
            set_clause.append("imagen_perfil = %s")
            params.append(data['imagen_perfil'])
        
        if 'password' in data:
            set_clause.append("password_hash = %s")
            params.append(generate_password_hash(data['password']))
        
        if not set_clause:
            return None
        
        query = f"""
        UPDATE profesionales 
        SET {', '.join(set_clause)}
        WHERE id = %s AND activo = 1
        """
        params.append(profesional_id)
        
        return Profesional.execute_query(query, params, fetch=False, commit=True)
    
    @staticmethod
    def delete(profesional_id):
        """Marca un profesional como inactivo (borrado lógico)."""
        query = """
        UPDATE profesionales 
        SET activo = 0
        WHERE id = %s
        """
        return Profesional.execute_query(query, (profesional_id,), fetch=False, commit=True)
    
    @staticmethod
    def verify_password(email, password):
        """Verifica si la contraseña es correcta para el profesional dado."""
        user = Profesional.get_by_email(email)
        if not user:
            return False
        return check_password_hash(user['password_hash'], password)

# Modelo para los pacientes
class Paciente(Model):
    """Modelo para gestionar los pacientes."""
    
    @staticmethod
    def get_all():
        """Obtiene todos los pacientes activos."""
        query = "SELECT * FROM pacientes WHERE activo = 1 ORDER BY apellido, nombre"
        return Paciente.execute_query(query)
    
    @staticmethod
    def get_by_id(paciente_id):
        """Obtiene un paciente por su ID."""
        query = "SELECT * FROM pacientes WHERE id = %s AND activo = 1"
        result = Paciente.execute_query(query, (paciente_id,))
        return result[0] if result else None
    
    @staticmethod
    def search(term):
        """Busca pacientes por nombre, apellido o RUT."""
        query = """
        SELECT * FROM pacientes 
        WHERE activo = 1 
        AND (nombre LIKE %s OR apellido LIKE %s OR rut LIKE %s)
        ORDER BY apellido, nombre
        """
        search_term = f"%{term}%"
        return Paciente.execute_query(query, (search_term, search_term, search_term))
    
    @staticmethod
    def create(data):
        """Crea un nuevo paciente."""
        query = """
        INSERT INTO pacientes (
            rut, nombre, apellido, fecha_nacimiento, edad, sexo, 
            telefono, email, direccion, contacto_emergencia_nombre, 
            contacto_emergencia_telefono
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data.get('rut'),
            data['nombre'],
            data['apellido'],
            data.get('fecha_nacimiento'),
            data.get('edad'),
            data.get('sexo'),
            data.get('telefono'),
            data.get('email'),
            data.get('direccion'),
            data.get('contacto_emergencia_nombre'),
            data.get('contacto_emergencia_telefono')
        )
        return Paciente.execute_query(query, params, fetch=False, commit=True)
    
    @staticmethod
    def update(paciente_id, data):
        """Actualiza los datos de un paciente."""
        query = """
        UPDATE pacientes SET 
            rut = %s, 
            nombre = %s, 
            apellido = %s, 
            fecha_nacimiento = %s, 
            edad = %s, 
            sexo = %s, 
            telefono = %s, 
            email = %s, 
            direccion = %s, 
            contacto_emergencia_nombre = %s, 
            contacto_emergencia_telefono = %s
        WHERE id = %s AND activo = 1
        """
        params = (
            data.get('rut'),
            data.get('nombre'),
            data.get('apellido'),
            data.get('fecha_nacimiento'),
            data.get('edad'),
            data.get('sexo'),
            data.get('telefono'),
            data.get('email'),
            data.get('direccion'),
            data.get('contacto_emergencia_nombre'),
            data.get('contacto_emergencia_telefono'),
            paciente_id
        )
        return Paciente.execute_query(query, params, fetch=False, commit=True)
    
    @staticmethod
    def delete(paciente_id):
        """Marca un paciente como inactivo (borrado lógico)."""
        query = """
        UPDATE pacientes 
        SET activo = 0
        WHERE id = %s
        """
        return Paciente.execute_query(query, (paciente_id,), fetch=False, commit=True)

# Modelo para las fichas médicas
class FichaMedica(Model):
    """Modelo para gestionar las fichas médicas."""
    
    @staticmethod
    def get_all(paciente_id=None):
        """Obtiene todas las fichas médicas con información de pacientes y profesionales."""
        if paciente_id:
            query = """
            SELECT f.*, 
                   p.nombre as paciente_nombre, 
                   p.apellido as paciente_apellido, 
                   prof.nombre as profesional_nombre, 
                   prof.apellido as profesional_apellido,
                   am.diagnostico_principal,
                   am.tipo_cirugia,
                   (SELECT MAX(fecha_evaluacion) FROM evaluaciones_medicas WHERE ficha_id = f.id) as ultimo_control
            FROM fichas_medicas f
            JOIN pacientes p ON f.paciente_id = p.id
            LEFT JOIN profesionales prof ON f.profesional_deriva_id = prof.id
            LEFT JOIN antecedentes_medicos am ON f.id = am.ficha_id
            WHERE f.paciente_id = %s AND f.estado = 'Activa'
            ORDER BY f.fecha_ingreso DESC
            """
            return FichaMedica.execute_query(query, (paciente_id,))
        else:
            query = """
            SELECT f.*, 
                   p.nombre as paciente_nombre, 
                   p.apellido as paciente_apellido, 
                   prof.nombre as profesional_nombre, 
                   prof.apellido as profesional_apellido,
                   am.diagnostico_principal,
                   am.tipo_cirugia,
                   (SELECT MAX(fecha_evaluacion) FROM evaluaciones_medicas WHERE ficha_id = f.id) as ultimo_control
            FROM fichas_medicas f
            JOIN pacientes p ON f.paciente_id = p.id
            LEFT JOIN profesionales prof ON f.profesional_deriva_id = prof.id
            LEFT JOIN antecedentes_medicos am ON f.id = am.ficha_id
            WHERE f.estado = 'Activa'
            ORDER BY f.fecha_ingreso DESC
            """
            return FichaMedica.execute_query(query)
    
    @staticmethod
    def get_by_id(ficha_id):
        """Obtiene una ficha médica por su ID con información detallada."""
        query = """
        SELECT f.*, 
               p.nombre as paciente_nombre, 
               p.apellido as paciente_apellido,
               p.rut as paciente_rut,
               p.fecha_nacimiento as paciente_fecha_nacimiento,
               p.edad as paciente_edad,
               p.sexo as paciente_sexo,
               p.telefono as paciente_telefono,
               p.email as paciente_email,
               p.direccion as paciente_direccion,
               p.contacto_emergencia_nombre as paciente_contacto_emergencia_nombre,
               p.contacto_emergencia_telefono as paciente_contacto_emergencia_telefono,
               prof.nombre as profesional_nombre, 
               prof.apellido as profesional_apellido
        FROM fichas_medicas f
        JOIN pacientes p ON f.paciente_id = p.id
        LEFT JOIN profesionales prof ON f.profesional_deriva_id = prof.id
        WHERE f.id = %s
        """
        result = FichaMedica.execute_query(query, (ficha_id,))
        if not result:
            return None
        
        ficha = result[0]
        
        # Obtener antecedentes médicos
        antecedentes_query = """
        SELECT am.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido
        FROM antecedentes_medicos am
        JOIN profesionales p ON am.profesional_id = p.id
        WHERE am.ficha_id = %s
        ORDER BY am.fecha_registro DESC
        """
        antecedentes = FichaMedica.execute_query(antecedentes_query, (ficha_id,))
        ficha['antecedentes'] = antecedentes
        
        # Obtener evaluaciones médicas
        evaluaciones_medicas_query = """
        SELECT em.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM evaluaciones_medicas em
        JOIN profesionales p ON em.profesional_id = p.id
        WHERE em.ficha_id = %s
        ORDER BY em.fecha_evaluacion DESC
        """
        evaluaciones_medicas = FichaMedica.execute_query(evaluaciones_medicas_query, (ficha_id,))
        ficha['evaluaciones_medicas'] = evaluaciones_medicas
        
        # Obtener evaluaciones de enfermería
        evaluaciones_enfermeria_query = """
        SELECT ee.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM evaluaciones_enfermeria ee
        JOIN profesionales p ON ee.profesional_id = p.id
        WHERE ee.ficha_id = %s
        ORDER BY ee.fecha_evaluacion DESC
        """
        evaluaciones_enfermeria = FichaMedica.execute_query(evaluaciones_enfermeria_query, (ficha_id,))
        ficha['evaluaciones_enfermeria'] = evaluaciones_enfermeria
        
        # Obtener evaluaciones kinésicas
        evaluaciones_kinesicas_query = """
        SELECT ek.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM evaluaciones_kinesicas ek
        JOIN profesionales p ON ek.profesional_id = p.id
        WHERE ek.ficha_id = %s
        ORDER BY ek.fecha_evaluacion DESC
        """
        evaluaciones_kinesicas = FichaMedica.execute_query(evaluaciones_kinesicas_query, (ficha_id,))
        ficha['evaluaciones_kinesicas'] = evaluaciones_kinesicas
        
        # Obtener notas de evolución
        notas_evolucion_query = """
        SELECT ne.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM notas_evolucion ne
        JOIN profesionales p ON ne.profesional_id = p.id
        WHERE ne.ficha_id = %s
        ORDER BY ne.fecha_hora DESC
        """
        notas_evolucion = FichaMedica.execute_query(notas_evolucion_query, (ficha_id,))
        ficha['notas_evolucion'] = notas_evolucion
        
        # Obtener alta médica (si existe)
        alta_query = """
        SELECT am.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM altas_medicas am
        JOIN profesionales p ON am.profesional_id = p.id
        WHERE am.ficha_id = %s
        """
        alta = FichaMedica.execute_query(alta_query, (ficha_id,))
        if alta:
            ficha['alta'] = alta[0]
        
        return ficha
    
    @staticmethod
    def search(term=None, filters=None):
        """Busca fichas médicas con filtros opcionales."""
        params = []
        where_clauses = ["f.estado = 'Activa'"]
        
        if term:
            where_clauses.append("(p.nombre LIKE %s OR p.apellido LIKE %s OR p.rut LIKE %s)")
            search_term = f"%{term}%"
            params.extend([search_term, search_term, search_term])
        
        if filters:
            if 'tipo_cirugia' in filters and filters['tipo_cirugia']:
                where_clauses.append("am.tipo_cirugia = %s")
                params.append(filters['tipo_cirugia'])
            
            if 'profesional_id' in filters and filters['profesional_id']:
                where_clauses.append("f.profesional_deriva_id = %s")
                params.append(filters['profesional_id'])
            
            if 'fecha_desde' in filters and filters['fecha_desde']:
                where_clauses.append("f.fecha_ingreso >= %s")
                params.append(filters['fecha_desde'])
            
            if 'fecha_hasta' in filters and filters['fecha_hasta']:
                where_clauses.append("f.fecha_ingreso <= %s")
                params.append(filters['fecha_hasta'])
        
        query = f"""
        SELECT f.*, 
               p.nombre as paciente_nombre, 
               p.apellido as paciente_apellido, 
               prof.nombre as profesional_nombre, 
               prof.apellido as profesional_apellido,
               am.diagnostico_principal,
               am.tipo_cirugia,
               (SELECT MAX(fecha_evaluacion) FROM evaluaciones_medicas WHERE ficha_id = f.id) as ultimo_control
        FROM fichas_medicas f
        JOIN pacientes p ON f.paciente_id = p.id
        LEFT JOIN profesionales prof ON f.profesional_deriva_id = prof.id
        LEFT JOIN antecedentes_medicos am ON f.id = am.ficha_id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY f.fecha_ingreso DESC
        """
        return FichaMedica.execute_query(query, params)
    
    @staticmethod
    def create(data, profesional_id):
        """Crea una nueva ficha médica."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Insertar la ficha médica
            cursor.execute("""
                INSERT INTO fichas_medicas (
                    paciente_id, fecha_ingreso, motivo_consulta, 
                    profesional_deriva_id, prevision_salud
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                data.get('paciente_id'),
                data.get('fecha_ingreso'),
                data.get('motivo_consulta'),
                data.get('profesional_deriva_id'),
                data.get('prevision_salud')
            ))
            
            ficha_id = cursor.lastrowid
            
            # Si se proporcionan antecedentes médicos, los insertamos
            if 'antecedentes' in data and data['antecedentes']:
                ant = data['antecedentes']
                cursor.execute("""
                    INSERT INTO antecedentes_medicos (
                        ficha_id, diagnostico_principal, diagnosticos_secundarios,
                        antecedentes_relevantes, alergias, medicamentos_actuales,
                        tipo_cirugia, fecha_cirugia, profesional_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ficha_id,
                    ant.get('diagnostico_principal'),
                    ant.get('diagnosticos_secundarios'),
                    ant.get('antecedentes_relevantes'),
                    ant.get('alergias'),
                    ant.get('medicamentos_actuales'),
                    ant.get('tipo_cirugia'),
                    ant.get('fecha_cirugia'),
                    profesional_id
                ))
            
            conn.commit()
            return ficha_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def update(ficha_id, data):
        """Actualiza los datos de una ficha médica."""
        query = """
        UPDATE fichas_medicas SET 
            paciente_id = %s,
            fecha_ingreso = %s,
            motivo_consulta = %s,
            profesional_deriva_id = %s,
            prevision_salud = %s,
            fecha_ultima_actualizacion = NOW()
        WHERE id = %s
        """
        params = (
            data.get('paciente_id'),
            data.get('fecha_ingreso'),
            data.get('motivo_consulta'),
            data.get('profesional_deriva_id'),
            data.get('prevision_salud'),
            ficha_id
        )
        return FichaMedica.execute_query(query, params, fetch=False, commit=True)
    
    @staticmethod
    def delete(ficha_id):
        """Cambia el estado de una ficha médica a 'Inactiva'."""
        query = """
        UPDATE fichas_medicas 
        SET estado = 'Inactiva', 
            fecha_ultima_actualizacion = NOW()
        WHERE id = %s
        """
        return FichaMedica.execute_query(query, (ficha_id,), fetch=False, commit=True)

    @staticmethod
    def add_antecedente(ficha_id, data, profesional_id):
        """Añade un nuevo registro de antecedentes médicos a la ficha."""
        query = """
        INSERT INTO antecedentes_medicos (
            ficha_id, diagnostico_principal, diagnosticos_secundarios,
            antecedentes_relevantes, alergias, medicamentos_actuales,
            tipo_cirugia, fecha_cirugia, profesional_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            ficha_id,
            data.get('diagnostico_principal'),
            data.get('diagnosticos_secundarios'),
            data.get('antecedentes_relevantes'),
            data.get('alergias'),
            data.get('medicamentos_actuales'),
            data.get('tipo_cirugia'),
            data.get('fecha_cirugia'),
            profesional_id
        )
        
        antecedente_id = FichaMedica.execute_query(query, params, fetch=False, commit=True)
        
        # Actualizar la fecha de última modificación de la ficha
        FichaMedica.execute_query(
            "UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s", 
            (ficha_id,), 
            fetch=False, 
            commit=True
        )
        
        return antecedente_id
    
    @staticmethod
    def add_evaluacion_medica(ficha_id, data, profesional_id):
        """Añade una nueva evaluación médica a la ficha."""
        query = """
        INSERT INTO evaluaciones_medicas (
            ficha_id, profesional_id, fecha_evaluacion,
            examen_fisico, indicaciones_medicas, examenes_solicitados,
            fecha_proxima_evaluacion
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            ficha_id,
            profesional_id,
            data.get('fecha_evaluacion', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('examen_fisico'),
            data.get('indicaciones_medicas'),
            data.get('examenes_solicitados'),
            data.get('fecha_proxima_evaluacion')
        )
        
        evaluacion_id = FichaMedica.execute_query(query, params, fetch=False, commit=True)
        
        # Actualizar la fecha de última modificación de la ficha
        FichaMedica.execute_query(
            "UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s", 
            (ficha_id,), 
            fetch=False, 
            commit=True
        )
        
        return evaluacion_id
    
    @staticmethod
    def add_evaluacion_enfermeria(ficha_id, data, profesional_id):
        """Añade una nueva evaluación de enfermería a la ficha."""
        query = """
        INSERT INTO evaluaciones_enfermeria (
            ficha_id, profesional_id, fecha_evaluacion,
            tension_arterial, frecuencia_cardiaca, frecuencia_respiratoria,
            temperatura, saturacion_o2, observaciones_generales,
            cuidado_heridas, medicamentos_administrados, comentarios_adicionales
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            ficha_id,
            profesional_id,
            data.get('fecha_evaluacion', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('tension_arterial'),
            data.get('frecuencia_cardiaca'),
            data.get('frecuencia_respiratoria'),
            data.get('temperatura'),
            data.get('saturacion_o2'),
            data.get('observaciones_generales'),
            data.get('cuidado_heridas'),
            data.get('medicamentos_administrados'),
            data.get('comentarios_adicionales')
        )
        
        evaluacion_id = FichaMedica.execute_query(query, params, fetch=False, commit=True)
        
        # Actualizar la fecha de última modificación de la ficha
        FichaMedica.execute_query(
            "UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s", 
            (ficha_id,), 
            fetch=False, 
            commit=True
        )
        
        return evaluacion_id
    
    @staticmethod
    def add_evaluacion_kinesica(ficha_id, data, profesional_id):
        """Añade una nueva evaluación kinésica a la ficha."""
        query = """
        INSERT INTO evaluaciones_kinesicas (
            ficha_id, profesional_id, fecha_evaluacion,
            motivo_atencion, evaluacion_funcional, objetivos_tratamiento,
            intervenciones_realizadas, evolucion_respuesta, sugerencias_equipo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            ficha_id,
            profesional_id,
            data.get('fecha_evaluacion', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('motivo_atencion'),
            data.get('evaluacion_funcional'),
            data.get('objetivos_tratamiento'),
            data.get('intervenciones_realizadas'),
            data.get('evolucion_respuesta'),
            data.get('sugerencias_equipo')
        )
        
        evaluacion_id = FichaMedica.execute_query(query, params, fetch=False, commit=True)
        
        # Actualizar la fecha de última modificación de la ficha
        FichaMedica.execute_query(
            "UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s", 
            (ficha_id,), 
            fetch=False, 
            commit=True
        )
        
        return evaluacion_id
    
    @staticmethod
    def add_nota_evolucion(ficha_id, data, profesional_id):
        """Añade una nueva nota de evolución a la ficha."""
        query = """
        INSERT INTO notas_evolucion (
            ficha_id, profesional_id, fecha_hora, observacion
        ) VALUES (%s, %s, %s, %s)
        """
        params = (
            ficha_id,
            profesional_id,
            data.get('fecha_hora', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('observacion')
        )
        
        nota_id = FichaMedica.execute_query(query, params, fetch=False, commit=True)
        
        # Actualizar la fecha de última modificación de la ficha
        FichaMedica.execute_query(
            "UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s", 
            (ficha_id,), 
            fetch=False, 
            commit=True
        )
        
        return nota_id
    
    @staticmethod
    def add_alta(ficha_id, data, profesional_id):
        """Añade un alta médica a la ficha y la marca como archivada."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Verificar si ya existe un alta para esta ficha
            cursor.execute('SELECT id FROM altas_medicas WHERE ficha_id = %s', (ficha_id,))
            if cursor.fetchone():
                raise ValueError('Esta ficha ya tiene un alta médica registrada')
            
            # Insertar el alta médica
            cursor.execute("""
                INSERT INTO altas_medicas (
                    ficha_id, fecha_alta, motivo_alta, 
                    indicaciones_post_alta, derivaciones_sugeridas, profesional_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                ficha_id,
                data.get('fecha_alta'),
                data.get('motivo_alta'),
                data.get('indicaciones_post_alta'),
                data.get('derivaciones_sugeridas'),
                profesional_id
            ))
            
            alta_id = cursor.lastrowid
            
            # Cambiar estado de la ficha a "Archivada"
            cursor.execute('UPDATE fichas_medicas SET estado = "Archivada", fecha_ultima_actualizacion = NOW() WHERE id = %s', (ficha_id,))
            
            conn.commit()
            return alta_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_estadisticas():
        """Obtiene estadísticas generales para el dashboard."""
        # Total de pacientes
        total_pacientes_query = "SELECT COUNT(*) as total FROM pacientes WHERE activo = 1"
        total_pacientes = FichaMedica.execute_query(total_pacientes_query)[0]['total']
        
        # Total de fichas activas
        total_fichas_query = "SELECT COUNT(*) as total FROM fichas_medicas WHERE estado = 'Activa'"
        total_fichas = FichaMedica.execute_query(total_fichas_query)[0]['total']
        
        # Citas del mes
        citas_mes_query = """
            SELECT COUNT(*) as total FROM evaluaciones_medicas 
            WHERE fecha_evaluacion BETWEEN DATE_FORMAT(NOW(), '%Y-%m-01') AND LAST_DAY(NOW())
        """
        citas_mes = FichaMedica.execute_query(citas_mes_query)[0]['total']
        
        # Fichas nuevas en los últimos 30 días
        fichas_nuevas_query = """
            SELECT COUNT(*) as total FROM fichas_medicas 
            WHERE fecha_ingreso >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """
        fichas_nuevas = FichaMedica.execute_query(fichas_nuevas_query)[0]['total']
        
        # Próximas citas programadas (para el widget de "Pendientes Hoy")
        citas_hoy_query = """
            SELECT COUNT(*) as total FROM evaluaciones_medicas 
            WHERE DATE(fecha_proxima_evaluacion) = CURDATE()
        """
        citas_hoy = FichaMedica.execute_query(citas_hoy_query)[0]['total']
        
        # Distribución por tipo de cirugía
        distribucion_cirugias_query = """
            SELECT tipo_cirugia, COUNT(*) as total 
            FROM antecedentes_medicos 
            GROUP BY tipo_cirugia
        """
        distribucion_cirugias = FichaMedica.execute_query(distribucion_cirugias_query)
        
        return {
            'total_pacientes': total_pacientes,
            'total_fichas': total_fichas,
            'citas_mes': citas_mes,
            'fichas_nuevas': fichas_nuevas,
            'citas_hoy': citas_hoy,
            'distribucion_cirugias': distribucion_cirugias
        }