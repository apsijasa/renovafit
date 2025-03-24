from flask import request, jsonify
from . import api
from models import Paciente
from auth import token_required
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

@api.route('/pacientes', methods=['GET'])
@token_required
def get_pacientes():
    """Obtiene todos los pacientes o filtra por término de búsqueda."""
    try:
        search_term = request.args.get('search', '')
        
        if search_term:
            pacientes = Paciente.search(search_term)
        else:
            pacientes = Paciente.get_all()
            
        return jsonify(pacientes), 200
    except Exception as e:
        logger.error(f"Error al obtener pacientes: {str(e)}")
        return jsonify({"message": "Error al obtener pacientes", "error": str(e)}), 500

@api.route('/pacientes/<int:paciente_id>', methods=['GET'])
@token_required
def get_paciente(paciente_id):
    """Obtiene un paciente por su ID."""
    try:
        paciente = Paciente.get_by_id(paciente_id)
        
        if not paciente:
            return jsonify({"message": "Paciente no encontrado"}), 404
            
        return jsonify(paciente), 200
    except Exception as e:
        logger.error(f"Error al obtener paciente {paciente_id}: {str(e)}")
        return jsonify({"message": "Error al obtener paciente", "error": str(e)}), 500

@api.route('/pacientes', methods=['POST'])
@token_required
def create_paciente():
    """Crea un nuevo paciente."""
    try:
        data = request.get_json()
        
        # Validación básica
        if not data.get('nombre') or not data.get('apellido'):
            return jsonify({"message": "Nombre y apellido son obligatorios"}), 400
        
        # Crear paciente
        paciente_id = Paciente.create(data)
        
        # Obtener el paciente recién creado
        paciente = Paciente.get_by_id(paciente_id)
        
        return jsonify({"message": "Paciente creado con éxito", "id": paciente_id, **paciente}), 201
    except Exception as e:
        logger.error(f"Error al crear paciente: {str(e)}")
        return jsonify({"message": "Error al crear paciente", "error": str(e)}), 500

@api.route('/pacientes/<int:paciente_id>', methods=['PUT'])
@token_required
def update_paciente(paciente_id):
    """Actualiza los datos de un paciente."""
    try:
        data = request.get_json()
        
        # Verificar si el paciente existe
        paciente = Paciente.get_by_id(paciente_id)
        if not paciente:
            return jsonify({"message": "Paciente no encontrado"}), 404
        
        # Actualizar paciente
        Paciente.update(paciente_id, data)
        
        # Obtener el paciente actualizado
        paciente_actualizado = Paciente.get_by_id(paciente_id)
        
        return jsonify({"message": "Paciente actualizado con éxito", **paciente_actualizado}), 200
    except Exception as e:
        logger.error(f"Error al actualizar paciente {paciente_id}: {str(e)}")
        return jsonify({"message": "Error al actualizar paciente", "error": str(e)}), 500

@api.route('/pacientes/<int:paciente_id>', methods=['DELETE'])
@token_required
def delete_paciente(paciente_id):
    """Elimina un paciente (borrado lógico)."""
    try:
        # Verificar si el paciente existe
        paciente = Paciente.get_by_id(paciente_id)
        if not paciente:
            return jsonify({"message": "Paciente no encontrado"}), 404
        
        # Eliminar paciente (borrado lógico)
        Paciente.delete(paciente_id)
        
        return jsonify({"message": "Paciente eliminado con éxito"}), 200
    except Exception as e:
        logger.error(f"Error al eliminar paciente {paciente_id}: {str(e)}")
        return jsonify({"message": "Error al eliminar paciente", "error": str(e)}), 500