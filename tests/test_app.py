# tests/test_app.py
import pytest
from app import app as flask_app, db
from models import Producto

@pytest.fixture(scope='module')
def app_fixture():
    """Configura la aplicación Flask para pruebas."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": flask_app.config["SQLALCHEMY_DATABASE_URI"],
    })
    with flask_app.app_context():
        db.create_all() # Asegura que las tablas estén creadas para la sesión de prueba
    yield flask_app
    # Opcional: Limpieza después de todas las pruebas del módulo.
    # with flask_app.app_context():
    #     db.drop_all() # Borraría todas las tablas, usar con precaución

@pytest.fixture(scope='module')
def client(app_fixture):
    """Proporciona un cliente de pruebas para la aplicación Flask."""
    return app_fixture.test_client()

@pytest.fixture(scope='module')
def runner(app_fixture):
    """Proporciona un ejecutor de comandos CLI de Flask."""
    return app_fixture.test_cli_runner()

# --- Helper para limpiar la base de datos antes de ciertas pruebas ---
def limpiar_db():
    """Limpia la tabla de productos."""
    with flask_app.app_context():
        Producto.query.delete()
        db.session.commit()

# --- Funciones de Prueba ---

def test_obtener_productos_vacio(client):
    """Prueba GET /productos cuando no hay productos."""
    limpiar_db()
    response = client.get('/productos')
    assert response.status_code == 200
    assert response.json == []
    assert response.content_type == 'application/json'

def test_crear_producto(client):
    """Prueba POST /productos para crear un nuevo producto."""
    limpiar_db()
    producto_data = {
        "nombre": "Producto de Prueba",
        "descripcion": "Descripción de prueba",
        "precio": 10.99,
        "stock": 100
    }
    response = client.post('/productos', json=producto_data)
    assert response.status_code == 201
    assert response.content_type == 'application/json'
    
    response_json = response.json
    assert response_json['nombre'] == producto_data['nombre']
    assert response_json['descripcion'] == producto_data['descripcion']
    assert response_json['precio'] == producto_data['precio']
    assert response_json['stock'] == producto_data['stock']
    assert 'id' in response_json

    with flask_app.app_context():
        producto_db = db.session.get(Producto, response_json['id'])
        assert producto_db is not None
        assert producto_db.nombre == producto_data['nombre']

def test_obtener_producto_existente(client):
    """Prueba GET /productos/<id> para un producto que existe."""
    limpiar_db()
    producto_data_original = {
        "nombre": "Producto Específico",
        "descripcion": "Descripción para obtener",
        "precio": 25.50,
        "stock": 5
    }
    response_post = client.post('/productos', json=producto_data_original)
    assert response_post.status_code == 201
    producto_creado_id = response_post.json['id']

    response_get = client.get(f'/productos/{producto_creado_id}')
    
    assert response_get.status_code == 200
    assert response_get.content_type == 'application/json'
    
    response_json_get = response_get.json
    assert response_json_get['id'] == producto_creado_id
    assert response_json_get['nombre'] == producto_data_original['nombre']
    assert response_json_get['descripcion'] == producto_data_original['descripcion']
    assert response_json_get['precio'] == producto_data_original['precio']
    assert response_json_get['stock'] == producto_data_original['stock']

def test_obtener_producto_no_existente(client):
    """Prueba GET /productos/<id> para un producto que NO existe."""
    limpiar_db()
    id_no_existente = 99999 
    response = client.get(f'/productos/{id_no_existente}')
    
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    
    response_json = response.json
    assert 'error' in response_json
    assert response_json['error'] == 'Producto no encontrado'

# --- Pruebas para PUT /productos/<id> ---

def test_actualizar_producto_existente(client):
    """Prueba PUT /productos/<id> para actualizar un producto existente."""
    limpiar_db()
    producto_original_data = {
        "nombre": "Producto Original Para Actualizar",
        "descripcion": "Descripción original",
        "precio": 50.00,
        "stock": 20
    }
    response_post = client.post('/productos', json=producto_original_data)
    assert response_post.status_code == 201
    producto_id = response_post.json['id']

    datos_actualizacion = {
        "nombre": "Producto Actualizado Correctamente",
        "precio": 55.75,
        "stock": 15
    }
    response_put = client.put(f'/productos/{producto_id}', json=datos_actualizacion)
    
    assert response_put.status_code == 200
    assert response_put.content_type == 'application/json'
    
    response_json_put = response_put.json
    assert response_json_put['id'] == producto_id
    assert response_json_put['nombre'] == datos_actualizacion['nombre']
    assert response_json_put['descripcion'] == producto_original_data['descripcion']
    assert response_json_put['precio'] == datos_actualizacion['precio']
    assert response_json_put['stock'] == datos_actualizacion['stock']

    with flask_app.app_context():
        producto_db = db.session.get(Producto, producto_id)
        assert producto_db is not None
        assert producto_db.nombre == datos_actualizacion['nombre']
        assert producto_db.precio == datos_actualizacion['precio']

def test_actualizar_producto_no_existente(client):
    """Prueba PUT /productos/<id> para un producto que NO existe."""
    limpiar_db()
    id_no_existente = 99998 
    datos_actualizacion = {"nombre": "Intento Fallido de Actualización"}
    
    response = client.put(f'/productos/{id_no_existente}', json=datos_actualizacion)
    
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    assert 'error' in response.json
    assert response.json['error'] == 'Producto no encontrado'

def test_actualizar_producto_datos_invalidos(client):
    """Prueba PUT /productos/<id> con datos inválidos (ej. precio negativo)."""
    limpiar_db()
    producto_original_data = {
        "nombre": "Producto Para Actualización Inválida",
        "precio": 30.00,
        "stock": 10
    }
    response_post = client.post('/productos', json=producto_original_data)
    assert response_post.status_code == 201
    producto_id = response_post.json['id']

    datos_actualizacion_invalidos = {"precio": -5.00}
    response_put = client.put(f'/productos/{producto_id}', json=datos_actualizacion_invalidos)
    
    assert response_put.status_code == 400
    assert response_put.content_type == 'application/json'
    
    response_json = response_put.json
    assert 'error' in response_json
    assert "El precio debe ser un número no negativo" in response_json.get('error', '') or \
           "precio" in str(response_json.get('mensajes', {}))

# --- Pruebas para DELETE /productos/<id> ---

def test_eliminar_producto_existente(client):
    """Prueba DELETE /productos/<id> para eliminar un producto existente."""
    limpiar_db()
    # 1. Crear un producto de prueba
    producto_data = {
        "nombre": "Producto Para Eliminar",
        "precio": 15.00,
        "stock": 3
    }
    response_post = client.post('/productos', json=producto_data)
    assert response_post.status_code == 201
    producto_id = response_post.json['id']

    # 2. Eliminar el producto
    response_delete = client.delete(f'/productos/{producto_id}')
    assert response_delete.status_code == 200 # Tu endpoint devuelve 200 y mensaje
    assert response_delete.content_type == 'application/json'
    assert 'mensaje' in response_delete.json
    assert response_delete.json['mensaje'] == "Producto eliminado correctamente"

    # 3. Verificar que el producto ya no se puede obtener (devuelve 404)
    response_get = client.get(f'/productos/{producto_id}')
    assert response_get.status_code == 404

    # 4. (Opcional) Verificar directamente en la BD que no existe
    with flask_app.app_context():
        producto_db = db.session.get(Producto, producto_id)
        assert producto_db is None

def test_eliminar_producto_no_existente(client):
    """Prueba DELETE /productos/<id> para un producto que NO existe."""
    limpiar_db()
    id_no_existente = 99997 
    
    response_delete = client.delete(f'/productos/{id_no_existente}')
    
    assert response_delete.status_code == 404
    assert response_delete.content_type == 'application/json'
    assert 'error' in response_delete.json
    assert response_delete.json['error'] == 'Producto no encontrado'