# app.py
import os
from flask import Flask, request, jsonify
from marshmallow.exceptions import ValidationError
from flasgger import Swagger # Importar Swagger

# Importaciones locales
from config import Config
from models import db, Producto
from schemas import ma, ProductoSchema, producto_schema, productos_schema

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Configuración básica de Swagger/Flasgger
# Puedes personalizar esto mucho más según la documentación de Flasgger.
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1', # Nombre del endpoint para la especificación
            "route": '/apispec_1.json', # Ruta donde se servirá la especificación JSON
            "rule_filter": lambda rule: True,  # Incluir todas las reglas (endpoints)
            "model_filter": lambda tag: True,  # Incluir todos los modelos/tags
        }
    ],
    "static_url_path": "/flasgger_static", # Ruta para los archivos estáticos de Swagger UI
    "swagger_ui": True, # Habilitar Swagger UI
    "specs_route": "/apidocs/" # Ruta para acceder a Swagger UI
}

# Inicializar Flasgger con la aplicación y la configuración
swagger = Swagger(app, config=swagger_config)

# Carga la configuración de la aplicación desde el objeto Config
app.config.from_object(Config)

# Crear la carpeta 'instance' si no existe
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Inicializar extensiones con la aplicación Flask
db.init_app(app)
ma.init_app(app)

# --- Endpoints de la API (Rutas) ---

@app.route('/productos', methods=['POST'])
def crear_producto():
    """
    Crea un nuevo producto en la base de datos.
    ---
    tags:
      - Productos
    summary: Crea un nuevo producto.
    description: Este endpoint permite la creación de un nuevo producto proporcionando sus detalles en el cuerpo de la solicitud.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        description: Objeto Producto que necesita ser añadido.
        schema:
          type: object
          required:
            - nombre
            - precio
            - stock
          properties:
            nombre:
              type: string
              description: Nombre del producto.
              example: "Laptop Gamer Pro"
            descripcion:
              type: string
              description: Descripción detallada del producto (opcional).
              example: "Laptop con RTX 4090 y 32GB RAM"
            precio:
              type: number
              format: float
              description: Precio del producto.
              example: 1999.99
            stock:
              type: integer
              description: Cantidad de unidades en stock.
              example: 50
    responses:
      201:
        description: Producto creado exitosamente. Devuelve el producto creado.
        schema:
          # Flasgger intentará inferir esto de tu ProductoSchema de Marshmallow
          $ref: '#/definitions/Producto' 
      400:
        description: Error de validación en los datos de entrada.
        # Puedes definir un esquema 'ErrorValidacion' o usar uno genérico
        schema:
          type: object
          properties:
            error: 
              type: string
              example: "Datos de entrada inválidos"
            mensajes:
              type: object 
              example: {"nombre": ["Missing data for required field."]}
    """
    try:
        nuevo_producto_obj = producto_schema.load(request.json, session=db.session)
    except ValidationError as err:
        return jsonify({"error": "Datos de entrada inválidos", "mensajes": err.messages}), 400

    if nuevo_producto_obj.precio < 0:
        return jsonify({"error": "El precio no puede ser negativo"}), 400
    if nuevo_producto_obj.stock < 0:
        return jsonify({"error": "El stock no puede ser negativo"}), 400
    
    db.session.add(nuevo_producto_obj)
    db.session.commit()

    datos_serializados = producto_schema.dump(nuevo_producto_obj)
    return jsonify(datos_serializados), 201

@app.route('/productos', methods=['GET'])
def obtener_productos():
    """
    Obtiene una lista de todos los productos.
    ---
    tags:
      - Productos
    summary: Obtiene todos los productos.
    description: Devuelve una lista de todos los productos almacenados en la base de datos.
    produces:
      - application/json
    responses:
      200:
        description: Una lista de productos.
        schema:
          type: array
          items:
            # Flasgger intentará inferir esto de tu ProductoSchema de Marshmallow
            $ref: '#/definitions/Producto' 
    """
    todos_los_productos = Producto.query.all()
    resultado = productos_schema.dump(todos_los_productos)
    return jsonify(resultado), 200

@app.route('/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    # TODO: Añadir docstring YAML para Flasgger
    producto = db.session.get(Producto, id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    
    datos_serializados = producto_schema.dump(producto)
    return jsonify(datos_serializados), 200

@app.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    # TODO: Añadir docstring YAML para Flasgger
    producto_existente = db.session.get(Producto, id)
    if not producto_existente:
        return jsonify({"error": "Producto no encontrado"}), 404

    try:
        datos_json = request.json
        schema_validador_parcial = ProductoSchema(
            partial=True, 
            session=db.session, 
            unknown='EXCLUDE' 
        )
        try:
            schema_validador_parcial.load(datos_json) 
        except ValidationError as err:
            return jsonify({"error": "Datos de entrada inválidos", "mensajes": err.messages}), 400

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
            
    except Exception as e: 
        app.logger.error(f"Error inesperado al actualizar producto ID {id}: {str(e)}")
        return jsonify({"error": "Ocurrió un error inesperado al actualizar el producto."}), 500
    
    db.session.commit()
    datos_serializados = producto_schema.dump(producto_existente)
    return jsonify(datos_serializados), 200

@app.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    # TODO: Añadir docstring YAML para Flasgger
    producto_a_eliminar = db.session.get(Producto, id)
    if not producto_a_eliminar:
        return jsonify({"error": "Producto no encontrado"}), 404

    db.session.delete(producto_a_eliminar)
    db.session.commit()
    return jsonify({"mensaje": "Producto eliminado correctamente"}), 200

# --- Manejadores de Errores Globales ---
@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify({"error": "Error de validación en los datos de entrada", "mensajes": err.messages}), 400

@app.errorhandler(404)
def handle_not_found_error(err):
    return jsonify(error="RecursoNoEncontrado", mensaje="El recurso solicitado no fue encontrado en la API."), 404
    
@app.errorhandler(500)
def handle_internal_server_error(err):
    original_exception = err.original_exception if hasattr(err, 'original_exception') else err
    app.logger.error(f"Error interno del servidor: {original_exception}")
    return jsonify(error="ErrorInternoDelServidor", mensaje="Ha ocurrido un error inesperado en el servidor."), 500

@app.errorhandler(405)
def handle_method_not_allowed(err):
    return jsonify(error="MetodoNoPermitido", mensaje="El método HTTP no está permitido para la URL solicitada."), 405

@app.errorhandler(400) 
def handle_bad_request(err):
    if isinstance(err, ValidationError):
        return handle_marshmallow_validation(err)
    mensaje = err.description if hasattr(err, 'description') and err.description else "La solicitud es incorrecta o malformada."
    return jsonify(error="SolicitudIncorrecta", mensaje=mensaje), 400

# --- Creación de la base de datos ---
with app.app_context():
    db.create_all()

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == '__main__':
    app.run(debug=True)