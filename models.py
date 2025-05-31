# models.py
from flask_sqlalchemy import SQLAlchemy

# Inicializa la extensión SQLAlchemy.
# La vinculación a la aplicación Flask se hará en app.py usando db.init_app(app).
db = SQLAlchemy()

class Producto(db.Model):
    # Define el nombre de la tabla en la base de datos.
    __tablename__ = 'productos'

    # Definición de las columnas de la tabla:
    # id: Clave primaria, entero, se autoincrementa.
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # nombre: Cadena de texto (máx 100 caracteres), campo obligatorio.
    nombre = db.Column(db.String(100), nullable=False)
    
    # descripcion: Cadena de texto (máx 255 caracteres), campo opcional.
    descripcion = db.Column(db.String(255), nullable=True)
    
    # precio: Número flotante, campo obligatorio.
    precio = db.Column(db.Float, nullable=False)
    
    # stock: Entero, campo obligatorio.
    stock = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        # Representación en cadena del objeto Producto, útil para debugging.
        return f'<Producto {self.id}: {self.nombre}>'