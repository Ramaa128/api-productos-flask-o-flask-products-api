# tests/test_app.py
import pytest
from app import app as flask_app, db # Tu aplicación Flask y la instancia de BD
from models import Producto          # CORRECCIÓN: Importar el modelo Producto

@pytest.fixture(scope='module')
def app_fixture(): # Renombrado para evitar posible confusión con 'app' de 'from app import app'
    """Configura la aplicación Flask para pruebas."""
    flask_app.config.update({
        "TESTING": True,
        # Considera usar una BD en memoria o de prueba para aislar las pruebas.
        # "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", 
        # Para este ejemplo, las pruebas modificarán la BD existente.
        # Asegúrate de que la BD se cree si no existe:
        "SQLALCHEMY_DATABASE_URI": flask_app.config["SQLALCHEMY_DATABASE_URI"], # Usar la config existente
    })

    # Crear tablas si no existen (importante si se usa una BD en memoria o una nueva)
    with flask_app.app_context():
        db.create_all()

    yield flask_app

    # Opcional: Limpieza después de todas las pruebas del módulo
    # with flask_app.app_context():
    # db.drop_all() # ¡CUIDADO! Esto borraría todas las tablas.

@pytest.fixture(scope='module')
def client(app_fixture): # Usar el fixture renombrado
    """Proporciona un cliente de pruebas para la aplicación Flask."""
    return app_fixture.test_client()

@pytest.fixture(scope='module')
def runner(app_fixture): # Usar el fixture renombrado
    """Proporciona un ejecutor de comandos CLI de Flask."""
    return app_fixture.test_cli_runner()

# --- Funciones de Prueba ---

def test_obtener_productos_vacio(client):
    """
    Prueba GET /productos cuando no hay productos.
    """
    with flask_app.app_context(): # Usar flask_app (la instancia importada) para el contexto
        # CORRECCIÓN: Forma más directa y común de borrar todos los productos
        Producto.query.delete()
        db.session.commit()

    response = client.get('/productos')
    
    assert response.status_code == 200
    assert response.json == []
    assert response.content_type == 'application/json'

def test_crear_producto(client):
    """
    Prueba POST /productos para crear un nuevo producto.
    """
    # Se recomienda limpiar la tabla o asegurar un estado conocido
    # si las pruebas pueden interferir entre sí.
    with flask_app.app_context():
        Producto.query.delete()
        db.session.commit()

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

    # Verificar que el producto existe en la base de datos
    with flask_app.app_context():
        producto_db = Producto.query.get(response_json['id'])
        assert producto_db is not None
        assert producto_db.nombre == producto_data['nombre']