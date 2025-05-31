# tests/test_app.py
import pytest
from app import app as flask_app, db # Tu aplicación Flask y la instancia de BD
from models import Producto          # Modelo para interactuar con la BD en pruebas

@pytest.fixture(scope='module')
def app_fixture(): # Renombrado para evitar posible confusión
    """Configura la aplicación Flask para pruebas."""
    flask_app.config.update({
        "TESTING": True,
        # Usar la configuración de URI de la base de datos existente
        "SQLALCHEMY_DATABASE_URI": flask_app.config["SQLALCHEMY_DATABASE_URI"], 
    })

    # Asegurar que las tablas se creen dentro del contexto de la aplicación de prueba
    with flask_app.app_context():
        db.create_all()

    yield flask_app

    # Opcional: Limpieza después de todas las pruebas del módulo.
    # Considera si es necesario para tu estrategia de pruebas.
    # with flask_app.app_context():
    #     db.drop_all()

@pytest.fixture(scope='module')
def client(app_fixture):
    """Proporciona un cliente de pruebas para la aplicación Flask."""
    return app_fixture.test_client()

@pytest.fixture(scope='module')
def runner(app_fixture): # Aunque no se usa en estas pruebas, es bueno tenerlo
    """Proporciona un ejecutor de comandos CLI de Flask."""
    return app_fixture.test_cli_runner()

# --- Funciones de Prueba ---

def test_obtener_productos_vacio(client):
    """
    Prueba GET /productos cuando no hay productos en la base de datos.
    Debería devolver una lista vacía y un estado 200 OK.
    """
    with flask_app.app_context():
        # Limpiar todos los productos de la tabla
        Producto.query.delete()
        db.session.commit()

    response = client.get('/productos')
    
    assert response.status_code == 200
    assert response.json == [] # Esperamos una lista JSON vacía
    assert response.content_type == 'application/json'

def test_crear_producto(client):
    """
    Prueba POST /productos para crear un nuevo producto.
    """
    # Limpiar la tabla antes de esta prueba para asegurar un estado conocido.
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
    
    assert response.status_code == 201 # 201 Created
    assert response.content_type == 'application/json'
    
    response_json = response.json
    assert response_json['nombre'] == producto_data['nombre']
    assert response_json['descripcion'] == producto_data['descripcion']
    assert response_json['precio'] == producto_data['precio']
    assert response_json['stock'] == producto_data['stock']
    assert 'id' in response_json # El ID debería estar presente

    # Verificar que el producto existe en la base de datos
    with flask_app.app_context():
        # CORRECCIÓN para la advertencia de SQLAlchemy:
        # Usar db.session.get(Modelo, id_primaria) en lugar de Modelo.query.get(id_primaria)
        producto_db = db.session.get(Producto, response_json['id'])
        assert producto_db is not None
        assert producto_db.nombre == producto_data['nombre']
        assert producto_db.precio == producto_data['precio'] # Añadir más aserciones si se desea