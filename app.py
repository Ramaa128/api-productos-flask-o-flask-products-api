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
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "title": "API de Productos - Flask", # Título para la página de Swagger UI
    "version": "1.0.0", # Versión de tu API
    "description": "Una API sencilla para gestionar un catálogo de productos, construida con Flask.",
    # Puedes añadir más configuraciones de Swagger aquí si lo deseas
    # "uiversion": 3 # Para usar Swagger UI 3.x
}

# Definiciones de esquemas para Swagger. Flasgger intentará inferir de Marshmallow,
# pero definir explícitamente puede dar más control o solucionar problemas de inferencia.
# Si la inferencia de '#/definitions/Producto' funciona bien, no necesitas definirlo aquí.
# Si no, puedes añadirlo al template.
swagger_template = {
    "info": {
        "title": swagger_config.get("title"),
        "version": swagger_config.get("version"),
        "description": swagger_config.get("description"),
        # "contact": {
        #     "responsibleOrganization": "Tu Nombre/Organización",
        #     "responsibleDeveloper": "Tu Nombre",
        #     "email": "tu_correo@example.com",
        #     "url": "tu_website.com",
        # },
        # "termsOfService": "tus_terminos_de_servicio_url",
    },
    # "host": "localhost:5000",  # O el host donde se despliega
    # "basePath": "/",  # El prefijo base para todos los endpoints de la API
    "schemes": [
        "http",
        # "https" # Si soporta HTTPS
    ],
    "definitions": {
        "Producto": { # Esta es la definición que referenciamos con $ref: '#/definitions/Producto'
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "ID único del producto.", "readOnly": True},
                "nombre": {"type": "string", "description": "Nombre del producto.", "example": "Teclado Inalámbrico"},
                "descripcion": {"type": "string", "description": "Descripción del producto.", "example": "Teclado ergonómico con Bluetooth"},
                "precio": {"type": "number", "format": "float", "description": "Precio del producto.", "example": 49.99},
                "stock": {"type": "integer", "description": "Stock del producto.", "example": 120}
            }
        },
        "ErrorRespuesta": { # Un esquema genérico para respuestas de error
            "type": "object",
            "properties": {
                "error": {"type": "string", "description": "Clave del error o descripción corta."},
                "mensaje": {"type": "string", "description": "Mensaje detallado del error."}
            }
        },
        "ErrorValidacion": {
             "type": "object",
             "properties": {
                 "error": {"type": "string", "example": "Datos de entrada inválidos"},
                 "mensajes": {"type": "object", "description": "Detalles de los errores de validación por campo."}
             }
        }
    }
}

# Inicializar Flasgger con la aplicación, la configuración y el template
swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Carga la configuración de la aplicación
app.config.from_object(Config)

# Crear la carpeta 'instance' si no existe
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Inicializar extensiones
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
    description: Este endpoint permite la creación de un nuevo producto proporcionando sus detalles.
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
          # Referencia al esquema Producto, pero sin el ID (ya que es para creación)
          # O puedes definir un esquema específico para la entrada aquí.
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
        description: Producto creado exitosamente.
        schema:
          $ref: '#/definitions/Producto' 
      400:
        description: Error de validación en los datos de entrada.
        schema:
          $ref: '#/definitions/ErrorValidacion'
    """
    try:
        nuevo_producto_obj = producto_schema.load(request.json, session=db.session)
    except ValidationError as err:
        return jsonify({"error": "Datos de entrada inválidos", "mensajes": err.messages}), 400

    if nuevo_producto_obj.precio < 0:
        return jsonify({"error": "El precio no puede ser negativo"}), 400 # Podría ser un esquema ErrorRespuesta
    if nuevo_producto_obj.stock < 0:
        return jsonify({"error": "El stock no puede ser negativo"}), 400 # Podría ser un esquema ErrorRespuesta
    
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
    description: Devuelve una lista de todos los productos almacenados.
    produces:
      - application/json
    responses:
      200:
        description: Una lista de productos.
        schema:
          type: array
          items:
            $ref: '#/definitions/Producto' 
    """
    todos_los_productos = Producto.query.all() # Considerar paginación para APIs grandes
    resultado = productos_schema.dump(todos_los_productos)
    return jsonify(resultado), 200

@app.route('/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    """
    Obtiene un producto específico por su ID.
    ---
    tags:
      - Productos
    summary: Obtiene un producto por ID.
    description: Devuelve los detalles de un producto específico si se encuentra por su ID.
    produces:
      - application/json
    parameters:
      - name: id
        in: path
        description: ID del producto a obtener.
        required: true
        type: integer
        format: int64 
    responses:
      200:
        description: Detalles del producto encontrado.
        schema:
          $ref: '#/definitions/Producto'
      404:
        description: Producto no encontrado.
        schema:
          # Usando el esquema de error genérico que definimos
          $ref: '#/definitions/ErrorRespuesta' 
    """
    producto = db.session.get(Producto, id)
    if not producto:
        # Para que coincida con el esquema ErrorRespuesta del manejador global
        return jsonify({"error": "RecursoNoEncontrado", "mensaje": "Producto no encontrado."}), 404
    
    datos_serializados = producto_schema.dump(producto)
    return jsonify(datos_serializados), 200

@app.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    """
    Actualiza un producto existente por su ID.
    Permite actualizaciones parciales; solo los campos proporcionados en el cuerpo
    de la solicitud serán actualizados.
    ---
    tags:
      - Productos
    summary: Actualiza un producto existente.
    description: Actualiza los detalles de un producto existente identificado por su ID. Solo los campos incluidos en el cuerpo de la solicitud serán modificados.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: id
        in: path
        description: ID del producto a actualizar.
        required: true
        type: integer
        format: int64
      - name: body
        in: body
        description: Campos del producto a actualizar.
        required: true
        schema:
          # Para PUT, los campos son opcionales. Se puede referenciar Producto
          # o listar explícitamente las propiedades como opcionales.
          type: object
          properties:
            nombre:
              type: string
              description: Nuevo nombre del producto.
              example: "Laptop Ultra Pro Max"
            descripcion:
              type: string
              description: Nueva descripción del producto.
              example: "La mejor laptop, ahora con más RAM."
            precio:
              type: number
              format: float
              description: Nuevo precio del producto.
              example: 2199.00
            stock:
              type: integer
              description: Nuevo stock del producto.
              example: 45
    responses:
      200:
        description: Producto actualizado exitosamente. Devuelve el producto actualizado.
        schema:
          $ref: '#/definitions/Producto'
      400:
        description: Error de validación en los datos de entrada o datos inválidos.
        schema:
          $ref: '#/definitions/ErrorValidacion' # O ErrorRespuesta si es un error de lógica de negocio
      404:
        description: Producto no encontrado.
        schema:
          $ref: '#/definitions/ErrorRespuesta'
    """
    producto_existente = db.session.get(Producto, id)
    if not producto_existente:
        return jsonify({"error": "RecursoNoEncontrado", "mensaje": "Producto no encontrado para actualizar."}), 404

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
                return jsonify({"error": "ValorInválido", "mensaje": "El precio debe ser un número no negativo"}), 400
            producto_existente.precio = precio_actualizado
        if 'stock' in datos_json:
            stock_actualizado = datos_json['stock']
            if not isinstance(stock_actualizado, int) or stock_actualizado < 0:
                return jsonify({"error": "ValorInválido", "mensaje": "El stock debe ser un entero no negativo"}), 400
            producto_existente.stock = stock_actualizado
            
    except Exception as e: 
        app.logger.error(f"Error inesperado al actualizar producto ID {id}: {str(e)}")
        return jsonify({"error": "ErrorInternoDelServidor", "mensaje": "Ocurrió un error inesperado al actualizar el producto."}), 500
    
    db.session.commit()
    datos_serializados = producto_schema.dump(producto_existente)
    return jsonify(datos_serializados), 200

@app.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    """
    Elimina un producto específico por su ID.
    ---
    tags:
      - Productos
    summary: Elimina un producto por ID.
    description: Elimina permanentemente un producto de la base de datos identificado por su ID.
    produces:
      - application/json
    parameters:
      - name: id
        in: path
        description: ID del producto a eliminar.
        required: true
        type: integer
        format: int64
    responses:
      200:
        description: Producto eliminado exitosamente.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Producto eliminado correctamente"
      404:
        description: Producto no encontrado.
        schema:
          $ref: '#/definitions/ErrorRespuesta'
    """
    producto_a_eliminar = db.session.get(Producto, id)
    if not producto_a_eliminar:
        return jsonify({"error": "RecursoNoEncontrado", "mensaje": "Producto no encontrado para eliminar."}), 404

    db.session.delete(producto_a_eliminar)
    db.session.commit()
    return jsonify({"mensaje": "Producto eliminado correctamente"}), 200

# --- Manejadores de Errores Globales ---
@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    # Para que coincida con el esquema ErrorValidacion
    return jsonify({"error": "Datos de entrada inválidos", "mensajes": err.messages}), 400

@app.errorhandler(404)
def handle_not_found_error(err):
    # Para que coincida con el esquema ErrorRespuesta
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
    # Para que coincida con el esquema ErrorRespuesta
    return jsonify(error="SolicitudIncorrecta", mensaje=mensaje), 400

# --- Creación de la base de datos ---
with app.app_context():
    db.create_all()

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == '__main__':
    app.run(debug=True)