from flask import Flask, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import os
import datetime
import jwt
from functools import wraps
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_secreta_por_defecto')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['JWT_EXPIRATION_DELTA'] = int(os.getenv('JWT_EXPIRATION_DELTA', 7200))  # 2 horas por defecto

# Habilitar CORS para permitir peticiones desde el frontend
CORS(app)

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'renovafit_user'),
    'password': os.getenv('DB_PASSWORD', 'secure_password_here'),
    'db': os.getenv('DB_NAME', 'renovafit_medical'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Función para conectar a la base de datos
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# Decorador para verificar token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Buscar token en los headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token es requerido'}), 401
        
        try:
            # Decodificar el token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            # Verificar si el usuario existe y está activo
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, nombre, apellido, email, especialidad FROM profesionales WHERE id = %s AND activo = 1', (data['id'],))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not current_user:
                return jsonify({'message': 'Usuario no encontrado o inactivo'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado. Por favor, inicie sesión nuevamente'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        
        # Pasar el usuario actual a la función
        return f(current_user, *args, **kwargs)
    
    return decorated

# Ruta de login
@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Falta información de autenticación'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nombre, apellido, email, especialidad, password_hash FROM profesionales WHERE email = %s', (auth.get('email'),))
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user['password_hash'], auth.get('password')):
        cursor.close()
        conn.close()
        return jsonify({'message': 'Email o contraseña incorrectos'}), 401
    
    # Actualizar último acceso
    cursor.execute('UPDATE profesionales SET ultimo_acceso = NOW() WHERE id = %s', (user['id'],))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    # Generar token JWT
    token_payload = {
        'id': user['id'],
        'email': user['email'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=app.config['JWT_EXPIRATION_DELTA'])
    }
    
    token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'nombre': user['nombre'],
            'apellido': user['apellido'],
            'email': user['email'],
            'especialidad': user['especialidad']
        }
    })

# Ruta para verificar estado de autenticación
@app.route('/api/auth/check', methods=['GET'])
@token_required
def check_auth(current_user):
    return jsonify({
        'authenticated': True,
        'user': {
            'id': current_user['id'],
            'nombre': current_user['nombre'],
            'apellido': current_user['apellido'],
            'email': current_user['email'],
            'especialidad': current_user['especialidad']
        }
    })

# Rutas para pacientes
@app.route('/api/pacientes', methods=['GET'])
@token_required
def get_pacientes(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Búsqueda por nombre, apellido o rut
    search = request.args.get('search', '')
    
    if search:
        cursor.execute('''
            SELECT * FROM pacientes 
            WHERE (nombre LIKE %s OR apellido LIKE %s OR rut LIKE %s) AND activo = 1
            ORDER BY apellido, nombre
        ''', (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute('SELECT * FROM pacientes WHERE activo = 1 ORDER BY apellido, nombre')
    
    pacientes = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(pacientes)

@app.route('/api/pacientes/<int:id>', methods=['GET'])
@token_required
def get_paciente(current_user, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not paciente:
        return jsonify({'message': 'Paciente no encontrado'}), 404
    
    return jsonify(paciente)

@app.route('/api/pacientes', methods=['POST'])
@token_required
def create_paciente(current_user):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el RUT ya existe
    if 'rut' in data and data['rut']:
        cursor.execute('SELECT id FROM pacientes WHERE rut = %s', (data['rut'],))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Ya existe un paciente con ese RUT'}), 400
    
    # Insertar el nuevo paciente
    try:
        cursor.execute('''
            INSERT INTO pacientes (rut, nombre, apellido, fecha_nacimiento, edad, sexo, 
                                 telefono, email, direccion, contacto_emergencia_nombre,
                                 contacto_emergencia_telefono)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
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
            data.get('contacto_emergencia_telefono')
        ))
        
        conn.commit()
        new_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear paciente: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({'id': new_id, 'message': 'Paciente creado exitosamente'}), 201

@app.route('/api/pacientes/<int:id>', methods=['PUT'])
@token_required
def update_paciente(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el paciente existe
    cursor.execute('SELECT id FROM pacientes WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Paciente no encontrado'}), 404
    
    # Verificar si el RUT ya existe en otro paciente
    if 'rut' in data and data['rut']:
        cursor.execute('SELECT id FROM pacientes WHERE rut = %s AND id != %s', (data['rut'], id))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Ya existe otro paciente con ese RUT'}), 400
    
    # Actualizar el paciente
    try:
        cursor.execute('''
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
            WHERE id = %s
        ''', (
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
            id
        ))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al actualizar paciente: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Paciente actualizado exitosamente'})

@app.route('/api/pacientes/<int:id>', methods=['DELETE'])
@token_required
def delete_paciente(current_user, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el paciente existe
    cursor.execute('SELECT id FROM pacientes WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Paciente no encontrado'}), 404
    
    # Marcar como inactivo en lugar de eliminar
    try:
        cursor.execute('UPDATE pacientes SET activo = 0 WHERE id = %s', (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al eliminar paciente: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Paciente eliminado exitosamente'})

# Rutas para fichas médicas
@app.route('/api/fichas', methods=['GET'])
@token_required
def get_fichas(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Parámetros de consulta
    paciente_id = request.args.get('paciente_id')
    
    if paciente_id:
        cursor.execute('''
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
        ''', (paciente_id,))
    else:
        cursor.execute('''
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
        ''')
    
    fichas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(fichas)

@app.route('/api/fichas/<int:id>', methods=['GET'])
@token_required
def get_ficha(current_user, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener la ficha médica principal
    cursor.execute('''
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
    ''', (id,))
    
    ficha = cursor.fetchone()
    
    if not ficha:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Obtener antecedentes médicos
    cursor.execute('''
        SELECT am.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido
        FROM antecedentes_medicos am
        JOIN profesionales p ON am.profesional_id = p.id
        WHERE am.ficha_id = %s
        ORDER BY am.fecha_registro DESC
    ''', (id,))
    
    antecedentes = cursor.fetchall()
    ficha['antecedentes'] = antecedentes
    
    # Obtener evaluaciones médicas
    cursor.execute('''
        SELECT em.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM evaluaciones_medicas em
        JOIN profesionales p ON em.profesional_id = p.id
        WHERE em.ficha_id = %s
        ORDER BY em.fecha_evaluacion DESC
    ''', (id,))
    
    evaluaciones_medicas = cursor.fetchall()
    ficha['evaluaciones_medicas'] = evaluaciones_medicas
    
    # Obtener evaluaciones de enfermería
    cursor.execute('''
        SELECT ee.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM evaluaciones_enfermeria ee
        JOIN profesionales p ON ee.profesional_id = p.id
        WHERE ee.ficha_id = %s
        ORDER BY ee.fecha_evaluacion DESC
    ''', (id,))
    
    evaluaciones_enfermeria = cursor.fetchall()
    ficha['evaluaciones_enfermeria'] = evaluaciones_enfermeria
    
    # Obtener evaluaciones kinésicas
    cursor.execute('''
        SELECT ek.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM evaluaciones_kinesicas ek
        JOIN profesionales p ON ek.profesional_id = p.id
        WHERE ek.ficha_id = %s
        ORDER BY ek.fecha_evaluacion DESC
    ''', (id,))
    
    evaluaciones_kinesicas = cursor.fetchall()
    ficha['evaluaciones_kinesicas'] = evaluaciones_kinesicas
    
    # Obtener notas de evolución
    cursor.execute('''
        SELECT ne.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM notas_evolucion ne
        JOIN profesionales p ON ne.profesional_id = p.id
        WHERE ne.ficha_id = %s
        ORDER BY ne.fecha_hora DESC
    ''', (id,))
    
    notas_evolucion = cursor.fetchall()
    ficha['notas_evolucion'] = notas_evolucion
    
    # Obtener alta médica (si existe)
    cursor.execute('''
        SELECT am.*, 
               p.nombre as profesional_nombre, 
               p.apellido as profesional_apellido,
               p.especialidad as profesional_especialidad
        FROM altas_medicas am
        JOIN profesionales p ON am.profesional_id = p.id
        WHERE am.ficha_id = %s
    ''', (id,))
    
    alta = cursor.fetchone()
    if alta:
        ficha['alta'] = alta
    
    cursor.close()
    conn.close()
    
    return jsonify(ficha)

@app.route('/api/fichas', methods=['POST'])
@token_required
def create_ficha(current_user):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el paciente existe
    cursor.execute('SELECT id FROM pacientes WHERE id = %s', (data.get('paciente_id'),))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Paciente no encontrado'}), 404
    
    # Insertar la ficha médica
    try:
        cursor.execute('''
            INSERT INTO fichas_medicas (
                paciente_id, fecha_ingreso, motivo_consulta, 
                profesional_deriva_id, prevision_salud
            ) VALUES (%s, %s, %s, %s, %s)
        ''', (
            data.get('paciente_id'),
            data.get('fecha_ingreso'),
            data.get('motivo_consulta'),
            data.get('profesional_deriva_id'),
            data.get('prevision_salud')
        ))
        
        conn.commit()
        ficha_id = cursor.lastrowid
        
        # Si se proporcionan antecedentes médicos, los insertamos
        if 'antecedentes' in data and data['antecedentes']:
            ant = data['antecedentes']
            cursor.execute('''
                INSERT INTO antecedentes_medicos (
                    ficha_id, diagnostico_principal, diagnosticos_secundarios,
                    antecedentes_relevantes, alergias, medicamentos_actuales,
                    tipo_cirugia, fecha_cirugia, profesional_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                ficha_id,
                ant.get('diagnostico_principal'),
                ant.get('diagnosticos_secundarios'),
                ant.get('antecedentes_relevantes'),
                ant.get('alergias'),
                ant.get('medicamentos_actuales'),
                ant.get('tipo_cirugia'),
                ant.get('fecha_cirugia'),
                current_user['id']
            ))
            conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear ficha médica: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': ficha_id,
        'message': 'Ficha médica creada exitosamente'
    }), 201

@app.route('/api/fichas/<int:id>', methods=['PUT'])
@token_required
def update_ficha(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ficha existe
    cursor.execute('SELECT id FROM fichas_medicas WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Actualizar la ficha médica
    try:
        cursor.execute('''
            UPDATE fichas_medicas SET 
                paciente_id = %s,
                fecha_ingreso = %s,
                motivo_consulta = %s,
                profesional_deriva_id = %s,
                prevision_salud = %s,
                fecha_ultima_actualizacion = NOW()
            WHERE id = %s
        ''', (
            data.get('paciente_id'),
            data.get('fecha_ingreso'),
            data.get('motivo_consulta'),
            data.get('profesional_deriva_id'),
            data.get('prevision_salud'),
            id
        ))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al actualizar ficha médica: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Ficha médica actualizada exitosamente'})

@app.route('/api/fichas/<int:id>/antecedentes', methods=['POST'])
@token_required
def create_antecedente(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ficha existe
    cursor.execute('SELECT id FROM fichas_medicas WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Insertar los antecedentes médicos
    try:
        cursor.execute('''
            INSERT INTO antecedentes_medicos (
                ficha_id, diagnostico_principal, diagnosticos_secundarios,
                antecedentes_relevantes, alergias, medicamentos_actuales,
                tipo_cirugia, fecha_cirugia, profesional_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            id,
            data.get('diagnostico_principal'),
            data.get('diagnosticos_secundarios'),
            data.get('antecedentes_relevantes'),
            data.get('alergias'),
            data.get('medicamentos_actuales'),
            data.get('tipo_cirugia'),
            data.get('fecha_cirugia'),
            current_user['id']
        ))
        
        conn.commit()
        antecedente_id = cursor.lastrowid
        
        # Actualizar la fecha de última modificación de la ficha
        cursor.execute('UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s', (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear antecedentes médicos: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': antecedente_id,
        'message': 'Antecedentes médicos creados exitosamente'
    }), 201

@app.route('/api/fichas/<int:id>/evaluaciones/medica', methods=['POST'])
@token_required
def create_evaluacion_medica(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ficha existe
    cursor.execute('SELECT id FROM fichas_medicas WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Insertar la evaluación médica
    try:
        cursor.execute('''
            INSERT INTO evaluaciones_medicas (
                ficha_id, profesional_id, fecha_evaluacion,
                examen_fisico, indicaciones_medicas, examenes_solicitados,
                fecha_proxima_evaluacion
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            id,
            current_user['id'],
            data.get('fecha_evaluacion', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('examen_fisico'),
            data.get('indicaciones_medicas'),
            data.get('examenes_solicitados'),
            data.get('fecha_proxima_evaluacion')
        ))
        
        conn.commit()
        evaluacion_id = cursor.lastrowid
        
        # Actualizar la fecha de última modificación de la ficha
        cursor.execute('UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s', (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear evaluación médica: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': evaluacion_id,
        'message': 'Evaluación médica creada exitosamente'
    }), 201

@app.route('/api/fichas/<int:id>/evaluaciones/enfermeria', methods=['POST'])
@token_required
def create_evaluacion_enfermeria(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ficha existe
    cursor.execute('SELECT id FROM fichas_medicas WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Insertar la evaluación de enfermería
    try:
        cursor.execute('''
            INSERT INTO evaluaciones_enfermeria (
                ficha_id, profesional_id, fecha_evaluacion,
                tension_arterial, frecuencia_cardiaca, frecuencia_respiratoria,
                temperatura, saturacion_o2, observaciones_generales,
                cuidado_heridas, medicamentos_administrados, comentarios_adicionales
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            id,
            current_user['id'],
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
        ))
        
        conn.commit()
        evaluacion_id = cursor.lastrowid
        
        # Actualizar la fecha de última modificación de la ficha
        cursor.execute('UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s', (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear evaluación de enfermería: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': evaluacion_id,
        'message': 'Evaluación de enfermería creada exitosamente'
    }), 201

@app.route('/api/fichas/<int:id>/evaluaciones/kinesica', methods=['POST'])
@token_required
def create_evaluacion_kinesica(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ficha existe
    cursor.execute('SELECT id FROM fichas_medicas WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Insertar la evaluación kinésica
    try:
        cursor.execute('''
            INSERT INTO evaluaciones_kinesicas (
                ficha_id, profesional_id, fecha_evaluacion,
                motivo_atencion, evaluacion_funcional, objetivos_tratamiento,
                intervenciones_realizadas, evolucion_respuesta, sugerencias_equipo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            id,
            current_user['id'],
            data.get('fecha_evaluacion', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('motivo_atencion'),
            data.get('evaluacion_funcional'),
            data.get('objetivos_tratamiento'),
            data.get('intervenciones_realizadas'),
            data.get('evolucion_respuesta'),
            data.get('sugerencias_equipo')
        ))
        
        conn.commit()
        evaluacion_id = cursor.lastrowid
        
        # Actualizar la fecha de última modificación de la ficha
        cursor.execute('UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s', (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear evaluación kinésica: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': evaluacion_id,
        'message': 'Evaluación kinésica creada exitosamente'
    }), 201

@app.route('/api/fichas/<int:id>/evoluciones', methods=['POST'])
@token_required
def create_evolucion(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ficha existe
    cursor.execute('SELECT id FROM fichas_medicas WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Insertar la nota de evolución
    try:
        cursor.execute('''
            INSERT INTO notas_evolucion (
                ficha_id, profesional_id, fecha_hora, observacion
            ) VALUES (%s, %s, %s, %s)
        ''', (
            id,
            current_user['id'],
            data.get('fecha_hora', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('observacion')
        ))
        
        conn.commit()
        evolucion_id = cursor.lastrowid
        
        # Actualizar la fecha de última modificación de la ficha
        cursor.execute('UPDATE fichas_medicas SET fecha_ultima_actualizacion = NOW() WHERE id = %s', (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear nota de evolución: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': evolucion_id,
        'message': 'Nota de evolución creada exitosamente'
    }), 201

@app.route('/api/fichas/<int:id>/alta', methods=['POST'])
@token_required
def crear_alta(current_user, id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ficha existe
    cursor.execute('SELECT id FROM fichas_medicas WHERE id = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Ficha médica no encontrada'}), 404
    
    # Verificar si ya existe un alta para esta ficha
    cursor.execute('SELECT id FROM altas_medicas WHERE ficha_id = %s', (id,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'message': 'Esta ficha ya tiene un alta médica registrada'}), 400
    
    # Insertar el alta médica
    try:
        cursor.execute('''
            INSERT INTO altas_medicas (
                ficha_id, fecha_alta, motivo_alta, 
                indicaciones_post_alta, derivaciones_sugeridas, profesional_id
            ) VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            id,
            data.get('fecha_alta'),
            data.get('motivo_alta'),
            data.get('indicaciones_post_alta'),
            data.get('derivaciones_sugeridas'),
            current_user['id']
        ))
        
        # Cambiar estado de la ficha a "Archivada"
        cursor.execute('UPDATE fichas_medicas SET estado = "Archivada", fecha_ultima_actualizacion = NOW() WHERE id = %s', (id,))
        
        conn.commit()
        alta_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'message': f'Error al crear alta médica: {str(e)}'}), 500
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': alta_id,
        'message': 'Alta médica creada exitosamente'
    }), 201

# Rutas para profesionales (solo para administradores en un futuro)
@app.route('/api/profesionales', methods=['GET'])
@token_required
def get_profesionales(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, apellido, especialidad, email, telefono, 
               activo, fecha_registro, ultimo_acceso, imagen_perfil
        FROM profesionales
        WHERE activo = 1
        ORDER BY apellido, nombre
    ''')
    
    profesionales = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(profesionales)

# Estadísticas
@app.route('/api/estadisticas', methods=['GET'])
@token_required
def get_estadisticas(current_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de pacientes
    cursor.execute('SELECT COUNT(*) as total FROM pacientes WHERE activo = 1')
    total_pacientes = cursor.fetchone()['total']
    
    # Total de fichas activas
    cursor.execute('SELECT COUNT(*) as total FROM fichas_medicas WHERE estado = "Activa"')
    total_fichas = cursor.fetchone()['total']
    
    # Citas del mes (simulado, se debería implementar integración con sistema de citas)
    cursor.execute('''
        SELECT COUNT(*) as total FROM evaluaciones_medicas 
        WHERE fecha_evaluacion BETWEEN DATE_FORMAT(NOW(), '%Y-%m-01') AND LAST_DAY(NOW())
    ''')
    citas_mes = cursor.fetchone()['total']
    
    # Fichas nuevas en los últimos 30 días
    cursor.execute('''
        SELECT COUNT(*) as total FROM fichas_medicas 
        WHERE fecha_ingreso >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    ''')
    fichas_nuevas = cursor.fetchone()['total']
    
    # Próximas citas programadas (para el widget de "Pendientes Hoy")
    cursor.execute('''
        SELECT COUNT(*) as total FROM evaluaciones_medicas 
        WHERE DATE(fecha_proxima_evaluacion) = CURDATE()
    ''')
    citas_hoy = cursor.fetchone()['total']
    
    # Distribución por tipo de cirugía
    cursor.execute('''
        SELECT tipo_cirugia, COUNT(*) as total 
        FROM antecedentes_medicos 
        GROUP BY tipo_cirugia
    ''')
    distribucion_cirugias = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'total_pacientes': total_pacientes,
        'total_fichas': total_fichas,
        'citas_mes': citas_mes,
        'fichas_nuevas': fichas_nuevas,
        'citas_hoy': citas_hoy,
        'distribucion_cirugias': distribucion_cirugias
    })

if __name__ == '__main__':
    app.run(debug=True)