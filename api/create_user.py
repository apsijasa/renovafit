import pymysql
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import datetime
import sys

# Cargar variables de entorno
load_dotenv()

# Configuración básica de la base de datos (sin especificar la base de datos)
DB_CONFIG_BASIC = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'renovafit_user'),
    'password': os.getenv('DB_PASSWORD', 'secure_password_here'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Configuración completa de la base de datos (incluyendo la base de datos)
DB_CONFIG = {
    **DB_CONFIG_BASIC,
    'db': os.getenv('DB_NAME', 'renovafit_medical')
}

def create_database_and_schema():
    """Crea la base de datos y el esquema si no existen."""
    try:
        # Conectar a MySQL sin especificar la base de datos
        conn = pymysql.connect(**DB_CONFIG_BASIC)
        cursor = conn.cursor()
        
        # Crear la base de datos si no existe
        db_name = DB_CONFIG['db']
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Base de datos '{db_name}' creada o ya existente.")
        
        # Usar la base de datos
        cursor.execute(f"USE {db_name}")
        
        # Leer el archivo schema.sql
        schema_file_path = "../db/schema.sql"
        if not os.path.exists(schema_file_path):
            schema_file_path = "db/schema.sql"
            if not os.path.exists(schema_file_path):
                print("Error: No se encuentra el archivo schema.sql")
                return False
        
        with open(schema_file_path, 'r') as schema_file:
            schema_content = schema_file.read()
        
        # Dividir por instrucciones SQL (esto es una simplificación, podría requerir ajustes)
        # Eliminar la creación de base de datos ya que la acabamos de crear
        schema_content = schema_content.replace("CREATE DATABASE IF NOT EXISTS renovafit_medical CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;", "")
        schema_content = schema_content.replace("USE renovafit_medical;", "")
        
        # Ejecutar cada instrucción SQL
        for statement in schema_content.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        print("Esquema de base de datos creado exitosamente.")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error al crear la base de datos o el esquema: {str(e)}")
        return False

def create_professional():
    """Crea un nuevo profesional en la base de datos."""
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
    print("=== Configuración Inicial del Sistema RenovaFit ===\n")
    
    # Preguntar si se debe crear la base de datos
    create_db = input("¿Deseas crear la base de datos y el esquema? (s/n): ").lower()
    
    if create_db == 's':
        print("\nCreando base de datos y esquema...")
        if not create_database_and_schema():
            print("No se pudo crear la base de datos o el esquema. Saliendo.")
            sys.exit(1)
    
    print("\n=== Crear Nuevo Profesional RenovaFit ===\n")
    create_professional()

#para ejecutar python create_user.py