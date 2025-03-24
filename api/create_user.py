import pymysql
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import datetime

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'renovafit_user'),
    'password': os.getenv('DB_PASSWORD', 'secure_password_here'),
    'db': os.getenv('DB_NAME', 'renovafit_medical'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def create_professional():
    # Datos del nuevo profesional
    nombre = input("Nombre: ")
    apellido = input("Apellido: ")
    email = input("Email: ")
    password = input("Contraseña: ")
    especialidad = input("Especialidad: ")
    telefono = input("Teléfono: ")
    
    # Generar hash de la contraseña
    password_hash = generate_password_hash(password)
    
    try:
        # Conectar a la base de datos
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Insertar el nuevo profesional
        cursor.execute('''
            INSERT INTO profesionales (
                nombre, apellido, email, password_hash, especialidad, 
                telefono, activo, fecha_registro
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            nombre, apellido, email, password_hash, especialidad, 
            telefono, 1, datetime.datetime.now()
        ))
        
        # Obtener el ID del nuevo profesional
        profesional_id = cursor.lastrowid
        
        # Confirmar la transacción
        conn.commit()
        
        print(f"\n¡Profesional creado exitosamente! ID: {profesional_id}")
        print(f"Puedes iniciar sesión con: {email} y la contraseña que estableciste.")
        
    except Exception as e:
        print(f"Error al crear profesional: {str(e)}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    print("=== Crear Nuevo Profesional RenovaFit ===\n")
    create_professional()