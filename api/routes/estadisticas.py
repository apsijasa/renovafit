from flask import jsonify, request
from . import api
from models import FichaMedica, Evaluacion, Paciente, Usuario
from auth import token_required, get_current_user
import logging
from datetime import datetime, timedelta

# Configuración de logging
logger = logging.getLogger(__name__)

@api.route('/estadisticas', methods=['GET'])
@token_required
def get_estadisticas():
    """Obtiene estadísticas generales para el dashboard."""
    try:
        # Obtener estadísticas básicas
        estadisticas = FichaMedica.get_estadisticas()
        
        return jsonify(estadisticas), 200
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        return jsonify({"message": "Error al obtener estadísticas", "error": str(e)}), 500

@api.route('/estadisticas/profesionales', methods=['GET'])
@token_required
def get_estadisticas_profesionales():
    """Obtiene estadísticas por profesional."""
    try:
        # Obtener estadísticas por profesional
        query = """
        SELECT 
            u.id, 
            u.nombre, 
            u.apellido, 
            u.especialidad,
            COUNT(DISTINCT e.id) as total_evaluaciones,
            COUNT(DISTINCT f.paciente_id) as total_pacientes
        FROM usuarios u
        LEFT JOIN evaluaciones e ON u.id = e.profesional_id AND e.activo = 1
        LEFT JOIN fichas_medicas f ON e.ficha_id = f.id AND f.activo = 1
        WHERE u.activo = 1
        GROUP BY u.id
        ORDER BY total_evaluaciones DESC
        """
        
        estadisticas = Usuario.execute_query(query)
        
        return jsonify(estadisticas), 200
    except Exception as e:
        logger.error(f"Error al obtener estadísticas por profesional: {str(e)}")
        return jsonify({"message": "Error al obtener estadísticas", "error": str(e)}), 500

@api.route('/estadisticas/tipos-cirugia', methods=['GET'])
@token_required
def get_estadisticas_tipos_cirugia():
    """Obtiene estadísticas por tipo de cirugía."""
    try:
        # Obtener estadísticas por tipo de cirugía
        query = """
        SELECT 
            JSON_UNQUOTE(JSON_EXTRACT(antecedentes_json, '$.tipo_cirugia')) as tipo_cirugia,
            COUNT(*) as total
        FROM fichas_medicas
        WHERE activo = 1
        GROUP BY JSON_UNQUOTE(JSON_EXTRACT(antecedentes_json, '$.tipo_cirugia'))
        ORDER BY total DESC
        """
        
        resultados = FichaMedica.execute_query(query)
        
        # Formatear resultados para mostrar nombres legibles
        tipos_cirugia = {
            'by_pass': 'Bypass Gástrico',
            'sleeve': 'Manga Gástrica',
            'balon': 'Balón Gástrico',
            'otro': 'Otro',
            'ninguna': 'Ninguna (Prevención)'
        }
        
        for resultado in resultados:
            if resultado['tipo_cirugia'] in tipos_cirugia:
                resultado['nombre'] = tipos_cirugia[resultado['tipo_cirugia']]
            else:
                resultado['nombre'] = 'No especificado'
        
        return jsonify(resultados), 200
    except Exception as e:
        logger.error(f"Error al obtener estadísticas por tipo de cirugía: {str(e)}")
        return jsonify({"message": "Error al obtener estadísticas", "error": str(e)}), 500

@api.route('/estadisticas/evaluaciones-mensuales', methods=['GET'])
@token_required
def get_estadisticas_evaluaciones_mensuales():
    """Obtiene estadísticas de evaluaciones por mes."""
    try:
        # Obtener parámetros
        anio = request.args.get('anio', datetime.now().year)
        
        # Obtener estadísticas de evaluaciones por mes
        query = """
        SELECT 
            MONTH(fecha) as mes,
            COUNT(*) as total
        FROM evaluaciones
        WHERE YEAR(fecha) = %s AND activo = 1
        GROUP BY MONTH(fecha)
        ORDER BY mes
        """
        
        resultados = Evaluacion.execute_query(query, (anio,))
        
        # Formatear resultados con nombres de meses
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        # Asegurar que todos los meses estén representados
        datos_completos = []
        for i in range(1, 13):
            mes_encontrado = next((r for r in resultados if r['mes'] == i), None)
            if mes_encontrado:
                mes_encontrado['nombre'] = meses[i]
                datos_completos.append(mes_encontrado)
            else:
                datos_completos.append({'mes': i, 'nombre': meses[i], 'total': 0})
        
        return jsonify(datos_completos), 200
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de evaluaciones mensuales: {str(e)}")
        return jsonify({"message": "Error al obtener estadísticas", "error": str(e)}), 500

@api.route('/estadisticas/profesional/<int:profesional_id>', methods=['GET'])
@token_required
def get_estadisticas_profesional(profesional_id):
    """Obtiene estadísticas detalladas para un profesional específico."""
    try:
        # Verificar si existe el profesional
        profesional = Usuario.get_by_id(profesional_id)
        if not profesional:
            return jsonify({"message": "Profesional no encontrado"}), 404
        
        # Obtener estadísticas básicas
        query_basicas = """
        SELECT 
            COUNT(DISTINCT e.id) as total_evaluaciones,
            COUNT(DISTINCT f.paciente_id) as total_pacientes,
            COUNT(DISTINCT CASE WHEN e.fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN e.id END) as evaluaciones_ultimo_mes,
            AVG(e.duracion_minutos) as duracion_promedio
        FROM evaluaciones e
        JOIN fichas_medicas f ON e.ficha_id = f.id AND f.activo = 1
        WHERE e.profesional_id = %s AND e.activo = 1
        """
        
        estadisticas_basicas = Evaluacion.execute_query(query_basicas, (profesional_id,))
        
        # Obtener evaluaciones por tipo
        query_tipos = """
        SELECT 
            tipo,
            COUNT(*) as total
        FROM evaluaciones
        WHERE profesional_id = %s AND activo = 1
        GROUP BY tipo
        ORDER BY total DESC
        """
        
        evaluaciones_por_tipo = Evaluacion.execute_query(query_tipos, (profesional_id,))
        
        # Obtener próximas citas
        proximas_citas = Evaluacion.get_proximas_citas(profesional_id, 14)
        
        # Combinar resultados
        resultados = {
            'profesional': {
                'id': profesional_id,
                'nombre': profesional['nombre'],
                'apellido': profesional['apellido'],
                'especialidad': profesional['especialidad']
            },
            'estadisticas': estadisticas_basicas[0] if estadisticas_basicas else {},
            'evaluaciones_por_tipo': evaluaciones_por_tipo,
            'proximas_citas': proximas_citas
        }
        
        return jsonify(resultados), 200
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del profesional {profesional_id}: {str(e)}")
        return jsonify({"message": "Error al obtener estadísticas", "error": str(e)}), 500

@api.route('/profesionales', methods=['GET'])
@token_required
def get_profesionales():
    """Obtiene la lista de profesionales para filtros y selección."""
    try:
        profesionales = Usuario.get_all()
        
        # Filtrar campos sensibles
        profesionales_filtrados = []
        for prof in profesionales:
            profesionales_filtrados.append({
                'id': prof['id'],
                'nombre': prof['nombre'],
                'apellido': prof['apellido'],
                'especialidad': prof['especialidad'],
                'rol': prof['rol']
            })
        
        return jsonify(profesionales_filtrados), 200
    except Exception as e:
        logger.error(f"Error al obtener profesionales: {str(e)}")
        return jsonify({"message": "Error al obtener profesionales", "error": str(e)}), 500