import sqlite3
import hashlib

DATABASE_NAME = 'pos_database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Para acceder a las columnas por nombre
    return conn

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Funciones de Usuarios ---
def crear_usuario(nombre_usuario, contrasena, rol, pregunta_seguridad_1=None, respuesta_seguridad_1=None, pregunta_seguridad_2=None, respuesta_seguridad_2=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hash_contrasena = _hash_password(contrasena)
        cursor.execute('''
        INSERT INTO Usuarios (nombre_usuario, hash_contrasena, rol, pregunta_seguridad_1, respuesta_seguridad_1, pregunta_seguridad_2, respuesta_seguridad_2)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nombre_usuario, hash_contrasena, rol, pregunta_seguridad_1, respuesta_seguridad_1, pregunta_seguridad_2, respuesta_seguridad_2))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # nombre_usuario debe ser único
        return None
    finally:
        conn.close()

def verificar_credenciales(nombre_usuario, contrasena):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_usuario, hash_contrasena, rol FROM Usuarios WHERE nombre_usuario = ?", (nombre_usuario,))
    usuario = cursor.fetchone()
    conn.close()
    if usuario and usuario['hash_contrasena'] == _hash_password(contrasena):
        return {'id': usuario['id'], 'nombre_usuario': usuario['nombre_usuario'], 'rol': usuario['rol']}
    return None

def obtener_usuario_por_nombre(nombre_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_usuario, rol, pregunta_seguridad_1, pregunta_seguridad_2 FROM Usuarios WHERE nombre_usuario = ?", (nombre_usuario,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def obtener_usuario_por_id(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_usuario, rol, pregunta_seguridad_1, respuesta_seguridad_1, pregunta_seguridad_2, respuesta_seguridad_2 FROM Usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def cambiar_contrasena(nombre_usuario, nueva_contrasena):
    conn = get_db_connection()
    cursor = conn.cursor()
    nueva_hash_contrasena = _hash_password(nueva_contrasena)
    try:
        cursor.execute("UPDATE Usuarios SET hash_contrasena = ? WHERE nombre_usuario = ?", (nueva_hash_contrasena, nombre_usuario))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def actualizar_info_usuario(usuario_id, nombre_usuario=None, rol=None, pregunta_seguridad_1=None, respuesta_seguridad_1=None, pregunta_seguridad_2=None, respuesta_seguridad_2=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields_to_update = []
    params = []

    if nombre_usuario is not None:
        fields_to_update.append("nombre_usuario = ?")
        params.append(nombre_usuario)
    if rol is not None:
        fields_to_update.append("rol = ?")
        params.append(rol)
    if pregunta_seguridad_1 is not None:
        fields_to_update.append("pregunta_seguridad_1 = ?")
        params.append(pregunta_seguridad_1)
    if respuesta_seguridad_1 is not None:
        fields_to_update.append("respuesta_seguridad_1 = ?")
        params.append(respuesta_seguridad_1)
    if pregunta_seguridad_2 is not None:
        fields_to_update.append("pregunta_seguridad_2 = ?")
        params.append(pregunta_seguridad_2)
    if respuesta_seguridad_2 is not None:
        fields_to_update.append("respuesta_seguridad_2 = ?")
        params.append(respuesta_seguridad_2)

    if not fields_to_update:
        return False

    query = f"UPDATE Usuarios SET {', '.join(fields_to_update)} WHERE id = ?"
    params.append(usuario_id)

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError: # En caso de que se intente cambiar a un nombre_usuario que ya existe
        return False
    finally:
        conn.close()


def obtener_preguntas_seguridad(nombre_usuario):
    usuario = obtener_usuario_por_nombre(nombre_usuario)
    if usuario:
        return {
            'pregunta_1': usuario['pregunta_seguridad_1'],
            'pregunta_2': usuario['pregunta_seguridad_2']
        }
    return None

def verificar_respuestas_seguridad(nombre_usuario, respuesta_1, respuesta_2):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT respuesta_seguridad_1, respuesta_seguridad_2 FROM Usuarios WHERE nombre_usuario = ?", (nombre_usuario,))
    respuestas_db = cursor.fetchone()
    conn.close()
    if respuestas_db and respuestas_db['respuesta_seguridad_1'] == respuesta_1 and respuestas_db['respuesta_seguridad_2'] == respuesta_2:
        return True
    return False

def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_usuario, rol FROM Usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return [dict(row) for row in usuarios]

def eliminar_usuario(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Asegurarse de que el usuario administrador por defecto no se elimine si es el único admin
        # Esta lógica podría ser más compleja si hay múltiples admins.
        # Por ahora, permitimos la eliminación, pero la UI debería prevenir la eliminación del último admin.
        cursor.execute("DELETE FROM Usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        # También eliminamos sus permisos individuales
        cursor.execute("DELETE FROM UsuariosPermisos WHERE usuario_id = ?", (usuario_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

# --- Funciones de Permisos y Roles ---
def obtener_permiso_id_por_nombre(nombre_permiso):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Permisos WHERE nombre_permiso = ?", (nombre_permiso,))
    permiso = cursor.fetchone()
    conn.close()
    return permiso['id'] if permiso else None

def asignar_permiso_usuario(usuario_id, nombre_permiso, otorgado=True):
    permiso_id = obtener_permiso_id_por_nombre(nombre_permiso)
    if not permiso_id:
        print(f"Error: Permiso '{nombre_permiso}' no encontrado.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO UsuariosPermisos (usuario_id, permiso_id, otorgado)
        VALUES (?, ?, ?)
        ''', (usuario_id, permiso_id, otorgado))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error al asignar permiso: {e}")
        return False
    finally:
        conn.close()

def revocar_permiso_usuario(usuario_id, nombre_permiso):
    return asignar_permiso_usuario(usuario_id, nombre_permiso, otorgado=False)

def obtener_permisos_por_rol_base(rol):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.nombre_permiso
    FROM Permisos p
    JOIN RolesPermisos rp ON p.id = rp.permiso_id
    WHERE rp.rol = ?
    ''', (rol,))
    permisos = [row['nombre_permiso'] for row in cursor.fetchall()]
    conn.close()
    return set(permisos)

def obtener_permisos_usuario(usuario_id):
    usuario = obtener_usuario_por_id(usuario_id)
    if not usuario:
        return set()

    permisos_del_rol = obtener_permisos_por_rol_base(usuario['rol'])

    conn = get_db_connection()
    cursor = conn.cursor()
    # Obtener permisos individuales
    cursor.execute('''
    SELECT p.nombre_permiso, up.otorgado
    FROM Permisos p
    JOIN UsuariosPermisos up ON p.id = up.permiso_id
    WHERE up.usuario_id = ?
    ''', (usuario_id,))

    permisos_individuales = cursor.fetchall()
    conn.close()

    permisos_finales = set(permisos_del_rol) # Empezamos con los permisos del rol

    for permiso_individual in permisos_individuales:
        if permiso_individual['otorgado']:
            permisos_finales.add(permiso_individual['nombre_permiso'])
        else: # Si está explícitamente revocado (otorgado=0)
            if permiso_individual['nombre_permiso'] in permisos_finales:
                permisos_finales.remove(permiso_individual['nombre_permiso'])

    return permisos_finales

def tiene_permiso(usuario_id, nombre_permiso):
    permisos_usuario = obtener_permisos_usuario(usuario_id)
    return nombre_permiso in permisos_usuario

# --- Funciones de RolesPermisos ---
def asignar_permiso_a_rol(rol, nombre_permiso):
    permiso_id = obtener_permiso_id_por_nombre(nombre_permiso)
    if not permiso_id:
        print(f"Permiso {nombre_permiso} no existe.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO RolesPermisos (rol, permiso_id) VALUES (?, ?)", (rol, permiso_id))
        conn.commit()
        return True
    finally:
        conn.close()

def revocar_permiso_de_rol(rol, nombre_permiso):
    permiso_id = obtener_permiso_id_por_nombre(nombre_permiso)
    if not permiso_id:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM RolesPermisos WHERE rol = ? AND permiso_id = ?", (rol, permiso_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

# --- Inicialización de datos ---
def inicializar_datos_base():
    # Crear usuario administrador por defecto si no existe
    if not obtener_usuario_por_nombre('usuario'):
        crear_usuario('usuario', 'admin', 'administrador',
                      'Nombre de tu primera mascota', 'Max',
                      'Ciudad donde naciste', 'CDMX')
        print("Usuario 'usuario' (admin) creado con contraseña 'admin'.")

    admin_user = obtener_usuario_por_nombre('usuario')
    if admin_user:
        # Asignar todos los permisos al rol 'administrador' si no están ya
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre_permiso FROM Permisos")
        todos_los_permisos = [row['nombre_permiso'] for row in cursor.fetchall()]
        conn.close()

        for permiso in todos_los_permisos:
            asignar_permiso_a_rol('administrador', permiso)
        print(f"Permisos asignados al rol 'administrador'.")

        # Asignar algunos permisos básicos al rol 'empleado'
        permisos_empleado = ['realizar_ventas', 'ver_dashboard_ventas']
        for permiso in permisos_empleado:
            asignar_permiso_a_rol('empleado', permiso)
        print(f"Permisos básicos asignados al rol 'empleado'.")


if __name__ == '__main__':
    # Este bloque se ejecuta solo si se corre models.py directamente.
    # Útil para inicializar o probar.
    import os
    # Si la base de datos no existe, database_setup.py debería haberla creado.
    # Si existe, simplemente nos conectamos.
    if not os.path.exists(DATABASE_NAME):
        print(f"La base de datos {DATABASE_NAME} no existe. Ejecute database_setup.py primero.")
    else:
        inicializar_datos_base()

        # Pruebas básicas (opcional, comentar/eliminar después)
        print("\n--- Probando Funciones del Modelo ---")

        # Verificar admin
        admin = verificar_credenciales('usuario', 'admin')
        if admin:
            print(f"Login admin exitoso: {admin}")
            admin_id = admin['id']

            # Obtener permisos del admin
            permisos_admin = obtener_permisos_usuario(admin_id)
            print(f"Permisos del admin ({admin['nombre_usuario']}): {permisos_admin}")
            print(f"Admin tiene permiso 'administrar_usuarios': {tiene_permiso(admin_id, 'administrar_usuarios')}")
            print(f"Admin tiene permiso 'realizar_ventas': {tiene_permiso(admin_id, 'realizar_ventas')}")

            # Crear un empleado de prueba
            if not obtener_usuario_por_nombre('empleado_test'):
                empleado_id = crear_usuario('empleado_test', '1234', 'empleado', 'Color favorito', 'Azul', 'Comida favorita', 'Pizza')
                if empleado_id:
                    print(f"Usuario 'empleado_test' creado con ID: {empleado_id}")
            else:
                empleado_test_user = obtener_usuario_por_nombre('empleado_test')
                empleado_id = empleado_test_user['id']
                print(f"Usuario 'empleado_test' ya existe con ID: {empleado_id}")


            if empleado_id:
                # Verificar empleado
                empleado_login = verificar_credenciales('empleado_test', '1234')
                print(f"Login empleado_test exitoso: {empleado_login}")

                # Obtener permisos del empleado
                permisos_empleado = obtener_permisos_usuario(empleado_id)
                print(f"Permisos de empleado_test: {permisos_empleado}")
                print(f"Empleado tiene permiso 'administrar_usuarios': {tiene_permiso(empleado_id, 'administrar_usuarios')}")
                print(f"Empleado tiene permiso 'realizar_ventas': {tiene_permiso(empleado_id, 'realizar_ventas')}")

                # Admin otorga un permiso adicional al empleado
                print(f"\nAdmin otorgando 'gestionar_stock' a empleado_test...")
                asignar_permiso_usuario(empleado_id, 'gestionar_stock', otorgado=True)
                permisos_empleado_mod = obtener_permisos_usuario(empleado_id)
                print(f"Nuevos permisos de empleado_test: {permisos_empleado_mod}")
                print(f"Empleado ahora tiene permiso 'gestionar_stock': {tiene_permiso(empleado_id, 'gestionar_stock')}")

                # Admin revoca un permiso (que ya tenía por rol) al empleado
                print(f"\nAdmin revocando 'realizar_ventas' a empleado_test (aunque lo tenga por rol)...")
                asignar_permiso_usuario(empleado_id, 'realizar_ventas', otorgado=False)
                permisos_empleado_mod_2 = obtener_permisos_usuario(empleado_id)
                print(f"Nuevos permisos de empleado_test: {permisos_empleado_mod_2}")
                print(f"Empleado ahora tiene permiso 'realizar_ventas': {tiene_permiso(empleado_id, 'realizar_ventas')}")


            # Listar usuarios
            print("\nUsuarios actuales:")
            for u in listar_usuarios():
                print(u)
        else:
            print("Fallo login admin")

        # Pruebas de recuperación de contraseña
        user_for_recovery = obtener_usuario_por_nombre('usuario')
        if user_for_recovery:
            print(f"\nProbando recuperación para 'usuario':")
            preguntas = obtener_preguntas_seguridad('usuario')
            # print(f"Preguntas: {preguntas}") # Comentado para reducir verbosidad
            if preguntas and preguntas['pregunta_1'] and preguntas['pregunta_2']:
                es_valido = verificar_respuestas_seguridad('usuario', 'Max', 'CDMX')
                # print(f"Verificación con respuestas correctas: {es_valido}")
                if es_valido:
                    cambiar_contrasena('usuario', 'nuevapass')
                    # print("Contraseña cambiada a 'nuevapass'. Intentando login...")
                    verif_nueva = verificar_credenciales('usuario', 'nuevapass')
                    # print(f"Login con nueva pass: {verif_nueva}")
                    cambiar_contrasena('usuario', 'admin')
                    # print("Contraseña revertida a 'admin'.")
                es_valido_incorrecto = verificar_respuestas_seguridad('usuario', 'Incorrecta1', 'Incorrecta2')
                # print(f"Verificación con respuestas incorrectas: {es_valido_incorrecto}")
            # else:
                # print("El usuario 'usuario' no tiene preguntas de seguridad configuradas para probar la recuperación.")
        # else:
            # print("Usuario 'usuario' no encontrado para prueba de recuperación.")

# --- Funciones de Categorías ---
def crear_categoria(nombre_categoria, descripcion=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Categorias (nombre_categoria, descripcion) VALUES (?, ?)", (nombre_categoria, descripcion))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # nombre_categoria es UNIQUE
        return None
    finally:
        conn.close()

def obtener_categoria_por_id(categoria_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Categorias WHERE id = ?", (categoria_id,))
    categoria = cursor.fetchone()
    conn.close()
    return dict(categoria) if categoria else None

def listar_categorias():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Categorias ORDER BY nombre_categoria")
    categorias = cursor.fetchall()
    conn.close()
    return [dict(cat) for cat in categorias]

def actualizar_categoria(categoria_id, nombre_categoria=None, descripcion=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields_to_update = []
    params = []
    if nombre_categoria is not None:
        fields_to_update.append("nombre_categoria = ?")
        params.append(nombre_categoria)
    if descripcion is not None: # Permitir vaciar descripción
        fields_to_update.append("descripcion = ?")
        params.append(descripcion)

    if not fields_to_update:
        return False

    params.append(categoria_id)
    query = f"UPDATE Categorias SET {', '.join(fields_to_update)} WHERE id = ?"
    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def eliminar_categoria(categoria_id):
    # Considerar si hay productos asociados. ON DELETE SET NULL en la FK lo maneja en DB.
    # Podríamos añadir una comprobación aquí si se quisiera prevenir la eliminación.
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Categorias WHERE id = ?", (categoria_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e: # Podría ser IntegrityError si hay FKs restrictivas (no es el caso aquí)
        print(f"Error al eliminar categoría: {e}")
        return False
    finally:
        conn.close()

# --- Funciones de Proveedores ---
def crear_proveedor(nombre_proveedor, contacto_principal=None, telefono=None, email=None, direccion=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO Proveedores (nombre_proveedor, contacto_principal, telefono, email, direccion)
                          VALUES (?, ?, ?, ?, ?)''', (nombre_proveedor, contacto_principal, telefono, email, direccion))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # Por la constraint UNIQUE(nombre_proveedor, telefono)
        return None
    finally:
        conn.close()

def obtener_proveedor_por_id(proveedor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Proveedores WHERE id = ?", (proveedor_id,))
    proveedor = cursor.fetchone()
    conn.close()
    return dict(proveedor) if proveedor else None

def listar_proveedores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Proveedores ORDER BY nombre_proveedor")
    proveedores = cursor.fetchall()
    conn.close()
    return [dict(prov) for prov in proveedores]

def actualizar_proveedor(proveedor_id, nombre_proveedor=None, contacto_principal=None, telefono=None, email=None, direccion=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = []
    params = []
    if nombre_proveedor is not None: fields.append("nombre_proveedor = ?"); params.append(nombre_proveedor)
    if contacto_principal is not None: fields.append("contacto_principal = ?"); params.append(contacto_principal)
    if telefono is not None: fields.append("telefono = ?"); params.append(telefono)
    if email is not None: fields.append("email = ?"); params.append(email)
    if direccion is not None: fields.append("direccion = ?"); params.append(direccion)

    if not fields: return False
    params.append(proveedor_id)
    query = f"UPDATE Proveedores SET {', '.join(fields)} WHERE id = ?"
    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def eliminar_proveedor(proveedor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Proveedores WHERE id = ?", (proveedor_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# --- Funciones de Productos ---
def crear_producto(nombre_producto, precio_venta_menudeo, codigo_barras=None, descripcion=None,
                   categoria_id=None, proveedor_id=None, precio_compra=0,
                   precio_venta_mayoreo=None, cantidad_para_mayoreo=None,
                   stock_actual=0, stock_minimo=0, unidad_medida='unidad'):
    conn = get_db_connection()
    cursor = conn.cursor()
    # fecha_ultima_modificacion se actualiza con un trigger o manualmente al actualizar
    try:
        cursor.execute('''
            INSERT INTO Productos (codigo_barras, nombre_producto, descripcion, categoria_id, proveedor_id,
                                 precio_compra, precio_venta_menudeo, precio_venta_mayoreo, cantidad_para_mayoreo,
                                 stock_actual, stock_minimo, unidad_medida, fecha_ultima_modificacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (codigo_barras, nombre_producto, descripcion, categoria_id, proveedor_id,
              precio_compra, precio_venta_menudeo, precio_venta_mayoreo, cantidad_para_mayoreo,
              stock_actual, stock_minimo, unidad_medida))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e: # Por codigo_barras UNIQUE
        print(f"Error de integridad al crear producto: {e}")
        return None
    finally:
        conn.close()

def obtener_producto_por_id(producto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Unir con Categorias y Proveedores para obtener nombres
    cursor.execute('''
        SELECT p.*, c.nombre_categoria, pr.nombre_proveedor
        FROM Productos p
        LEFT JOIN Categorias c ON p.categoria_id = c.id
        LEFT JOIN Proveedores pr ON p.proveedor_id = pr.id
        WHERE p.id = ? AND p.activo = TRUE
    ''', (producto_id,))
    producto = cursor.fetchone()
    conn.close()
    return dict(producto) if producto else None

def obtener_producto_por_codigo_barras(codigo_barras):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, c.nombre_categoria, pr.nombre_proveedor
        FROM Productos p
        LEFT JOIN Categorias c ON p.categoria_id = c.id
        LEFT JOIN Proveedores pr ON p.proveedor_id = pr.id
        WHERE p.codigo_barras = ? AND p.activo = TRUE
    ''', (codigo_barras,))
    producto = cursor.fetchone()
    conn.close()
    return dict(producto) if producto else None

def listar_productos(nombre=None, categoria_id=None, proveedor_id=None, stock_bajo=False, solo_activos=True, page=1, limit=25):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''SELECT p.*, c.nombre_categoria, pr.nombre_proveedor
               FROM Productos p
               LEFT JOIN Categorias c ON p.categoria_id = c.id
               LEFT JOIN Proveedores pr ON p.proveedor_id = pr.id'''
    conditions = []
    params = []

    if solo_activos:
        conditions.append("p.activo = TRUE")

    if nombre:
        conditions.append("p.nombre_producto LIKE ?")
        params.append(f"%{nombre}%")
    if categoria_id:
        conditions.append("p.categoria_id = ?")
        params.append(categoria_id)
    if proveedor_id:
        conditions.append("p.proveedor_id = ?")
        params.append(proveedor_id)
    if stock_bajo:
        conditions.append("p.stock_actual <= p.stock_minimo")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY p.nombre_producto"
    if limit:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])

    cursor.execute(query, tuple(params))
    productos = cursor.fetchall()
    conn.close()
    return [dict(prod) for prod in productos]

def actualizar_producto(producto_id, **kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()

    allowed_fields = ['codigo_barras', 'nombre_producto', 'descripcion', 'categoria_id', 'proveedor_id',
                      'precio_compra', 'precio_venta_menudeo', 'precio_venta_mayoreo', 'cantidad_para_mayoreo',
                      'stock_actual', 'stock_minimo', 'unidad_medida', 'activo']

    fields_to_update = []
    params = []

    for key, value in kwargs.items():
        if key in allowed_fields:
            fields_to_update.append(f"{key} = ?")
            params.append(value)

    if not fields_to_update:
        return False # No hay nada que actualizar

    # Siempre actualizar fecha_ultima_modificacion
    fields_to_update.append("fecha_ultima_modificacion = CURRENT_TIMESTAMP")

    params.append(producto_id)
    query = f"UPDATE Productos SET {', '.join(fields_to_update)} WHERE id = ?"

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError as e: # Ej. codigo_barras duplicado
        print(f"Error de integridad al actualizar producto: {e}")
        return False
    finally:
        conn.close()

def eliminar_producto(producto_id, suave=True): # Por defecto, eliminación suave
    if suave:
        return actualizar_producto(producto_id, activo=False)
    else: # Eliminación física (cuidado con FKs si las hubiera en otras tablas apuntando a productos)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Productos WHERE id = ?", (producto_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar físicamente producto: {e}")
            return False
        finally:
            conn.close()

def buscar_productos(nombre=None, codigo_barras=None, categoria_id=None, limit=25):
    # Wrapper simple para listar_productos, podría ser más específico.
    return listar_productos(nombre=nombre, categoria_id=categoria_id, limit=limit) # No busca por CB aquí directamente

def obtener_productos_stock_bajo(page=1, limit=25):
    return listar_productos(stock_bajo=True, page=page, limit=limit)

def registrar_movimiento_stock(producto_id, cantidad, tipo_movimiento, notas=None):
    """
    Registra una entrada o salida de stock.
    tipo_movimiento: 'entrada' o 'salida'
    cantidad: debe ser positiva.
    Retorna True si fue exitoso, False si no (ej. stock insuficiente para salida).
    """
    if cantidad <= 0: return False

    producto = obtener_producto_por_id(producto_id)
    if not producto: return False

    nuevo_stock = producto['stock_actual']
    if tipo_movimiento == 'entrada':
        nuevo_stock += cantidad
    elif tipo_movimiento == 'salida':
        if producto['stock_actual'] >= cantidad:
            nuevo_stock -= cantidad
        else:
            # print(f"Stock insuficiente para {producto['nombre_producto']}. Solicitado: {cantidad}, Disponible: {producto['stock_actual']}")
            return False # Stock insuficiente
    else:
        return False # Tipo de movimiento no válido

    # TODO: En un sistema completo, esto también se registraría en una tabla de 'MovimientosStock'
    # para auditoría: (producto_id, fecha, tipo, cantidad, usuario_id, notas)

    return actualizar_producto(producto_id, stock_actual=nuevo_stock)

# --- Funciones de Ventas ---
def registrar_nueva_venta(usuario_id, detalles_productos, total_venta, cliente_nombre=None, cliente_identificacion=None, monto_recibido=None, cambio_entregado=None, tipo_pago='efectivo', estado_venta='completada', notas=None):
    """
    Registra una nueva venta y actualiza el stock de los productos.
    detalles_productos: lista de dicts, cada uno con:
                        {'producto_id', 'cantidad', 'precio_unitario_venta', 'subtotal_linea', 'descuento_linea'(opcional)}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Iniciar transacción
        cursor.execute("BEGIN TRANSACTION")

        # 1. Insertar en Ventas
        cursor.execute('''
            INSERT INTO Ventas (usuario_id, cliente_nombre, cliente_identificacion, total_venta,
                                monto_recibido, cambio_entregado, tipo_pago, estado_venta, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (usuario_id, cliente_nombre, cliente_identificacion, total_venta,
              monto_recibido, cambio_entregado, tipo_pago, estado_venta, notas))
        venta_id = cursor.lastrowid

        if not venta_id:
            raise sqlite3.Error("No se pudo obtener el ID de la nueva venta.")

        # 2. Insertar en DetallesVenta y actualizar stock
        for item in detalles_productos:
            producto_id = item['producto_id']
            cantidad_vendida = item['cantidad']

            # Insertar detalle de venta
            cursor.execute('''
                INSERT INTO DetallesVenta (venta_id, producto_id, cantidad, precio_unitario_venta,
                                         subtotal_linea, descuento_linea)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (venta_id, producto_id, cantidad_vendida, item['precio_unitario_venta'],
                  item['subtotal_linea'], item.get('descuento_linea', 0)))

            # Actualizar stock del producto
            # Usar una subconsulta para asegurar la atomicidad de la lectura y escritura del stock
            cursor.execute('''
                UPDATE Productos
                SET stock_actual = stock_actual - ?,
                    fecha_ultima_modificacion = CURRENT_TIMESTAMP
                WHERE id = ? AND stock_actual >= ?
            ''', (cantidad_vendida, producto_id, cantidad_vendida))

            if cursor.rowcount == 0:
                # Esto significa que el stock no fue suficiente o el producto no existe (aunque debería haberse verificado antes)
                producto_info = obtener_producto_por_id(producto_id) # Para mensaje de error
                nombre_prod_error = producto_info['nombre_producto'] if producto_info else f"ID {producto_id}"
                raise sqlite3.Error(f"Stock insuficiente para el producto: {nombre_prod_error} (ID: {producto_id}) o producto no encontrado.")

        # Confirmar transacción
        conn.commit()
        return venta_id

    except sqlite3.Error as e:
        print(f"Error en transacción de venta: {e}")
        if conn:
            conn.rollback()
        return None # Indicar fallo
    finally:
        if conn:
            conn.close()

def obtener_venta_por_id(venta_id_buscada):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener datos de la venta principal
    cursor.execute('''
        SELECT v.*, u.nombre_usuario
        FROM Ventas v
        JOIN Usuarios u ON v.usuario_id = u.id
        WHERE v.id = ?
    ''', (venta_id_buscada,))
    venta_data = cursor.fetchone()

    if not venta_data:
        conn.close()
        return None

    venta_resultado = dict(venta_data)

    # Obtener detalles de la venta
    cursor.execute('''
        SELECT dv.*, p.nombre_producto, p.codigo_barras
        FROM DetallesVenta dv
        JOIN Productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
    ''', (venta_id_buscada,))
    detalles_data = cursor.fetchall()
    venta_resultado['detalles'] = [dict(d) for d in detalles_data]

    conn.close()
    return venta_resultado


def listar_ventas_modelo(fecha_inicio=None, fecha_fin=None, usuario_id_filtro=None, cliente_filtro=None, page=1, limit=25):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT v.id, v.fecha_venta, u.nombre_usuario, v.cliente_nombre, v.total_venta, v.tipo_pago, v.estado_venta
        FROM Ventas v
        JOIN Usuarios u ON v.usuario_id = u.id
    '''
    conditions = []
    params = []

    if fecha_inicio:
        conditions.append("date(v.fecha_venta) >= date(?)") # Comparar solo la fecha
        params.append(fecha_inicio)
    if fecha_fin:
        conditions.append("date(v.fecha_venta) <= date(?)")
        params.append(fecha_fin)
    if usuario_id_filtro:
        conditions.append("v.usuario_id = ?")
        params.append(usuario_id_filtro)
    if cliente_filtro: # Buscar en nombre o identificación
        conditions.append("(v.cliente_nombre LIKE ? OR v.cliente_identificacion LIKE ?)")
        params.append(f"%{cliente_filtro}%")
        params.append(f"%{cliente_filtro}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY v.fecha_venta DESC" # Más recientes primero

    # Para contar total de registros para paginación (antes de aplicar LIMIT/OFFSET)
    count_query = query.replace("v.id, v.fecha_venta, u.nombre_usuario, v.cliente_nombre, v.total_venta, v.tipo_pago, v.estado_venta", "COUNT(*)")
    cursor.execute(count_query, tuple(params))
    total_registros = cursor.fetchone()[0]

    if limit:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])

    cursor.execute(query, tuple(params))
    ventas = cursor.fetchall()
    conn.close()

    return {
        "ventas": [dict(v) for v in ventas],
        "total_registros": total_registros,
        "pagina_actual": page,
        "total_paginas": (total_registros + limit - 1) // limit if limit > 0 else 1
    }

# --- Funciones para Reportes ---
def obtener_resumen_ventas_periodo(fecha_inicio, fecha_fin):
    """
    Calcula el total de ventas, número de transacciones y desglose por tipo de pago
    para un período dado.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query_resumen = '''
        SELECT
            COUNT(id) as numero_transacciones,
            SUM(total_venta) as total_ventas_periodo,
            AVG(total_venta) as venta_promedio
        FROM Ventas
        WHERE date(fecha_venta) BETWEEN date(?) AND date(?)
        AND estado_venta = 'completada'
    '''
    cursor.execute(query_resumen, (fecha_inicio, fecha_fin))
    resumen = cursor.fetchone()

    query_tipo_pago = '''
        SELECT tipo_pago, SUM(total_venta) as total_por_tipo, COUNT(id) as transacciones_por_tipo
        FROM Ventas
        WHERE date(fecha_venta) BETWEEN date(?) AND date(?)
        AND estado_venta = 'completada'
        GROUP BY tipo_pago
    '''
    cursor.execute(query_tipo_pago, (fecha_inicio, fecha_fin))
    desglose_tipo_pago = [dict(row) for row in cursor.fetchall()]

    # Para obtener la lista detallada de ventas (opcional, para Excel)
    # query_detalle_ventas = '''
    #     SELECT v.id, v.fecha_venta, u.nombre_usuario, v.cliente_nombre, v.total_venta, v.tipo_pago
    #     FROM Ventas v
    #     JOIN Usuarios u ON v.usuario_id = u.id
    #     WHERE date(v.fecha_venta) BETWEEN date(?) AND date(?) AND v.estado_venta = 'completada'
    #     ORDER BY v.fecha_venta
    # '''
    # cursor.execute(query_detalle_ventas, (fecha_inicio, fecha_fin))
    # ventas_detalladas = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "resumen": dict(resumen) if resumen else {"numero_transacciones":0, "total_ventas_periodo":0, "venta_promedio":0},
        "desglose_tipo_pago": desglose_tipo_pago,
        # "ventas_detalladas": ventas_detalladas
    }

def obtener_productos_mas_vendidos(fecha_inicio, fecha_fin, top_n=10):
    """
    Obtiene los N productos más vendidos por cantidad y por valor total.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Por cantidad
    query_por_cantidad = '''
        SELECT p.id, p.codigo_barras, p.nombre_producto, SUM(dv.cantidad) as total_cantidad_vendida
        FROM DetallesVenta dv
        JOIN Productos p ON dv.producto_id = p.id
        JOIN Ventas v ON dv.venta_id = v.id
        WHERE date(v.fecha_venta) BETWEEN date(?) AND date(?) AND v.estado_venta = 'completada'
        GROUP BY p.id, p.nombre_producto
        ORDER BY total_cantidad_vendida DESC
        LIMIT ?
    '''
    cursor.execute(query_por_cantidad, (fecha_inicio, fecha_fin, top_n))
    top_por_cantidad = [dict(row) for row in cursor.fetchall()]

    # Por valor total
    query_por_valor = '''
        SELECT p.id, p.codigo_barras, p.nombre_producto, SUM(dv.subtotal_linea) as total_valor_vendido
        FROM DetallesVenta dv
        JOIN Productos p ON dv.producto_id = p.id
        JOIN Ventas v ON dv.venta_id = v.id
        WHERE date(v.fecha_venta) BETWEEN date(?) AND date(?) AND v.estado_venta = 'completada'
        GROUP BY p.id, p.nombre_producto
        ORDER BY total_valor_vendido DESC
        LIMIT ?
    '''
    cursor.execute(query_por_valor, (fecha_inicio, fecha_fin, top_n))
    top_por_valor = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {
        "top_por_cantidad": top_por_cantidad,
        "top_por_valor": top_por_valor
    }

def obtener_ventas_agrupadas_por_usuario(fecha_inicio, fecha_fin):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT u.nombre_usuario, COUNT(v.id) as numero_ventas, SUM(v.total_venta) as total_vendido_por_usuario
        FROM Ventas v
        JOIN Usuarios u ON v.usuario_id = u.id
        WHERE date(v.fecha_venta) BETWEEN date(?) AND date(?) AND v.estado_venta = 'completada'
        GROUP BY u.id, u.nombre_usuario
        ORDER BY total_vendido_por_usuario DESC
    '''
    cursor.execute(query, (fecha_inicio, fecha_fin))
    ventas_por_usuario = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ventas_por_usuario

# --- Funciones para Importación de Productos desde Excel ---
def procesar_fila_producto_excel(fila_datos, es_actualizacion=False):
    """
    Procesa una fila de datos de producto desde un archivo Excel.
    Crea o actualiza un producto.
    fila_datos: dict donde las claves son los nombres de las columnas del Excel.
    es_actualizacion: bool, si es True, se espera un 'id' o 'codigo_barras' para actualizar.
    Retorna: un dict con {'status': 'creado'/'actualizado'/'error', 'id': product_id, 'nombre': nombre, 'mensaje': ...}
    """
    # Mapeo esperado de columnas Excel a campos de la DB (ajustar según formato definido)
    # Se asume que el Excel tendrá nombres de columna que podemos mapear.
    # Es CRUCIAL que el formato del Excel sea consistente.
    try:
        nombre_producto = fila_datos.get('Nombre Producto')
        if not nombre_producto:
            return {'status': 'error', 'mensaje': 'Falta Nombre Producto'}

        codigo_barras = fila_datos.get('Código Barras') # Puede ser None/vacío

        # Obtener IDs de categoría y proveedor si se proveen nombres
        categoria_id = None
        nombre_cat = fila_datos.get('Categoría')
        if nombre_cat:
            # Intentar buscar categoría por nombre. Si no existe, ¿se crea o se ignora? Por ahora, se ignora.
            # En una implementación robusta, se podría tener una opción para crearla.
            cats = listar_categorias() # Podría optimizarse para no llamar siempre
            for cat_dict in cats:
                if cat_dict['nombre_categoria'].lower() == nombre_cat.lower():
                    categoria_id = cat_dict['id']
                    break
            # if not categoria_id: print(f"Advertencia: Categoría '{nombre_cat}' no encontrada para producto '{nombre_producto}'.")

        proveedor_id = None
        nombre_prov = fila_datos.get('Proveedor')
        if nombre_prov:
            provs = listar_proveedores() # Podría optimizarse
            for prov_dict in provs:
                if prov_dict['nombre_proveedor'].lower() == nombre_prov.lower():
                    proveedor_id = prov_dict['id']
                    break
            # if not proveedor_id: print(f"Advertencia: Proveedor '{nombre_prov}' no encontrada para producto '{nombre_producto}'.")

        # Convertir precios y stocks, manejando errores de tipo
        try:
            precio_compra = float(fila_datos.get('Precio Compra', 0) or 0)
            precio_venta_menudeo = float(fila_datos.get('Precio Venta', 0) or 0)
            precio_venta_mayoreo = float(fila_datos.get('Precio Mayoreo', 0) or 0) if fila_datos.get('Precio Mayoreo') else None
            cantidad_para_mayoreo = int(fila_datos.get('Cant. Mayoreo', 0) or 0) if fila_datos.get('Cant. Mayoreo') else None
            stock_actual = int(fila_datos.get('Stock Actual', 0) or 0)
            stock_minimo = int(fila_datos.get('Stock Mínimo', 0) or 0)
        except ValueError:
            return {'status': 'error', 'mensaje': f"Error de formato numérico en precios o stock para '{nombre_producto}'"}

        producto_data = {
            'nombre_producto': nombre_producto,
            'codigo_barras': codigo_barras if codigo_barras else None, # Asegurar None si está vacío
            'descripcion': fila_datos.get('Descripción'),
            'categoria_id': categoria_id,
            'proveedor_id': proveedor_id,
            'precio_compra': precio_compra,
            'precio_venta_menudeo': precio_venta_menudeo,
            'precio_venta_mayoreo': precio_venta_mayoreo,
            'cantidad_para_mayoreo': cantidad_para_mayoreo,
            'stock_actual': stock_actual,
            'stock_minimo': stock_minimo,
            'unidad_medida': fila_datos.get('Unidad Medida', 'unidad'),
            'activo': str(fila_datos.get('Activo', 'Sí')).lower() in ['sí', 'si', 'true', '1', 'yes']
        }

        producto_existente = None
        # Lógica para actualizar: buscar por ID o código de barras
        # Asumimos que si se proporciona un ID en el Excel, es para actualizar ese ID.
        # Si no hay ID pero sí código de barras, se busca por código de barras.
        id_excel = fila_datos.get('ID')
        if id_excel:
            try:
                producto_existente = obtener_producto_por_id(int(id_excel)) # Para la actualización, no importa si está activo o no.
                                                                        #listar_productos(solo_activos=False) podría ser mejor
            except ValueError:
                return {'status': 'error', 'mensaje': f"ID '{id_excel}' inválido para producto '{nombre_producto}'"}

        if not producto_existente and codigo_barras: # Si no se encontró por ID pero hay CB
            # Necesitamos una función que busque por CB sin importar estado 'activo' para actualizar
            conn_temp = get_db_connection()
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT * FROM Productos WHERE codigo_barras = ?", (codigo_barras,))
            prod_row = cursor_temp.fetchone()
            conn_temp.close()
            if prod_row:
                producto_existente = dict(prod_row)

        if producto_existente: # Actualizar
            # No actualizamos el stock_actual directamente aquí, eso se haría con movimientos de stock.
            # La importación podría ser para actualizar precios, descripciones, etc.
            # Opcionalmente, se podría tener una columna "Ajuste de Stock" en el Excel.
            # Por ahora, el stock_actual del Excel sobreescribirá el existente si se quiere actualizar.

            # Quitar campos que no se deben actualizar masivamente o que son None y no queremos que borren datos existentes
            update_data_clean = {k: v for k, v in producto_data.items() if v is not None or k in ['descripcion', 'precio_venta_mayoreo', 'cantidad_para_mayoreo']} # Permitir None para estos
            if 'codigo_barras' in update_data_clean and not update_data_clean['codigo_barras']: # Si CB es vacío, no actualizarlo.
                del update_data_clean['codigo_barras']


            if actualizar_producto(producto_existente['id'], **update_data_clean):
                return {'status': 'actualizado', 'id': producto_existente['id'], 'nombre': nombre_producto, 'mensaje': 'Actualizado correctamente'}
            else:
                return {'status': 'error', 'id': producto_existente['id'], 'nombre': nombre_producto, 'mensaje': 'Error al actualizar (posiblemente código de barras duplicado con otro producto)'}
        else: # Crear nuevo
            if not producto_data.get('precio_venta_menudeo'): # Precio venta es mandatorio para crear
                 return {'status': 'error', 'mensaje': f"Precio Venta Menudeo requerido para nuevo producto '{nombre_producto}'"}

            nuevo_id = crear_producto(**producto_data)
            if nuevo_id:
                return {'status': 'creado', 'id': nuevo_id, 'nombre': nombre_producto, 'mensaje': 'Creado correctamente'}
            else:
                return {'status': 'error', 'nombre': nombre_producto, 'mensaje': 'Error al crear (posiblemente código de barras ya existe o datos faltantes)'}

    except Exception as e:
        return {'status': 'error', 'mensaje': f"Error procesando fila para '{fila_datos.get('Nombre Producto', 'Desconocido')}': {e}"}
