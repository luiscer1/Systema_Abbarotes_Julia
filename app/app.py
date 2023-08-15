# bibliotecas
from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from math import ceil
from datetime import datetime
import os
import re
from flask_bcrypt import Bcrypt, check_password_hash

# Creacion de  una instancia de Flask
app = Flask(__name__)

# Configuración de Flask-Bcrypt para el manejo seguro de contraseñas
bcrypt = Bcrypt(app)

# Configuración de la clave secreta para las sesiones
app.secret_key = "my_super_secret_key_147345"

# Configuración de la carpeta de carga de archivos
app.config['UPLOAD_FOLDER'] = './app/static/img/uploads'

# Configuración de la conexión a la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'luis1473'
app.config['MYSQL_DB'] = 'datos_julia'
mysql = MySQL(app)

# Ruta para procesar el inicio de sesión
@app.route('/', methods=['GET', 'POST'])
def login():
    # Manejar la solicitud POST del formulario de inicio de sesión
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Consultar el administrador en la base de datos
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM Administrador WHERE Correo = %s', (correo,))
        administrador = cur.fetchone()
        cur.close()

        if administrador and check_password_hash(administrador[4], contraseña):
            # Autenticación exitosa
            session['admin_id'] = administrador[0]
            session['admin_nombre'] = administrador[1]
            flash(f'Bienvenid@, {administrador[1]}', 'success')
            return redirect('/admin')
        else:
            # Autenticación fallida
            flash('Credenciales inválidas', 'error')
            return render_template('login.html')

    # Manejar la solicitud GET para mostrar el formulario de inicio de sesión
    return render_template('login.html')

#ruta para registrar un nuevo administrador
@app.route('/register', methods=['GET', 'POST'])
def register_admin():
    # Verificar si el ID de administrador está en la sesión, si no, redirigir a la página principal
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')

    # Manejar la solicitud POST para registrar al nuevo administrador
    if request.method == 'POST':
        # Obtener los datos del formulario enviado 
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Hashear la contraseña antes de almacenarla en la base de datos
        hashed_password = bcrypt.generate_password_hash(contraseña).decode('utf-8')
     
        # cursor para interactuar con la base de datos
        cur = mysql.connection.cursor()
        
        # Consultar si ya existe un administrador con el mismo correo electrónico
        cur.execute('SELECT * FROM Administrador WHERE Correo = %s', (correo,))
        administrador = cur.fetchone()

        # Verificar si ya existe un administrador con el mismo correo electrónico
        if administrador:
            flash('El correo electrónico ya está registrado.', 'error')
            return render_template('register.html')

        # Insertar los datos del nuevo administrador en la tabla Administrador
        cur.execute('INSERT INTO Administrador (Nombre, Apellido, Correo, Contraseña) VALUES (%s, %s, %s, %s)',
                    (nombre, apellido, correo, hashed_password))
        mysql.connection.commit()
        cur.close()

        # Redirigir al panel de administración después de registrar exitosamente
        return redirect('/admin')
    
    # Si la solicitud no es POST, renderizar la página de registro
    return render_template('register.html')



# Ruta de cierre de sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Ruta para acceder al panel de administración
@app.route('/admin')
def admin():
    # Verificar si el ID de administrador está en la sesión, si no, redirigir a la página principal
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')

    #cursor para interactuar con la base de datos
    cur = mysql.connection.cursor()

    # Consultar todos los administradores en la tabla Administrador
    cur.execute('SELECT * FROM Administrador')
    administradores = cur.fetchall()
    cur.close()

    # Obtener el nombre del administrador de la sesión si está disponible
    if 'admin_nombre' in session:
        nombre = session['admin_nombre']
    else:
        nombre = None

    # Renderizar la página de administración con la lista de administradores y el nombre
    return render_template('admin.html', administradores=administradores, nombre=nombre)

# Ruta para agregar un nuevo administrador
@app.route('/admin/add', methods=['GET', 'POST'])
def add_admin():
    # Verificar si el ID de administrador está en la sesión, si no, redirigir a la página principal
    if 'admin_id' not in session:
        return redirect('/')

    # Manejar la solicitud POST para agregar un nuevo administrador
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Validar la contraseña utilizando una expresión 
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", contraseña):
            flash('La contraseña debe tener al menos 8 caracteres, incluyendo una letra y un número.', 'error')
            return redirect('/register')
        else:
            # Hashear la contraseña antes de almacenarla en la base de datos
            hashed_password = bcrypt.generate_password_hash(contraseña).decode('utf-8')

            #cursor para interactuar con la base de datos
            cur = mysql.connection.cursor()

            # Consultar si ya existe un administrador con el mismo correo electrónico
            cur.execute('SELECT * FROM Administrador WHERE Correo = %s', (correo,))
            administrador = cur.fetchone()

            if administrador:
                flash('El correo electrónico ya está registrado.', 'error')
                return render_template('register.html')

            # Insertar los datos del nuevo administrador en la tabla Administrador
            cur.execute('INSERT INTO Administrador (Nombre, Apellido, Correo, Contraseña) VALUES (%s, %s, %s, %s)',
                        (nombre, apellido, correo, hashed_password))
            mysql.connection.commit()
            cur.close()

            flash('Administrador registrado correctamente', 'success')
            return redirect('/admin')

    # Si la solicitud no es POST, renderizar la página de registro
    return render_template('register.html')



# Ruta para editar un administrador específico
@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_admin(id):
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Administrador WHERE idAdministrador = %s', (id,))
    administrador = cur.fetchone()

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        nueva_contraseña = request.form['nueva_contraseña']

        if not administrador:  # Nuevo administrador
            if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", nueva_contraseña):
                flash('La contraseña debe tener al menos 8 caracteres, incluyendo una letra y un número.', 'error')
                return redirect('/register')
            else:
                hashed_password = bcrypt.generate_password_hash(nueva_contraseña).decode('utf-8')
                cur.execute('INSERT INTO Administrador (Nombre, Apellido, Correo, Contraseña) VALUES (%s, %s, %s, %s)',
                            (nombre, apellido, correo, hashed_password))
        else:  # Administrador existente
            cur.execute('UPDATE Administrador SET Nombre = %s, Apellido = %s, Correo = %s WHERE idAdministrador = %s',
                        (nombre, apellido, correo, id))
            if nueva_contraseña:  # Actualizar la contraseña solo si se proporciona
                if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", nueva_contraseña):
                    flash('La contraseña debe tener al menos 8 caracteres, incluyendo una letra y un número.', 'error')
                    return redirect('/register')
                else:
                    hashed_password = bcrypt.generate_password_hash(nueva_contraseña).decode('utf-8')
                    cur.execute('UPDATE Administrador SET Contraseña = %s WHERE idAdministrador = %s',
                                (hashed_password, id))

        mysql.connection.commit()
        cur.close()

        flash('Administrador editado correctamente', 'success')
        return redirect('/admin')

    return render_template('edit_admin.html', administrador=administrador)

# Ruta para eliminar un administrador específico
@app.route('/admin/delete/<int:id>', methods=['GET', 'POST'])
def delete_admin(id):
    # Verificar si el ID de administrador está en la sesión, si no, redirigir a la página principal
    if 'admin_id' not in session:
        return redirect('/')

    # Verificar si se está intentando eliminar el administrador principal
    if id == session['admin_id']:
        flash('No puedes eliminar al administrador principal', 'warning')
        return redirect('/admin')

    # cursor para interactuar con la base de datos
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Administrador WHERE idAdministrador = %s', (id,))
    administrador = cur.fetchone()
    cur.close()

    # Verificar si el administrador existe y eliminarlo
    if administrador:
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM Administrador WHERE idAdministrador = %s', (id,))
        mysql.connection.commit()
        cur.close()

        flash('Administrador eliminado correctamente', 'success')
    else:
        flash('El administrador no existe', 'error')

    return redirect('/admin')

categories_list = [
    'Bebidas',
    'Aceites',
    'Frutas y Verduras',
    'Lácteos',
    'Panadería',
    'Pastas y Cereales',
    'Conservas y Enlatados',
    'Dulces ',
    'Cuidado Personal',
    'Limpieza y Hogar',
    'Desechables',
    'Embutidos',
    'Salsa y aderezos',
    'Botanas',
    'Vinos y Licores',
    'Otros'
]
# Ruta para mostrar la lista paginada de productos
@app.route('/productos')
def productos():
    if 'admin_id' not in session:
        return redirect('/')

    # Obtener el número de página actual de la solicitud
    page = request.args.get('page', 1, type=int)
    products_per_page = 3

    # Consulta para contar el número total de productos
    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(*) FROM Productos')
    total_products = cur.fetchone()[0]
    cur.close()

    # Cálculo de páginas totales y configuración de la paginación
    total_pages = (total_products + products_per_page - 1) // products_per_page
    start_idx = (page - 1) * products_per_page

    # Consulta para obtener productos de la página actual
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Productos LIMIT %s, %s', (start_idx, products_per_page))
    productos = cur.fetchall()
    cur.close()

    # Mensaje si no hay productos registrados
    if total_products == 0:
        mensaje = "No hay productos registrados."
    else:
        mensaje = None

    # Renderizar la plantilla con productos y detalles de paginación
    return render_template('productos.html', productos=productos, total_pages=total_pages, current_page=page, total_products=total_products, mensaje=mensaje)



@app.route('/productos/add', methods=['GET', 'POST'])
def add_producto():
    if 'admin_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        categoria = request.form['categoria']

        archivo_imagen = request.files['imagen']
        nombre_archivo_imagen = secure_filename(archivo_imagen.filename)
        ruta_archivo_imagen = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo_imagen)
        archivo_imagen.save(ruta_archivo_imagen)

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO Productos (Nombre, Precio, Cantidad, Categoria, Imagen) VALUES (%s, %s, %s, %s, %s)',
                    (nombre, precio, cantidad, categoria, nombre_archivo_imagen))
        mysql.connection.commit()
        cur.close()
        flash('Producto registrado correctamente', 'success')
        return redirect('/productos')
    return render_template('add_producto.html', categories_list=categories_list)

   

@app.route('/productos/edit/<int:id>', methods=['GET', 'POST'])
def edit_producto(id):
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Productos WHERE idProductos = %s', (id,))
    producto = cur.fetchone()

    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        categoria = request.form['categoria']

        archivo_imagen = request.files['imagen']
        nombre_archivo_imagen = None  

        if archivo_imagen and archivo_imagen.filename != '':
            
            nombre_archivo_imagen = secure_filename(archivo_imagen.filename)
            ruta_archivo_imagen = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo_imagen)
            archivo_imagen.save(ruta_archivo_imagen)
        else:
            
            nombre_archivo_imagen = producto['Imagen']

        cur.execute('UPDATE Productos SET Nombre = %s, Precio = %s, Cantidad = %s, Categoria = %s, Imagen = %s WHERE idProductos = %s',
                    (nombre, precio, cantidad, categoria, nombre_archivo_imagen, id))
        mysql.connection.commit()
        cur.close()
        flash('Producto editado correctamente', 'success')

        return redirect('/productos')

    return render_template('edit_producto.html', producto=producto, categories_list=categories_list)

@app.route('/productos/delete/<int:id>', methods=['GET', 'POST'])
def delete_producto(id):
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM Productos WHERE idProductos = %s', (id,))
    mysql.connection.commit()
    cur.close()
    flash('Producto  eliminado correctamente', 'success')

    return redirect('/productos')

# Rutas y lógica para ventas
@app.route('/ventas')
@app.route('/ventas/<int:page>')
def ventas(page=1):
    if 'admin_id' not in session:
        return redirect('/')

    per_page = 2
    cur = mysql.connection.cursor()

    cur.execute('SELECT COUNT(*) FROM Ventas')
    total_sales = cur.fetchone()[0]
    total_pages = ceil(total_sales / per_page)
    offset = (page - 1) * per_page

    cur.execute('SELECT * FROM Ventas LIMIT %s OFFSET %s', (per_page, offset))
    ventas = cur.fetchall()
    cur.close()

    if not ventas:
        flash('No hay ventas registradas, por favor registre la venta total del día.', 'info')

    return render_template('ventas.html', ventas=ventas, current_page=page, total_pages=total_pages, per_page=per_page)

@app.route('/ventas/add', methods=['GET', 'POST'])
def add_venta():
    total_compras_dia = request.args.get('total_compras_dia')
    if 'admin_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        fecha = request.form['fecha']
        total = request.form['total']
        administrador_id = request.form['administrador_id']

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO Ventas (Fecha, Total, Administrador_idAdministrador) VALUES (%s, %s, %s)',
                    (fecha, total, administrador_id))
        mysql.connection.commit()
        cur.close()
        flash('Venta registrada correctamente', 'success')
        return redirect('/ventas')

    total_compras_dia = calcular_total_compras_dia()  
    

    return render_template('add_venta.html', total_compras_dia=total_compras_dia)





@app.route('/ventas/edit/<int:id>', methods=['GET', 'POST'])
def edit_venta(id):
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Ventas WHERE idVentas = %s', (id,))
    venta = cur.fetchone()

    if request.method == 'POST':
        fecha = request.form['fecha']
        total = request.form['total']
        administrador_id = request.form['administrador_id']

        cur.execute('UPDATE Ventas SET Fecha = %s, Total = %s, Administrador_idAdministrador = %s WHERE idVentas = %s',
                    (fecha, total, administrador_id, id))
        mysql.connection.commit()
        cur.close()
        flash('Venta editada correctamente', 'success')

        return redirect('/ventas')

    return render_template('edit_venta.html', venta=venta)


@app.route('/ventas/delete/<int:id>', methods=['GET', 'POST'])
def delete_venta(id):
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM Ventas WHERE idVentas = %s', (id,))
    mysql.connection.commit()
    cur.close()
    flash('Venta eliminada correctamente', 'success')
    return redirect('/ventas')

# Rutas para proveedores
@app.route('/proveedores')
def proveedores():
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Proveedores')
    proveedores = cur.fetchall()
    cur.close()

    if not proveedores:
        mensaje = "No hay proveedores registrados."
        return render_template('proveedores.html', mensaje=mensaje)

    return render_template('proveedores.html', proveedores=proveedores)


@app.route('/proveedores/add', methods=['GET', 'POST'])
def add_proveedor():
    if 'admin_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        numero = request.form['numero']
        administrador_id = request.form['administrador_id']

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO Proveedores (Nombre, Direccion, Numero, Administrador_idAdministrador) VALUES (%s, %s, %s, %s)',
                    (nombre, direccion, numero, administrador_id))
        mysql.connection.commit()
        cur.close()
        flash('Proveedor registrado correctamente', 'success')

        return redirect('/proveedores')

    return render_template('add_proveedor.html')

@app.route('/proveedores/edit/<int:id>', methods=['GET', 'POST'])
def edit_proveedor(id):
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Proveedores WHERE idProveedores = %s', (id,))
    proveedor = cur.fetchone()

    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        numero = request.form['numero']
        administrador_id = request.form['administrador_id']

        cur.execute('UPDATE Proveedores SET Nombre = %s, Direccion = %s, Numero = %s, Administrador_idAdministrador = %s WHERE idProveedores = %s',
                    (nombre, direccion, numero, administrador_id, id))
        mysql.connection.commit()
        cur.close()
        flash('Proveedor editado correctamente', 'success')

        return redirect('/proveedores')

    return render_template('edit_proveedor.html', proveedor=proveedor)


@app.route('/proveedores/delete/<int:id>', methods=['GET', 'POST'])
def delete_proveedor(id):
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM Proveedores WHERE idProveedores = %s', (id,))
    mysql.connection.commit()
    cur.close()
    flash('Proveedor eliminado correctamente', 'success')

    return redirect('/proveedores')


# Ruta para consultar productos por categoría
@app.route('/productos/categoria', methods=['GET', 'POST'])
def consultar_productos_por_categoria():
    if 'admin_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        categoria = request.form['categoria']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM Productos WHERE Categoria = %s', (categoria,))
        productos = cur.fetchall()
        cur.close()

        if not productos:  # Verificar si la lista está vacía
            mensaje = "No se encontraron productos en esta categoría."
            return render_template('productos_categoria.html', mensaje=mensaje)

        return render_template('productos_categoria.html', productos=productos)

    return render_template('consultar_productos_categoria.html', categories_list=categories_list)



# Ruta para consultar ventas por rango de fechas
@app.route('/ventas/rango-fechas', methods=['GET', 'POST'])
def consultar_ventas_por_rango_fechas():
    if 'admin_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM Ventas WHERE Fecha BETWEEN %s AND %s', (fecha_inicio, fecha_fin))
        ventas = cur.fetchall()
        cur.close()

        if not ventas:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            mensaje = f'No hay ventas registradas entre {fecha_inicio_dt.strftime("%d-%m-%Y")} y {fecha_fin_dt.strftime("%d-%m-%Y")}.'
            flash(mensaje, 'info')

        return render_template('ventas_rango_fechas.html', ventas=ventas)

    return render_template('consultar_ventas_rango_fechas.html')


# Ruta para el reporte de productos  vendidos por dia
@app.route('/productos_vendidos')
def productos_vendidos():
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT producto, SUM(cantidad) AS total_cantidad, MAX(precio) AS precio, SUM(precio * cantidad) AS total_venta FROM compras GROUP BY producto ORDER BY total_cantidad DESC")
    products = cur.fetchall()
    cur.close()

    if not products:
        mensaje = "No se han vendido productos hoy."
        return render_template('productos_vendidos.html', mensaje=mensaje)
    
    return render_template('productos_vendidos.html', products=products)



# Ruta para mostrar la lista de compras
@app.route('/compras')
def compras():
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM compras")
    compras = cur.fetchall()
    cur.close()

    if not compras:
        flash('No hay ventas registradas, por favor registre nuevas ventas.', 'info')

    return render_template('mostrar_compras.html', compras=compras)



# Ruta para agregar una compra
@app.route('/compras/agregar', methods=['GET', 'POST'])
def agregar_compra():
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')
    if request.method == 'POST':
        producto = request.form['producto']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO compras (producto, precio, cantidad) VALUES (%s, %s, %s)", (producto, precio, cantidad))
        mysql.connection.commit()
        cur.close()
        flash('Venta del dia registrada correctamente', 'success')
        return redirect('/compras')
    
    total_compras_dia = calcular_total_compras_dia()  # Calcular el total de compras del día

    return render_template('agregar_compra.html', total_compras_dia=total_compras_dia)


# Ruta para editar una compra
@app.route('/compras/editar/<int:idCompra>', methods=['GET', 'POST'])
def editar_compra(idCompra):
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM compras WHERE idCompra = %s", (idCompra,))
    compra = cur.fetchone()
    if request.method == 'POST':
        producto = request.form['producto']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        cur.execute("UPDATE compras SET producto = %s, precio = %s, cantidad = %s WHERE idCompra = %s",
                    (producto, precio, cantidad, idCompra))
        mysql.connection.commit()
        cur.close()
        flash('Venta del dia editada correctamente', 'success')
        return redirect('/compras')
    return render_template('editar_compra.html', compra=compra)


# Ruta para eliminar una compra
@app.route('/compras/eliminar/<int:idCompra>', methods=['GET', 'POST'])
def eliminar_compra(idCompra):
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM compras WHERE idCompra = %s", (idCompra,))
    mysql.connection.commit()
    cur.close()
    flash('Venta del dia eliminada correctamente', 'success')
    return redirect('/compras')


# Función para calcular el total de una compra
def calcular_total_compra(precio, cantidad):
    return precio * cantidad


# Función para calcular el total de las compras del día
def calcular_total_compras_dia():
    cur = mysql.connection.cursor()
    cur.execute("SELECT SUM(precio * cantidad) FROM compras")
    total = cur.fetchone()[0]
    cur.close()
    return total

@app.route('/compras/terminar')
def terminar_compras():
    if 'admin_id' not in session:
        flash('Debe iniciar sesión primero', 'error')
        return redirect('/')
    # Calcular el total de compras del día
    total_compras_dia = calcular_total_compras_dia()

    return redirect(url_for('add_venta', total_compras_dia=total_compras_dia))

@app.route('/compras/vaciar')
def vaciar_compras():
    if 'admin_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM Compras')
    mysql.connection.commit()
    cur.close()
    flash('Puede registrar nuevas ventas del dia', 'success')

    return redirect('/compras/agregar')

from flask import jsonify


# Función para asignar un ícono y un color a cada tipo de mensaje flash
def get_flash_message_style(category):
    styles = {
        'success': ('fas fa-check-circle', 'success'),
        'error': ('fas fa-exclamation-circle', 'danger'),
        'info': ('fas fa-info-circle', 'info'),
        'warning': ('fas fa-exclamation-triangle', 'warning')
    }
    return styles.get(category, ('', 'secondary'))
# Registrar la función en el contexto de la plantilla
app.add_template_global(get_flash_message_style, name='get_flash_message_style')

if __name__ == '__main__':
    app.run()