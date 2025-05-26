import unittest

# Aquí iría la función que quieres testear, por ejemplo:
def enviar_correo(destinatario, asunto, mensaje):
    if not destinatario or '@' not in destinatario:
        return False
    # Simular que el correo se envía correctamente
    return True

class TestEnvioCorreos(unittest.TestCase):

    def test_envio_valido(self):
        self.assertTrue(enviar_correo('test@example.com', 'Hola', 'Mensaje de prueba'))

    def test_envio_sin_destinatario(self):
        self.assertFalse(enviar_correo('', 'Hola', 'Mensaje de prueba'))

    def test_envio_destinatario_invalido(self):
        self.assertFalse(enviar_correo('sin_arroba', 'Hola', 'Mensaje de prueba'))

if __name__ == "__main__":
    unittest.main() 

