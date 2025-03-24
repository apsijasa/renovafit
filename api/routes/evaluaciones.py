from flask import request, jsonify
from . import api
from models import Evaluacion, FichaMedica, Usuario
from auth import token_required, get_current_user
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

@api.route('/evaluaciones/<int:evaluacion_id>', methods=['GET'])
@token_required
def get_evaluacion(evaluacion_id):
    """Obtiene una evaluación por su ID."""
    try:
        evaluacion = Evaluacion.get_by_id(evaluacion_id)
        
        if not evaluacion:
            return jsonify({"message": "Evaluación no encontrada"}), 404
            
        return jsonify(evaluacion), 200
    except Exception as e:
        logger.error(f"Error al obtener evaluación {evaluacion_id}: {str(e)}")
        return jsonify({"message": "Error al obtener evaluación", "error": str(e)}), 500

@api.route('/fichas/<int:ficha_id>/evaluaciones', methods=['GET'])
@token_required
def get_evaluaciones_ficha(ficha_id):
    """Obtiene todas las evaluaciones de una ficha médica."""
    try:
        # Verificar si existe la ficha
        ficha = FichaMedica.get_by_id(ficha_id)
        if not ficha:
            return jsonify({"message": "Ficha médica no encontrada"}), 404
        
        # Obtener evaluaciones
        evaluaciones = Evaluacion.get_by_ficha(ficha_id)
            
        return jsonify(evaluaciones), 200
    except Exception as e:
        logger.error(f"Error al obtener evaluaciones de la ficha {ficha_id}: {str(e)}")
        return jsonify({"message": "Error al obtener evaluaciones", "error": str(e)}), 500

@api.route('/evaluaciones', methods=['POST'])
@token_required
def create_evaluacion():
    """Crea una nueva evaluación."""
    try:
        data = request.get_json()
        
        # Validación básica
        if not data.get('ficha_id') or not data.get('fecha'):
            return jsonify({"message": "Ficha médica y fecha son obligatorios"}), 400
        
        # Si no se proporciona profesional_id, usar el usuario actual
        if not data.get('profesional_id'):
            current_user = get_current_user()
            data['profesional_id'] = current_user['id']
        
        # Verificar si existe la ficha
        ficha = FichaMedica.get_by_id(data['ficha_id'])
        if not ficha:
            return jsonify({"message": "La ficha médica especificada no existe"}), 404
        
        # Verificar si existe el profesional
        profesional = Usuario.get_by_id(data['profesional_id'])
        if not profesional:
            return jsonify({"message": "El profesional especificado no existe"}), 404
        
        # Crear evaluación
        evaluacion_id = Evaluacion.create(data)
        
        # Obtener la evaluación recién creada
        evaluacion = Evaluacion.get_by_id(evaluacion_id)
        
        return jsonify({
            "message": "Evaluación creada con éxito", 
            "id": evaluacion_id,
            "evaluacion": evaluacion
        }), 201
    except ValueError as e:
        logger.error(f"Error de validación al crear evaluación: {str(e)}")
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear evaluación: {str(e)}")
        return jsonify({"message": "Error al crear evaluación", "error": str(e)}), 500

@api.route('/evaluaciones/<int:evaluacion_id>', methods=['PUT'])
@token_required
def update_evaluacion(evaluacion_id):
    """Actualiza una evaluación."""
    try:
        data = request.get_json()
        
        # Verificar si existe la evaluación
        evaluacion = Evaluacion.get_by_id(evaluacion_id)
        if not evaluacion:
            return jsonify({"message": "Evaluación no encontrada"}), 404
        
        # Actualizar evaluación
        Evaluacion.update(evaluacion_id, data)
        
        # Obtener la evaluación actualizada
        evaluacion_actualizada = Evaluacion.get_by_id(evaluacion_id)
        
        return jsonify({
            "message": "Evaluación actualizada con éxito",
            "evaluacion": evaluacion_actualizada
        }), 200
    except ValueError as e:
        logger.error(f"Error de validación al actualizar evaluación {evaluacion_id}: {str(e)}")
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar evaluación {evaluacion_id}: {str(e)}")
        return jsonify({"message": "Error al actualizar evaluación", "error": str(e)}), 500

@api.route('/evaluaciones/<int:evaluacion_id>', methods=['DELETE'])
@token_required
def delete_evaluacion(evaluacion_id):
    """Elimina una evaluación (borrado lógico)."""
    try:
        # Verificar si existe la evaluación
        evaluacion = Evaluacion.get_by_id(evaluacion_id)
        if not evaluacion:
            return jsonify({"message": "Evaluación no encontrada"}), 404
        
        # Eliminar evaluación (borrado lógico)
        Evaluacion.delete(evaluacion_id)
        
        return jsonify({"message": "Evaluación eliminada con éxito"}), 200
    except Exception as e:
        logger.error(f"Error al eliminar evaluación {evaluacion_id}: {str(e)}")
        return jsonify({"message": "Error al eliminar evaluación", "error": str(e)}), 500

@api.route('/agenda', methods=['GET'])
@token_required
def get_agenda():
    """Obtiene la agenda de próximas citas para el usuario actual o para un profesional específico."""
    try:
        # Obtener parámetros
        profesional_id = request.args.get('profesional_id')
        dias = int(request.args.get('dias', 7))
        
        # Si no se especifica profesional, usar el usuario actual
        if not profesional_id:
            current_user = get_current_user()
            profesional_id = current_user['id']
        
        # Obtener próximas citas
        citas = Evaluacion.get_proximas_citas(profesional_id, dias)
            
        return jsonify(citas), 200
    except Exception as e:
        logger.error(f"Error al obtener agenda: {str(e)}")
        return jsonify({"message": "Error al obtener agenda", "error": str(e)}), 500