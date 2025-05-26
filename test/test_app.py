import unittest
from app import app, enviar_catalogo_como_html

class TestEnvioCorreo(unittest.TestCase):
    def test_enviar_catalogo(self):
        with app.app_context():
            # Aquí ejecutas la función que usa Producto.query
            enviar_catalogo_como_html("correo@ejemplo.com", "Nombre Ejemplo")

if __name__ == '__main__':
    unittest.main()
    