# tests/test_app.py
import pytest
from app import app as flask_app, db
from models import Producto

@pytest.fixture(scope='module')
def app_fixture():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": flask_app.config["SQLALCHEMY_DATABASE_URI"],
    })
    with flask_app.app_context():
        db.create_all()
    yield flask_app

@pytest.fixture(scope='module')
def client(app_fixture):
    return app_fixture.test_client()

@pytest.fixture(scope='module')
def runner(app_fixture):
    return app_fixture.test_cli_runner()

# --- Funciones de Prueba ---

def test_obtener_productos_vacio(client):
    with flask_app.app_context():
        Producto.query.delete()
        db.session.commit()
    response = client.get('/productos')
    assert response.status_code == 200
    assert response.json == []
    assert response.content_type == 'application/json'

def test_crear_producto(client):
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
    with flask_app.app_context():
        producto_db = db.session.get(Producto, response_json['id'])
        assert producto_db is not None
        assert producto_db.nombre == producto_data['nombre']

# NUEVAS PRUEBAS AÑADIDAS AQUÍ:
def test_obtener_producto_existente(client):
    """
    Prueba GET /productos/<id> para un producto que existe.
    """
    # Limpiar la BD para esta prueba específica para evitar colisiones de ID si se ejecutan en orden.
    with flask_app.app_context():
        Producto.query.delete()
        db.session.commit()

    producto_data_original = {
        "nombre": "Producto Específico",
        "descripcion": "Descripción para obtener",
        "precio": 25.50,
        "stock": 5
    }
    response_post = client.post('/productos', json=producto_data_original)
    assert response_post.status_code == 201 # Asegurarse que la creación fue exitosa
    producto_creado_id = response_post.json['id']

    response_get = client.get(f'/productos/{producto_creado_id}')
    
    assert response_get.status_code == 200
    assert response_get.content_type == 'application/json'
    
    response_json = response_get.json
    assert response_json['id'] == producto_creado_id
    assert response_json['nombre'] == producto_data_original['nombre']
    assert response_json['descripcion'] == producto_data_original['descripcion']
    assert response_json['precio'] == producto_data_original['precio']
    assert response_json['stock'] == producto_data_original['stock']

def test_obtener_producto_no_existente(client):
    """
    Prueba GET /productos/<id> para un producto que NO existe.
    Debería devolver un estado 404.
    """
    # Asegurarse que la BD está limpia o que el ID es realmente no existente
    with flask_app.app_context():
        Producto.query.delete() # Opcional, pero ayuda a asegurar que el ID no exista
        db.session.commit()

    id_no_existente = 99999 
    response = client.get(f'/productos/{id_no_existente}')
    
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    
    response_json = response.json
    assert 'error' in response_json
    # Compara con el mensaje exacto definido en tu endpoint app.py para error 404
    assert response_json['error'] == 'Producto no encontrado' 