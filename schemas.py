# schemas.py
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import Producto # Importa el modelo Producto

# Inicializa la extensión Marshmallow.
# La vinculación a la aplicación Flask se hará en app.py usando ma.init_app(app).
ma = Marshmallow()

class ProductoSchema(SQLAlchemyAutoSchema):
    class Meta:
        # Especifica el modelo SQLAlchemy a partir del cual generar el esquema.
        model = Producto
        
        # Cuando se deserializan datos (ej. desde un JSON de entrada con .load()),
        # Marshmallow intentará crear o actualizar una instancia del modelo Producto.
        load_instance = True
        
        # Opcional: puedes especificar qué campos incluir o excluir explícitamente.
        # Si no se especifica, SQLAlchemyAutoSchema incluye todos los campos del modelo.
        # fields = ("id", "nombre", "descripcion", "precio", "stock")
        # exclude = ("algun_campo_a_excluir",)

# Instancia del esquema para serializar/deserializar un solo objeto Producto.
producto_schema = ProductoSchema()

# Instancia del esquema para serializar/deserializar una lista de objetos Producto.
productos_schema = ProductoSchema(many=True)