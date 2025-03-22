# Sistema de Fichas Médicas - RenovaFit

## Descripción

Sistema de gestión de fichas médicas para RenovaFit, diseñado para que los profesionales de la salud registren y consulten información de pacientes con cirugías bariátricas, bypass gástrico o balón gástrico. El sistema permite el seguimiento completo de la atención médica, incluyendo evaluaciones de distintos especialistas, notas de evolución y alta médica.

## Arquitectura

El sistema está dividido en dos partes principales:

1. **Frontend**: Páginas HTML, CSS y JavaScript para la interfaz de usuario.
2. **Backend**: Aplicación en Python con Flask que proporciona una API RESTful y se conecta a una base de datos MySQL.

## Requisitos Previos

- Python 3.8 o superior
- MySQL 8.0 o superior
- Servidor web (Apache, Nginx, etc.) para producción
- Navegador web moderno

## Estructura de Archivos

```
/renovafit_sistema/
│
├── frontend/                      # Archivos del frontend
│   ├── index.html                 # Página principal del sitio
│   ├── login.html                 # Página de login para profesionales
│   ├── fichas-medicas.html        # Listado de fichas médicas
│   ├── ver-ficha.html             # Ver detalle de ficha médica
│   ├── nueva-ficha.html           # Formulario para crear ficha médica
│   ├── editar-ficha.html          # Formulario para editar ficha médica
│   ├── style.css                  # Estilos principales
│   ├── sistema.css                # Estilos específicos del sistema
│   └── img/                       # Imágenes y recursos
│
├── backend/                       # Aplicación del backend
│   ├── app.py                     # Aplicación principal Flask
│   ├── auth.py                    # Módulo de autenticación
│   ├── models.py                  # Modelos de datos
│   ├── routes/                    # Rutas de la API
│   │   ├── __init__.py
│   │   ├── pacientes.py
│   │   ├── fichas.py
│   │   ├── evaluaciones.py
│   │   └── estadisticas.py
│   ├── requirements.txt           # Dependencias de Python
│   └── .env                       # Variables de entorno
│
└── db/                            # Scripts de la base de datos
    └── schema.sql                 # Esquema de la base de datos
```

## Instalación y Configuración

### 1. Base de Datos

1. Crear la base de datos y usuario en MySQL:

```sql
CREATE DATABASE renovafit_medical;
CREATE USER 'renovafit_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON renovafit_medical.* TO 'renovafit_user'@'localhost';
FLUSH PRIVILEGES;
```

2. Importar el esquema de la base de datos:

```bash
mysql -u renovafit_user -p renovafit_medical < db/schema.sql
```

### 2. Backend (Python/Flask)

1. Crear un entorno virtual e instalar dependencias:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configurar variables de entorno:

```bash
# Copiar el archivo .env de ejemplo
cp .env.example .env
# Editar el archivo .env con las credenciales correctas
```

3. Iniciar el servidor de desarrollo:

```bash
flask run --host=0.0.0.0 --port=5000
```

### 3. Frontend

1. Configurar el servidor web para servir los archivos estáticos del frontend.

   **Apache (ejemplo de configuración):**

   ```apache
   <VirtualHost *:80>
       ServerName sistema.renovafit.cl
       DocumentRoot /ruta/a/renovafit_sistema/frontend
       
       # Proxy para la API
       ProxyPass /api http://localhost:5000/api
       ProxyPassReverse /api http://localhost:5000/api
       
       <Directory /ruta/a/renovafit_sistema/frontend>
           Options -Indexes +FollowSymLinks
           AllowOverride All
           Require all granted
       </Directory>
   </VirtualHost>
   ```

   **Nginx (ejemplo de configuración):**

   ```nginx
   server {
       listen 80;
       server_name sistema.renovafit.cl;
       root /ruta/a/renovafit_sistema/frontend;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       location /api {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. Asegurarse de que los archivos HTML tengan los permisos correctos:

```bash
chmod 644 frontend/*.html frontend/*.css
```

## Despliegue en Producción

Para desplegar en un entorno de producción, se recomienda:

1. Usar Gunicorn o uWSGI para servir la aplicación Flask:

```bash
# Instalar gunicorn
pip install gunicorn

# Iniciar con gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. Configurar un servicio systemd para mantener la aplicación ejecutándose:

```ini
# /etc/systemd/system/renovafit-api.service
[Unit]
Description=RenovaFit API Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/ruta/a/renovafit_sistema/backend
ExecStart=/ruta/a/renovafit_sistema/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Habilitar e iniciar el servicio:

```bash
sudo systemctl enable renovafit-api
sudo systemctl start renovafit-api
```

## Seguridad

- Usar HTTPS en producción
- Cambiar las contraseñas por defecto
- Asegurar la configuración de MySQL
- Actualizar regularmente todas las dependencias

## Acceso al Sistema

- URL del sistema: http://sistema.renovafit.cl (o la configurada en el servidor)
- Para el primer acceso, usar las credenciales precargadas:
  - Email: juan.perez@renovafit.cl
  - Contraseña: password123 (cambiar inmediatamente)

## Respaldo y Mantenimiento

- Programar copias de seguridad diarias de la base de datos
- Configurar rotación de logs para evitar llenar el disco
- Monitorear el uso de recursos del servidor

## Soporte y Contacto

Para cualquier problema o consulta, contactar al administrador del sistema:
- Email: soporte@renovafit.cl
