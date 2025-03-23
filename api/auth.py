import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app

def generate_token(user_id, email, secret_key, expiration_delta):
    """
    Genera un token JWT para el usuario.
    
    Args:
        user_id: ID del usuario
        email: Correo electrónico del usuario
        secret_key: Clave secreta para firmar el token
        expiration_delta: Segundos de validez del token
        
    Returns:
        str: Token JWT generado
    """
    payload = {
        'id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_delta)
    }
    
    return jwt.encode(payload, secret_key, algorithm="HS256")

def token_required(f):
    """
    Decorador para proteger rutas que requieren autenticación.
    
    Este decorador verifica que el token JWT sea válido y que el usuario exista en la base de datos.
    La función decorada recibirá como primer argumento los datos del usuario actual.
    """
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
            from app import get_db_connection
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            
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