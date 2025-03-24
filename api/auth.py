import jwt
from functools import wraps
from flask import request, jsonify, current_app, g
from datetime import datetime, timedelta
import logging
from models import Profesional

# Configuración de logging
logger = logging.getLogger(__name__)

def generate_token(user_id):
    """Genera un token JWT para el usuario especificado."""
    try:
        # Configurar tiempo de expiración
        expiration = datetime.utcnow() + timedelta(seconds=current_app.config['JWT_EXPIRATION_DELTA'])
        
        # Crear payload
        payload = {
            'id': user_id,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        
        # Generar token
        token = jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        return token
    except Exception as e:
        logger.error(f"Error al generar token: {str(e)}")
        return None

def decode_token(token):
    """Decodifica un token JWT y verifica su validez."""
    try:
        # Decodificar token
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expirado. Por favor, inicie sesión nuevamente.'}
    except jwt.InvalidTokenError:
        return {'error': 'Token inválido. Por favor, inicie sesión nuevamente.'}

def token_required(f):
    """Decorador para verificar que el token JWT sea válido y establecer el usuario actual."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        # Verificar si hay un encabezado de autorización
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token requerido'}), 401
        
        # Decodificar token
        payload = decode_token(token)
        
        if 'error' in payload:
            return jsonify({'message': payload['error']}), 401
        
        # Obtener usuario
        user_id = payload['id']
        current_user = Profesional.get_by_id(user_id)
        
        if not current_user:
            return jsonify({'message': 'Usuario no encontrado o inactivo'}), 401
        
        # Almacenar usuario actual en g para acceso en la solicitud
        g.current_user = current_user
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def get_current_user():
    """Obtiene el usuario actual establecido por el decorador token_required."""
    return g.current_user if hasattr(g, 'current_user') else None

# Rutas de autenticación
def init_auth_routes(app):
    """Inicializa las rutas de autenticación."""
    
    @app.route('/api/login', methods=['POST'])
    def login():
        """Ruta para iniciar sesión y obtener un token JWT."""
        try:
            data = request.get_json()
            
            # Verificar que se proporcionaron email y contraseña
            if not data or not data.get('email') or not data.get('password'):
                return jsonify({'message': 'Email y contraseña requeridos'}), 400
            
            # Verificar las credenciales
            if not Profesional.verify_password(data['email'], data['password']):
                return jsonify({'message': 'Email o contraseña incorrectos'}), 401
            
            # Obtener usuario
            user = Profesional.get_by_email(data['email'])
            
            # Actualizar último acceso
            conn = Profesional.get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('UPDATE profesionales SET ultimo_acceso = NOW() WHERE id = %s', (user['id'],))
                conn.commit()
            finally:
                conn.close()
            
            # Generar token
            token = generate_token(user['id'])
            
            if not token:
                return jsonify({'message': 'Error al generar token'}), 500
            
            # Filtrar campos sensibles del usuario
            user_data = {
                'id': user['id'],
                'nombre': user['nombre'],
                'apellido': user['apellido'],
                'email': user['email'],
                'especialidad': user['especialidad']
            }
            
            return jsonify({
                'token': token,
                'user': user_data
            }), 200
            
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return jsonify({'message': 'Error en el servidor'}), 500
    
    @app.route('/api/auth/check', methods=['GET'])
    @token_required
    def check_auth(current_user):
        """Ruta para verificar si el token es válido."""
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user['id'],
                'nombre': current_user['nombre'],
                'apellido': current_user['apellido'],
                'email': current_user['email'],
                'especialidad': current_user['especialidad']
            }
        }), 200
    
    @app.route('/api/register', methods=['POST'])
    def register():
        """Ruta para registrar un nuevo profesional (sólo administradores)."""
        try:
            # Verificar si hay un usuario autenticado
            token = None
            auth_header = request.headers.get('Authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            
            # Si no hay token, verificar si es el primer usuario (setup inicial)
            if not token:
                # Verificar si hay usuarios en el sistema
                query = "SELECT COUNT(*) as total FROM profesionales"
                result = Profesional.execute_query(query)
                
                if result[0]['total'] > 0:
                    return jsonify({'message': 'No autorizado'}), 401
            else:
                # Verificar que el usuario sea administrador
                payload = decode_token(token)
                
                if 'error' in payload:
                    return jsonify({'message': payload['error']}), 401
                
                user_id = payload['id']
                current_user = Profesional.get_by_id(user_id)
                
                if not current_user or current_user.get('rol') != 'admin':
                    return jsonify({'message': 'No autorizado. Se requiere rol de administrador para esta operación'}), 403
            
            # Datos del nuevo profesional
            data = request.get_json()
            
            # Verificar que se proporcionaron los datos requeridos
            required_fields = ['nombre', 'apellido', 'email', 'password', 'especialidad']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'message': f'El campo {field} es requerido'}), 400
            
            # Verificar si ya existe un usuario con ese email
            existing_user = Profesional.get_by_email(data['email'])
            if existing_user:
                return jsonify({'message': 'Ya existe un profesional con ese email'}), 409
            
            # Crear profesional
            profesional_id = Profesional.create(data)
            
            return jsonify({
                'message': 'Profesional registrado con éxito',
                'id': profesional_id
            }), 201
            
        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            return jsonify({'message': 'Error en el servidor'}), 500
    
    @app.route('/api/change-password', methods=['POST'])
    @token_required
    def change_password(current_user):
        """Ruta para cambiar la contraseña del usuario actual."""
        try:
            data = request.get_json()
            
            # Verificar que se proporcionó la contraseña actual y la nueva
            if not data or not data.get('current_password') or not data.get('new_password'):
                return jsonify({'message': 'Contraseña actual y nueva requeridas'}), 400
            
            # Verificar la contraseña actual
            if not Profesional.verify_password(current_user['email'], data['current_password']):
                return jsonify({'message': 'Contraseña actual incorrecta'}), 401
            
            # Actualizar contraseña
            Profesional.update(current_user['id'], {'password': data['new_password']})
            
            return jsonify({'message': 'Contraseña actualizada con éxito'}), 200
            
        except Exception as e:
            logger.error(f"Error al cambiar contraseña: {str(e)}")
            return jsonify({'message': 'Error en el servidor'}), 500
    
    @app.route('/api/profile', methods=['GET'])
    @token_required
    def get_profile(current_user):
        """Obtiene el perfil completo del usuario actual."""
        try:
            # Filtrar campos sensibles
            profile = {
                'id': current_user['id'],
                'nombre': current_user['nombre'],
                'apellido': current_user['apellido'],
                'email': current_user['email'],
                'especialidad': current_user['especialidad'],
                'telefono': current_user.get('telefono'),
                'imagen_perfil': current_user.get('imagen_perfil'),
                'ultimo_acceso': current_user.get('ultimo_acceso'),
                'fecha_registro': current_user.get('fecha_registro')
            }
            
            return jsonify(profile), 200
            
        except Exception as e:
            logger.error(f"Error al obtener perfil: {str(e)}")
            return jsonify({'message': 'Error en el servidor'}), 500
    
    @app.route('/api/profile', methods=['PUT'])
    @token_required
    def update_profile(current_user):
        """Actualiza el perfil del usuario actual."""
        try:
            data = request.get_json()
            
            # Campos que el usuario puede actualizar
            updatable_fields = ['nombre', 'apellido', 'telefono', 'especialidad']
            update_data = {}
            
            for field in updatable_fields:
                if field in data:
                    update_data[field] = data[field]
            
            if not update_data:
                return jsonify({'message': 'No se proporcionaron datos para actualizar'}), 400
            
            # Actualizar perfil
            Profesional.update(current_user['id'], update_data)
            
            # Obtener perfil actualizado
            updated_user = Profesional.get_by_id(current_user['id'])
            
            # Filtrar campos sensibles
            profile = {
                'id': updated_user['id'],
                'nombre': updated_user['nombre'],
                'apellido': updated_user['apellido'],
                'email': updated_user['email'],
                'especialidad': updated_user['especialidad'],
                'telefono': updated_user.get('telefono'),
                'imagen_perfil': updated_user.get('imagen_perfil')
            }
            
            return jsonify({
                'message': 'Perfil actualizado con éxito',
                'profile': profile
            }), 200
            
        except Exception as e:
            logger.error(f"Error al actualizar perfil: {str(e)}")
            return jsonify({'message': 'Error en el servidor'}), 500