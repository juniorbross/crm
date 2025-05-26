import unittest
from app import app, db
from app import Producto

class TestAddProducto(unittest.TestCase):
    def setUp(self):
        # Configurar la app para testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Base de datos en memoria para pruebas
        self.client = app.test_client()

        # Crear las tablas en la base de datos en memoria
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Limpiar la base de datos después de cada test
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_add_producto_post(self):
        data = {
            'nombre': 'Producto Test',
            'descripcion': 'Descripción del producto',
            'precio': '12.34',
            'imagen_url': 'http://imagen.test/img.jpg'
        }

        # Enviar POST para agregar producto
        response = self.client.post('/add_producto', data=data, follow_redirects=True)

        # Verificar que la respuesta fue exitosa
        self.assertEqual(response.status_code, 200)

        # Verificar que el producto se guardó en la base de datos
        with app.app_context():
            producto = Producto.query.filter_by(nombre='Producto Test').first()
            self.assertIsNotNone(producto)
            self.assertEqual(producto.descripcion, 'Descripción del producto')
            self.assertEqual(float(producto.precio), 12.34)
            self.assertEqual(producto.imagen_url, 'http://imagen.test/img.jpg')


if __name__ == '__main__':
    unittest.main()
