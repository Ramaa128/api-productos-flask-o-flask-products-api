# config.py
import os

# Obtiene la ruta absoluta del directorio del script actual (api_productos_flask)
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Define la URI para la base de datos SQLite.
    # Se guardará en una carpeta 'instance' dentro del directorio base del proyecto.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'productos.db')
    
    # Desactiva el seguimiento de modificaciones de SQLAlchemy, ya que consume recursos y no lo necesitamos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Evita que Flask ordene las claves de los objetos JSON alfabéticamente en las respuestas.
    # Esto mantiene el orden definido en los esquemas o diccionarios.
    JSON_SORT_KEYS = False