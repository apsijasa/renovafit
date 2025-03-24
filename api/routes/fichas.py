from flask import request, jsonify
from . import api
from models import FichaMedica, Paciente
from auth import token_required
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

@api.route('/fichas', methods=['GET'])
@token_required
def get_fichas():
    """Obtiene todas las fichas médicas o filtra según parámetros."""
    try:
        # Obtener parámetros de búsqueda
        search_term = request.args.get('search', '')
        
        # Filtros adicionales
        filters = {}
        for param in ['tipo_cirugia', 'profesional_id', 'fecha_desde', 'fecha_hasta']:
            if param in request.args and request.args[param]:
                filters[param] = request.args[param]
        
        # Buscar fichas
        fichas = FichaMedica.search(search_term, filters) if search_term or filters else FichaMedica.get_all()
            
        return jsonify(fichas), 200
    except Exception as e:
        logger.error(f"Error al obtener fichas médicas: {str(e)}")
        return jsonify({"message": "Error al obtener fichas médicas", "error": str(e)}), 500

@api.route('/fichas/<int:ficha_id>', methods=['GET'])
@token_required
def get_ficha(ficha_id):
    """Obtiene una ficha médica por su ID."""
    try:
        ficha = FichaMedica.get_by_id(ficha_id)
        
        if not ficha:
            return jsonify({"message": "Ficha médica no encontrada"}), 404
            
        return jsonify(ficha), 200
    except Exception as e:
        logger.error(f"Error al obtener ficha médica {ficha_id}: {str(e)}")
        return jsonify({"message": "Error al obtener ficha médica", "error": str(e)}), 500

@api.route('/fichas', methods=['POST'])
@token_required
def create_ficha():
    """Crea una nueva ficha médica."""
    try:
        data = request.get_json()
        
        # Validación básica
        if not data.get('paciente_id') or not data.get('fecha_ingreso') or not data.get('motivo_consulta'):
            return jsonify({"message": "Paciente, fecha de ingreso y motivo de consulta son obligatorios"}), 400
        
        # Verificar si existe el paciente
        paciente = Paciente.get_by_id(data['paciente_id'])
        if not paciente:
            return jsonify({"message": "El paciente especificado no existe"}), 404
        
        # Crear ficha médica
        ficha_id = FichaMedica.create(data)
        
        # Obtener la ficha recién creada
        ficha = FichaMedica.get_by_id(ficha_id)
        
        return jsonify({"message": "Ficha médica creada con éxito", "id": ficha_id}), 201
    except ValueError as e:
        logger.error(f"Error de validación al crear ficha médica: {str(e)}")
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear ficha médica: {str(e)}")
        return jsonify({"message": "Error al crear ficha médica", "error": str(e)}), 500

@api.route('/fichas/<int:ficha_id>', methods=['PUT'])
@token_required
def update_ficha(ficha_id):
    """Actualiza una ficha médica."""
    try:
        data = request.get_json()
        
        # Verificar si existe la ficha
        ficha = FichaMedica.get_by_id(ficha_id)
        if not ficha:
            return jsonify({"message": "Ficha médica no encontrada"}), 404
        
        # Actualizar ficha
        FichaMedica.update(ficha_id, data)
        
        return jsonify({"message": "Ficha médica actualizada con éxito"}), 200
    except ValueError as e:
        logger.error(f"Error de validación al actualizar ficha médica {ficha_id}: {str(e)}")
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar ficha médica {ficha_id}: {str(e)}")
        return jsonify({"message": "Error al actualizar ficha médica", "error": str(e)}), 500

@api.route('/fichas/<int:ficha_id>', methods=['DELETE'])
@token_required
def delete_ficha(ficha_id):
    """Elimina una ficha médica (borrado lógico)."""
    try:
        # Verificar si existe la ficha
        ficha = FichaMedica.get_by_id(ficha_id)
        if not ficha:
            return jsonify({"message": "Ficha médica no encontrada"}), 404
        
        # Eliminar ficha (borrado lógico)
        FichaMedica.delete(ficha_id)
        
        return jsonify({"message": "Ficha médica eliminada con éxito"}), 200
    except Exception as e:
        logger.error(f"Error al eliminar ficha médica {ficha_id}: {str(e)}")
        return jsonify({"message": "Error al eliminar ficha médica", "error": str(e)}), 500

@api.route('/pacientes/<int:paciente_id>/fichas', methods=['GET'])
@token_required
def get_fichas_paciente(paciente_id):
    """Obtiene todas las fichas médicas de un paciente."""
    try:
        # Verificar si existe el paciente
        paciente = Paciente.get_by_id(paciente_id)
        if not paciente:
            return jsonify({"message": "Paciente no encontrado"}), 404
        
        # Filtrar fichas por paciente
        filters = {'paciente_id': paciente_id}
        fichas = FichaMedica.search(None, filters)
            
        return jsonify(fichas), 200
    except Exception as e:
        logger.error(f"Error al obtener fichas del paciente {paciente_id}: {str(e)}")
        return jsonify({"message": "Error al obtener fichas médicas", "error": str(e)}), 500