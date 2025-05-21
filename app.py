from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuración de la base de datos
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mi_clave_secreta'

db = SQLAlchemy(app)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # admin, asistente, atencion

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_password(password):
            session['usuario_id'] = usuario.id
            session['rol'] = usuario.rol
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))

        flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')

# cerrar sesion
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('login'))


# Modelo Cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    tipo_identificacion = db.Column(db.String(50), nullable=False)
    numero_identificacion = db.Column(db.String(50), unique=True, nullable=False)
    celular = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(50), nullable=True, default='Nuevo')
    tareas = db.relationship('Tarea', backref='cliente', lazy=True)

# Modelo Producto
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    precio = db.Column(db.String(50), nullable=False)
    imagen_url = db.Column(db.String(300), nullable=True)

# Modelo Tarea
class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    completado = db.Column(db.Boolean, default=False)
    estado = db.Column(db.String(50), nullable=False, default='Pendiente')
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)  # Relación con Producto
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Establecer relación con Producto
    producto = db.relationship('Producto', backref='tareas', lazy=True)


def enviar_correos_a_clientes(clientes):
    for cliente in clientes:
        tareas = cliente.tareas or []
        tareas_completadas = [t for t in tareas if t.estado == 'Completada']
        tareas_pendientes = [t for t in tareas if t.estado == 'Pendiente']

        print(f"\nCliente: {cliente.nombre}, Estado: {cliente.estado}, Tareas: {[t.estado for t in tareas]}")

        # 1. Cliente nuevo (sin tareas)
        if cliente.estado == 'Nuevo' and not tareas:
            print("→ Enviando catálogo a cliente nuevo.")
            enviar_catalogo_como_html(cliente.email, cliente.nombre)

        # 2. Cliente Interesado con tareas pendientes
        elif cliente.estado == 'Interesado' and tareas_pendientes:
            for tarea in tareas_pendientes:
                if tarea.estado == 'Pendiente':
                    print("→ Enviando mensaje interesado por tarea pendiente.")
                    producto_en_tarea = tarea.producto
                    enviar_mensaje_interesado(cliente.email, cliente.nombre, producto_en_tarea)

        # 3. Cliente en Venta con tareas completadas
        elif cliente.estado == 'Venta' and tareas_completadas:
            for tarea in tareas_completadas:
                print("→ Enviando mensaje de gracias por venta.")
                enviar_mensaje_gracias(cliente.email, cliente.nombre, tarea)

                # 4. Cliente en seguimiento con tareas pendiente
        
        elif cliente.estado == 'Seguimiento' and tareas_pendientes:
            for tarea in tareas_pendientes:
                print("→ Enviando mensaje de cobro.")
                enviar_mensaje_cobro(cliente.email, cliente.nombre, tarea)

        # 4. Cliente Frío sin tareas
        elif cliente.estado == 'Frío' and not tareas:
            print("→ Enviando catálogo con promociones a cliente frío sin tareas.")
            enviar_catalogo_con_promociones(cliente.email, cliente.nombre)

        # 5. Cliente Frío con tareas pendientes
        elif cliente.estado == 'Frío' and tareas_pendientes:
            for tarea in tareas_pendientes:
                print("→ Enviando producto con promociones a cliente frío con tarea pendiente.")
                enviar_producto_con_promociones(cliente.email, cliente.nombre, tarea)

def enviar_catalogo_como_html(cliente_email, cliente_nombre):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'crmprueba60@gmail.com'
    smtp_password = 'dxuh lwzy qgkb ilnw'

    productos = Producto.query.all()

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Nuestro catálogo de productos'
    mensaje['From'] = smtp_user
    mensaje['To'] = cliente_email

    html = f"""
    <html>
        <body>
            <h2>Hola {cliente_nombre},</h2>
            <p>¡Gracias por tu interés! Te compartimos nuestro catálogo de productos:</p>
    """

    for producto in productos:
        html += f"""
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <h3>{producto.nombre}</h3>
                <p><strong>Precio:</strong> ${producto.precio}</p>
                <p>{producto.descripcion or ''}</p>
                <img src="{producto.imagen_url}" alt="{producto.nombre}" width="250"><br>
            </div>
        """

    html += """
            <p>¿Te interesa alguno? ¡Responde este correo o contáctanos!</p>
            <p>Saludos,<br>Equipo de Ventas</p>
        </body>
    </html>
    """

    mensaje.set_content("Tu cliente de correo no soporta HTML. Revisa nuestro catálogo desde un navegador.")
    mensaje.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(mensaje)
        print(f"Catálogo enviado a {cliente_email}")
    except Exception as e:
        print(f"Error al enviar catálogo: {e}")


def enviar_mensaje_interesado(cliente_email, cliente_nombre, producto):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'crmprueba60@gmail.com'
    smtp_password = 'dxuh lwzy qgkb ilnw'

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Producto que podría interesarte'
    mensaje['From'] = smtp_user
    mensaje['To'] = cliente_email

    html = f"""
    <html>
        <body>
            <h2>Hola {cliente_nombre},</h2>
            <p>Vimos que estás interesado en nuestros productos. Te queremos hablar sobre uno de ellos:</p>
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <h3>{producto.nombre}</h3>
                <p><strong>Precio:</strong> ${producto.precio}</p>
                <p>{producto.descripcion or ''}</p>
                <img src="{producto.imagen_url}" alt="{producto.nombre}" width="250"><br>
            </div>
            <p>¡Esperamos que te interese! Si tienes alguna pregunta, no dudes en contactarnos.</p>
            <p>Saludos,<br>Equipo de Ventas</p>
        </body>
    </html>
    """

    mensaje.set_content("Tu cliente de correo no soporta HTML. Revisa este mensaje en un navegador.")
    mensaje.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(mensaje)
        print(f"Correo enviado a {cliente_email}")
    except Exception as e:
        print(f"Error al enviar correo de interesado: {e}")


def enviar_mensaje_cobro(cliente_email, cliente_nombre, tarea):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'crmprueba60@gmail.com'
    smtp_password = 'dxuh lwzy qgkb ilnw'

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Recuerda el pago de tu auto'
    mensaje['From'] = smtp_user
    mensaje['To'] = cliente_email

    # Asumiendo que la tarea  pendiente tiene una imagen asociada
    imagen_url = tarea.producto.imagen_url

    html = f"""
    <html>
        <body>
            <h2>Hola {cliente_nombre},</h2>
            <p>Recuerda que es importante hacer tus pagos para adquirir tu auto fecha limite {tarea.fecha_vencimiento}:</p>
            <img src="{imagen_url}" alt="Imagen de la tarea completada" width="300"><br>
            <p>Saludos,<br>Equipo de Ventas</p>
        </body>
    </html>
    """

    mensaje.set_content("Tu cliente de correo no soporta HTML. Revisa este mensaje en un navegador.")
    mensaje.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(mensaje)
        print(f"Correo de agradecimiento enviado a {cliente_email}")
    except Exception as e:
        print(f"Error al enviar correo de agradecimiento: {e}")

def enviar_mensaje_gracias(cliente_email, cliente_nombre, tarea):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'crmprueba60@gmail.com'
    smtp_password = 'dxuh lwzy qgkb ilnw'

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Gracias por completar tus tareas'
    mensaje['From'] = smtp_user
    mensaje['To'] = cliente_email

    # Asumiendo que la tarea completada tiene una imagen asociada
    imagen_url = tarea.producto.imagen_url

    html = f"""
    <html>
        <body>
            <h2>Hola {cliente_nombre},</h2>
            <p>¡Gracias por completar tu proceso con nosotros! Estrena con alegria tu nuevo auto ya esta listo!!!:</p>
            <img src="{imagen_url}" alt="Imagen de la tarea completada" width="300"><br>
            <p>Saludos,<br>Equipo de Ventas</p>
        </body>
    </html>
    """

    mensaje.set_content("Tu cliente de correo no soporta HTML. Revisa este mensaje en un navegador.")
    mensaje.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(mensaje)
        print(f"Correo de agradecimiento enviado a {cliente_email}")
    except Exception as e:
        print(f"Error al enviar correo de agradecimiento: {e}")



def enviar_catalogo_con_promociones(cliente_email, cliente_nombre):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'crmprueba60@gmail.com'
    smtp_password = 'dxuh lwzy qgkb ilnw'

    productos = Producto.query.all()

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Nuestro catálogo de productos + Promociones especiales'
    mensaje['From'] = smtp_user
    mensaje['To'] = cliente_email

    html = f"""
    <html>
        <body>
            <h2>Hola {cliente_nombre},</h2>
            <p>¡Gracias por tu interés! Te compartimos nuestro catálogo de productos, además de algunas promociones especiales:</p>
    """

    for producto in productos:
        html += f"""
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <h3>{producto.nombre}</h3>
                <p><strong>Precio:</strong> ${producto.precio}</p>
                <p>{producto.descripcion or ''}</p>
                <img src="{producto.imagen_url}" alt="{producto.nombre}" width="250"><br>
            </div>
        """

    html += """
            <h3>Promociones Especiales</h3>
            <ul>
                <li>SOAT Incluido</li>
                <li>Kit de carretera gratuito con la compra de cualquier vehículo</li>
            </ul>
            <p>Esperamos que encuentres algo de tu interés. ¡No dudes en contactarnos para más detalles!</p>
            <p>Saludos,<br>Equipo de Ventas</p>
        </body>
    </html>
    """

    mensaje.set_content("Tu cliente de correo no soporta HTML. Revisa nuestro catálogo desde un navegador.")
    mensaje.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(mensaje)
        print(f"Catálogo y promociones enviados a {cliente_email}")
    except Exception as e:
        print(f"Error al enviar catálogo con promociones: {e}")


def enviar_producto_con_promociones(cliente_email, cliente_nombre, tarea):
    producto = tarea.producto
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'crmprueba60@gmail.com'
    smtp_password = 'dxuh lwzy qgkb ilnw'

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Producto y promociones especiales'
    mensaje['From'] = smtp_user
    mensaje['To'] = cliente_email

    html = f"""
    <html>
        <body>
            <h2>Hola {cliente_nombre},</h2>
            <p>Te queremos mostrar un producto de interés para ti:</p>
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <h3>{producto.nombre}</h3>
                <p><strong>Precio:</strong> ${producto.precio}</p>
                <p>{producto.descripcion or ''}</p>
                <img src="{producto.imagen_url}" alt="{producto.nombre}" width="250"><br>
            </div>
            <h3>Promociones Especiales</h3>
            <ul>
                <li>SOAT Incluido</li>
                <li>Kit de carretera gratuito con la compra de cualquier vehículo</li>
            </ul>
            <p>Esperamos que te interese. ¡No dudes en contactarnos!</p>
            <p>Saludos,<br>Equipo de Ventas</p>
        </body>
    </html>
    """

    mensaje.set_content("Tu cliente de correo no soporta HTML. Revisa este mensaje en un navegador.")
    mensaje.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(mensaje)
        print(f"Correo con producto y promociones enviado a {cliente_email}")
    except Exception as e:
        print(f"Error al enviar correo con producto y promociones: {e}")

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    clientes = Cliente.query.all()
    return render_template('index.html', clientes=clientes)


@app.route('/enviar_correos', methods=['POST'])
def enviar_correos():
    clientes = Cliente.query.all()
    enviar_correos_a_clientes(clientes)
    flash("Correos enviados exitosamente a los clientes.", "success")
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
def add_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        tipo_identificacion = request.form['tipo_identificacion']
        numero_identificacion = request.form['numero_identificacion']
        celular = request.form['celular']

        # Validación: que los campos sean solo números
        if not numero_identificacion.isdigit() or not celular.isdigit():
            flash('El número de identificación y el celular deben contener solo números.', 'danger')
            return redirect(url_for('add_cliente'))

        # Validación: duplicados
        cliente_existente = Cliente.query.filter(
            (Cliente.email == email) | (Cliente.numero_identificacion == numero_identificacion)
        ).first()
        if cliente_existente:
            flash('El correo electrónico o número de identificación ya está registrado', 'danger')
            return redirect(url_for('add_cliente'))

        # Crear y guardar cliente
        nuevo_cliente = Cliente(
            nombre=nombre,
            email=email,
            tipo_identificacion=tipo_identificacion,
            numero_identificacion=numero_identificacion,
            celular=celular
        )
        db.session.add(nuevo_cliente)
        db.session.commit()
        flash('Cliente agregado correctamente', 'success')
        return redirect(url_for('index'))

    return render_template('add_cliente.html')


@app.route('/editar_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == 'POST':
        numero_identificacion = request.form['numero_identificacion']
        celular = request.form['celular']

        # Validación: que los campos sean solo números
        if not numero_identificacion.isdigit() or not celular.isdigit():
            flash('El número de identificación y el celular deben contener solo números.', 'danger')
            return redirect(url_for('editar_cliente', cliente_id=cliente.id))

        # Actualizar campos
        cliente.nombre = request.form['nombre']
        cliente.email = request.form['email']
        cliente.tipo_identificacion = request.form['tipo_identificacion']
        cliente.numero_identificacion = numero_identificacion
        cliente.celular = celular
        cliente.estado = request.form['estado']

        db.session.commit()
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('index'))

    return render_template('editar_cliente.html', cliente=cliente)


@app.route('/eliminar_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    for tarea in cliente.tareas:
        db.session.delete(tarea)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado correctamente', 'success')
    return redirect(url_for('index'))

@app.route('/tareas/<int:cliente_id>')
def tareas_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    tareas = Tarea.query.filter_by(cliente_id=cliente_id).all()
    productos = Producto.query.all()
    return render_template('tareas_cliente.html', cliente=cliente, tareas=tareas, productos=productos)

@app.route('/add_tarea/<int:cliente_id>', methods=['GET', 'POST'])
def add_tarea(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    productos = Producto.query.all()
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        fecha_vencimiento = datetime.strptime(request.form['fecha_vencimiento'], '%Y-%m-%d').date()
        estado = request.form['estado']
        producto_id = request.form['valor']  # Aquí guardas el ID del producto

        nueva_tarea = Tarea(
            descripcion=descripcion,
            fecha_vencimiento=fecha_vencimiento,
            estado=estado,
            producto_id=producto_id,  # Asociamos el producto por su ID
            cliente_id=cliente.id
        )
        db.session.add(nueva_tarea)
        db.session.commit()
        flash('Tarea agregada correctamente', 'success')
        return redirect(url_for('tareas_cliente', cliente_id=cliente.id))
    return render_template('add_tarea.html', cliente=cliente, productos=productos)

@app.route('/editar_tarea/<int:tarea_id>', methods=['GET', 'POST'])
def editar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    productos = Producto.query.all()
    if request.method == 'POST':
        tarea.descripcion = request.form['descripcion']
        tarea.fecha_vencimiento = datetime.strptime(request.form['fecha_vencimiento'], '%Y-%m-%d').date()
        tarea.estado = request.form['estado']
        tarea.producto_id = request.form['valor']
        db.session.commit()
        flash('Tarea actualizada correctamente', 'success')
        return redirect(url_for('tareas_cliente', cliente_id=tarea.cliente_id))
    return render_template('editar_tarea.html', tarea=tarea, productos=productos)

@app.route('/eliminar_tarea/<int:tarea_id>', methods=['POST'])
def eliminar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    cliente_id = tarea.cliente_id
    db.session.delete(tarea)
    db.session.commit()
    flash('Tarea eliminada correctamente', 'success')
    return redirect(url_for('tareas_cliente', cliente_id=cliente_id))


@app.route('/editar_estado/<int:cliente_id>', methods=['GET', 'POST'])
def editar_estado(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == 'POST':
        cliente.estado = request.form['estado']
        db.session.commit()
        flash('Estado actualizado correctamente', 'success')
        return redirect(url_for('index'))
    return render_template('editar_estado.html', cliente=cliente)

# CRUD Productos
@app.route('/productos')
def lista_productos():
    productos = Producto.query.all()
    return render_template('productos_lista.html', productos=productos)

@app.route('/add_producto', methods=['GET', 'POST'])
def add_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        imagen_url = request.form['imagen_url']

        nuevo_producto = Producto(nombre=nombre, descripcion=descripcion, precio=precio, imagen_url=imagen_url)
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto agregado correctamente', 'success')
        return redirect(url_for('lista_productos'))
    return render_template('crear_producto.html')

@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.precio = request.form['precio']
        producto.imagen_url = request.form['imagen_url']
        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('lista_productos'))
    return render_template('editar_producto.html', producto=producto)

@app.route('/eliminar_producto/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    producto = Producto.query.get(producto_id)
    if producto:
        db.session.delete(producto)
        db.session.commit()
    return redirect(url_for('lista_productos'))

@app.route('/total_ventas')
def total_ventas():
    # Obtener todas las tareas que estén en estado "Completado"
    tareas_completadas = Tarea.query.filter_by(estado='Completada').all()

    # Calcular el total sumando los precios de los productos asociados
    total_ventas = sum(float(tarea.producto.precio) for tarea in tareas_completadas if tarea.producto)

    return render_template('total_ventas.html', total_ventas=total_ventas)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

          # Crear usuarios quemados si no existen
        usuarios = [
            {'email': 'admin@crm.com', 'password': 'admin123', 'rol': 'admin'},
            {'email': 'servicio@crm.com', 'password': 'servicio123', 'rol': 'servicio'},
            {'email': 'asesor@crm.com', 'password': 'asesor123', 'rol': 'asesor'}
        ]

        for u in usuarios:
            if not Usuario.query.filter_by(email=u['email']).first():
                nuevo = Usuario(email=u['email'], rol=u['rol'])
                nuevo.set_password(u['password'])
                db.session.add(nuevo)

        db.session.commit()
    app.run(debug=True)