# tests/test_app.py
import pytest
from app import app as flask_app # Importa tu instancia de la aplicación Flask
from app import db # Importa tu instancia de la base de datos

@pytest.fixture(scope='module')
def app():
    """Configura la aplicación Flask para pruebas."""
    # Configurar la app para un entorno de pruebas
    flask_app.config.update({
        "TESTING": True,
        # Usar una base de datos en memoria para las pruebas o una BD de prueba separada
        # Para simplicidad, podemos seguir usando la misma configuración de SQLite por ahora,
        # pero idealmente se usaría una BD separada o en memoria para evitar interferencias.
        # "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # Ejemplo para BD en memoria
    })

    # Aquí podrías añadir lógica para crear tablas de prueba, poblar datos iniciales, etc.
    # si no quieres que las pruebas dependan de la BD principal.
    # Por ahora, asumimos que db.create_all() en app.py ya creó las tablas.

    yield flask_app # Proporciona la app a las pruebas

    # Código de limpieza después de que todas las pruebas en el módulo hayan corrido (opcional)
    # Ejemplo: limpiar la base de datos de prueba
    # with flask_app.app_context():
    #     db.drop_all() # ¡Cuidado si no estás usando una BD de prueba separada!

@pytest.fixture(scope='module')
def client(app):
    """Proporciona un cliente de pruebas para la aplicación Flask."""
    return app.test_client()

@pytest.fixture(scope='module')
def runner(app):
    """Proporciona un ejecutor de comandos CLI de Flask (si lo necesitaras)."""
    return app.test_cli_runner()

# --- ¡Aquí comenzarán nuestras funciones de prueba! ---

def test_obtener_productos_vacio(client):
    """
    Prueba GET /productos cuando no hay productos en la base de datos.
    Debería devolver una lista vacía y un estado 200 OK.
    """
    # Asegurémonos de que la base de datos esté limpia para esta prueba específica
    # (Esto es un ejemplo, una mejor gestión de la BD de prueba es más avanzada)
    with flask_app.app_context():
        db.session.query(flask_app.extensions['sqlalchemy'].models_committed.get('Producto')).delete()
        db.session.commit()

    response = client.get('/productos')
    
    assert response.status_code == 200
    assert response.json == [] # Esperamos una lista JSON vacía
    assert response.content_type == 'application/json'

def test_crear_producto(client):
    """
    Prueba POST /productos para crear un nuevo producto.
    """
    producto_data = {
        "nombre": "Producto de Prueba",
        "descripcion": "Descripción de prueba",
        "precio": 10.99,
        "stock": 100
    }
    response = client.post('/productos', json=producto_data)
    
    assert response.status_code == 201 # 201 Created
    assert response.content_type == 'application/json'
    
    # Verificar que los datos devueltos coincidan (excepto el ID que es autogenerado)
    response_json = response.json
    assert response_json['nombre'] == producto_data['nombre']
    assert response_json['descripcion'] == producto_data['descripcion']
    assert response_json['precio'] == producto_data['precio']
    assert response_json['stock'] == producto_data['stock']
    assert 'id' in response_json # El ID debería estar presente

    # (Opcional) Verificar que el producto se guardó en la BD
    # from models import Producto
    # with flask_app.app_context():
    #     producto_db = Producto.query.get(response_json['id'])
    #     assert producto_db is not None
    #     assert producto_db.nombre == producto_data['nombre']