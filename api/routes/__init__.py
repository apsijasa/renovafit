from flask import Blueprint

# Crear un Blueprint para las rutas de la API
api = Blueprint('api', __name__, url_prefix='/api')

# Importar las rutas después de crear el Blueprint para evitar importaciones circulares
from . import pacientes, fichas, evaluaciones, estadisticas

def init_app(app):
    """Registra todas las rutas de la API en la aplicación."""
    app.register_blueprint(api)
    return app