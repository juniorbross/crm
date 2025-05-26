def test_add_cliente_duplicate(self):
    # Agregar cliente original
    data = {
        'nombre': 'Cliente Uno',
        'email': 'duplicado@test.com',
        'tipo_identificacion': 'CC',
        'numero_identificacion': '2222222222',
        'celular': '3001111111'
    }
    self.client.post('/add', data=data, follow_redirects=True)
    # Intentar agregar cliente duplicado
    data2 = {
        'nombre': 'Cliente Dos',
        'email': 'duplicado@test.com',
        'tipo_identificacion': 'TI',
        'numero_identificacion': '3333333333',
        'celular': '3002222222'
    }
    response = self.client.post('/add', data=data2, follow_redirects=True)

    # DEBUG: imprime contenido para revisar el mensaje
    print(response.get_data(as_text=True))

    self.assertNotEqual(response.status_code, 500)
    self.assertIn('El correo electrónico o número de identificación ya está registrado', response.get_data(as_text=True))

