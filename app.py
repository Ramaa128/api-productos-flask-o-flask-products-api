# app.py
import os
from flask import Flask, request, jsonify # jsonify es la función correcta de Flask
from marshmallow.exceptions import ValidationError # Para capturar errores de validación de Marshmallow

# Importaciones locales
from config import Config
from models import db, Producto
# Importar la CLASE ProductoSchema además de las instancias
from schemas import ma, ProductoSchema, producto_schema, productos_schema

# Inicialización de la aplicación Flask
app = Flask(__name__)
# Carga la configuración desde el objeto Config en config.py
app.config.from_object(Config)

# Crear la carpeta 'instance' si no existe. Flask busca la BD aquí.
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Inicializar extensiones con la aplicación Flask
db.init_app(app)
ma.init_app(app)

# --- Endpoints de la API (Rutas) ---

@app.route('/productos', methods=['POST'])
def crear_producto():
    """Crea un nuevo producto."""
    try:
        # Pasar la sesión de SQLAlchemy al método load cuando load_instance=True.
        nuevo_producto_obj = producto_schema.load(request.json, session=db.session)
    except ValidationError as err:
        return jsonify({"error": "Datos de entrada inválidos", "mensajes": err.messages}), 400

    # Validaciones adicionales
    if nuevo_producto_obj.precio < 0:
        return jsonify({"error": "El precio no puede ser negativo"}), 400
    if nuevo_producto_obj.stock < 0:
        return jsonify({"error": "El stock no puede ser negativo"}), 400
    
    db.session.add(nuevo_producto_obj)
    db.session.commit()

    # Usar schema.dump() para serializar y luego flask.jsonify() para la respuesta.
    datos_serializados = producto_schema.dump(nuevo_producto_obj)
    return jsonify(datos_serializados), 201

@app.route('/productos', methods=['GET'])
def obtener_productos():
    """Obtiene todos los productos."""
    todos_los_productos = Producto.query.all()
    # Para listas, productos_schema.dump() ya devuelve una lista de dicts, lista para jsonify.
    resultado = productos_schema.dump(todos_los_productos)
    return jsonify(resultado), 200

@app.route('/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    """Obtiene un producto por su ID."""
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    
    # Usar schema.dump() para serializar y luego flask.jsonify() para la respuesta.
    datos_serializados = producto_schema.dump(producto)
    return jsonify(datos_serializados), 200

@app.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    """Actualiza un producto existente."""
    producto_existente = Producto.query.get(id)
    if not producto_existente:
        return jsonify({"error": "Producto no encontrado"}), 404

    try:
        datos_json = request.json
        # Usamos la clase ProductoSchema importada para crear una instancia de validación.
        schema_para_validacion = ProductoSchema(partial=True) # Permite campos opcionales
        errores_validacion = schema_para_validacion.validate(datos_json)
        if errores_validacion:
            return jsonify({"error": "Datos de entrada inválidos", "mensajes": errores_validacion}), 400

        # Asignación manual de campos
        if 'nombre' in datos_json:
            producto_existente.nombre = datos_json['nombre']
        if 'descripcion' in datos_json: 
            producto_existente.descripcion = datos_json.get('descripcion') 
        if 'precio' in datos_json:
            precio_actualizado = datos_json['precio']
            if not isinstance(precio_actualizado, (int, float)) or precio_actualizado < 0:
                return jsonify({"error": "El precio debe ser un número no negativo"}), 400
            producto_existente.precio = precio_actualizado
        if 'stock' in datos_json:
            stock_actualizado = datos_json['stock']
            if not isinstance(stock_actualizado, int) or stock_actualizado < 0:
                return jsonify({"error": "El stock debe ser un entero no negativo"}), 400
            producto_existente.stock = stock_actualizado
            
    except ValidationError as err: # Aunque la validación manual ya se hizo, es buena práctica por si acaso.
        return jsonify({"error": "Error procesando la solicitud de actualización", "mensajes": err.messages}), 400
    except Exception as e: # Captura general para otros posibles errores durante la actualización.
        app.logger.error(f"Error inesperado al actualizar producto ID {id}: {str(e)}")
        return jsonify({"error": "Ocurrió un error inesperado al actualizar el producto."}), 500
    
    db.session.commit()

    # Usar schema.dump() para serializar y luego flask.jsonify() para la respuesta.
    datos_serializados = producto_schema.dump(producto_existente)
    return jsonify(datos_serializados), 200

@app.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    """Elimina un producto."""
    producto_a_eliminar = Producto.query.get(id)
    if not producto_a_eliminar:
        return jsonify({"error": "Producto no encontrado"}), 404

    db.session.delete(producto_a_eliminar)
    db.session.commit()
    return jsonify({"mensaje": "Producto eliminado correctamente"}), 200

# --- Manejadores de Errores Globales ---
@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    """Manejador para errores de validación de Marshmallow."""
    return jsonify({"error": "Error de validación en los datos de entrada", "mensajes": err.messages}), 400

@app.errorhandler(404)
def handle_not_found_error(err):
    """Manejador para errores 404 (Recurso no encontrado)."""
    return jsonify(error="RecursoNoEncontrado", mensaje="El recurso solicitado no fue encontrado en la API."), 404
    
@app.errorhandler(500)
def handle_internal_server_error(err):
    """Manejador para errores 500 (Error interno del servidor)."""
    # Es buena práctica loggear el error original aquí para debugging
    original_exception = err.original_exception if hasattr(err, 'original_exception') else err
    app.logger.error(f"Error interno del servidor: {original_exception}")
    return jsonify(error="ErrorInternoDelServidor", mensaje="Ha ocurrido un error inesperado en el servidor."), 500

@app.errorhandler(405)
def handle_method_not_allowed(err):
    """Manejador para errores 405 (Método no permitido)."""
    return jsonify(error="MetodoNoPermitido", mensaje="El método HTTP no está permitido para la URL solicitada."), 405

@app.errorhandler(400) 
def handle_bad_request(err):
    """Manejador para errores 400 (Solicitud incorrecta) no capturados específicamente."""
    # Evita que este manejador capture errores de ValidationError si está definido después.
    if isinstance(err, ValidationError): # No debería ocurrir si el de ValidationError está antes y es más específico
        return handle_marshmallow_validation(err)
    
    mensaje = err.description if hasattr(err, 'description') and err.description else "La solicitud es incorrecta o malformada."
    return jsonify(error="SolicitudIncorrecta", mensaje=mensaje), 400

# --- Creación de la base de datos ---
# Este bloque se ejecuta una vez al iniciar la aplicación.
# db.create_all() crea las tablas definidas en los modelos si no existen.
# Se debe ejecutar dentro de un contexto de aplicación.
with app.app_context():
    db.create_all()

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == '__main__':
    # debug=True activa el modo de depuración de Flask.
    # ¡NUNCA usar debug=True en un entorno de producción!
    app.run(debug=True)