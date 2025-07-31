import models

# Estado de la aplicación (simulado, en una app real esto podría estar en una clase AppState o similar)
# El ID del usuario logueado y sus permisos se cargarían aquí tras un login exitoso.
# La vista (Flet) llamaría a estas funciones del controlador.

def intentar_login(nombre_usuario, contrasena):
    """
    Intenta loguear a un usuario.
    Retorna: dict con info del usuario si es exitoso, None si falla.
    """
    usuario_data = models.verificar_credenciales(nombre_usuario, contrasena)
    if usuario_data:
        # Aquí podrías cargar el estado global de la app, ej:
        # app_state.set_logged_in_user(usuario_data['id'], usuario_data['rol'])
        # app_state.set_user_permissions(models.obtener_permisos_usuario(usuario_data['id']))
        print(f"Controlador: Login exitoso para {nombre_usuario}")
        return usuario_data
    else:
        print(f"Controlador: Fallo de login para {nombre_usuario}")
        return None

def iniciar_recuperacion_contrasena(nombre_usuario):
    """
    Obtiene las preguntas de seguridad para un usuario.
    Retorna: dict con preguntas si el usuario existe y tiene preguntas, None si no.
    """
    usuario = models.obtener_usuario_por_nombre(nombre_usuario)
    if usuario and usuario['pregunta_seguridad_1'] and usuario['pregunta_seguridad_2']:
        return {
            'id_usuario': usuario['id'], # Aunque no se use directamente en este paso, es bueno tenerlo
            'nombre_usuario': usuario['nombre_usuario'],
            'pregunta_1': usuario['pregunta_seguridad_1'],
            'pregunta_2': usuario['pregunta_seguridad_2']
        }
    return None

def verificar_respuestas_y_establecer_nueva_contrasena(nombre_usuario, respuesta_1, respuesta_2, nueva_contrasena):
    """
    Verifica las respuestas de seguridad y, si son correctas, cambia la contraseña.
    Retorna: True si todo fue exitoso, False en caso contrario.
    """
    if models.verificar_respuestas_seguridad(nombre_usuario, respuesta_1, respuesta_2):
        if models.cambiar_contrasena(nombre_usuario, nueva_contrasena):
            print(f"Controlador: Contraseña cambiada exitosamente para {nombre_usuario}")
            return True
        else:
            print(f"Controlador: Error al cambiar la contraseña para {nombre_usuario} (después de verificar respuestas)")
            return False
    else:
        print(f"Controlador: Respuestas de seguridad incorrectas para {nombre_usuario}")
        return False

# --- Funciones para Administradores ---

def crear_nuevo_usuario_admin(admin_id, nombre_usuario_nuevo, contrasena_nuevo, rol_nuevo,
                              pregunta1=None, respuesta1=None, pregunta2=None, respuesta2=None):
    """
    Permite a un administrador crear un nuevo usuario.
    Retorna: ID del nuevo usuario si es exitoso, None si falla o no tiene permiso.
    """
    if not models.tiene_permiso(admin_id, 'administrar_usuarios'):
        print(f"Controlador: Usuario {admin_id} no tiene permiso para crear usuarios.")
        return None

    nuevo_id = models.crear_usuario(nombre_usuario_nuevo, contrasena_nuevo, rol_nuevo,
                                   pregunta1, respuesta1, pregunta2, respuesta2)
    if nuevo_id:
        print(f"Controlador: Usuario '{nombre_usuario_nuevo}' creado con ID {nuevo_id} por admin {admin_id}.")
        # Si el nuevo rol es 'administrador', asegurarse de que herede los permisos base del rol
        if rol_nuevo == 'administrador':
            permisos_rol_admin = models.obtener_permisos_por_rol_base('administrador')
            # No es necesario asignar explícitamente aquí si `obtener_permisos_usuario` ya considera el rol.
            # Si quisiéramos copiar los permisos del rol a UsuariosPermisos, se haría aquí.
            print(f"Controlador: Nuevo admin '{nombre_usuario_nuevo}' hereda permisos de rol 'administrador'.")
        return nuevo_id
    else:
        print(f"Controlador: Error al crear usuario '{nombre_usuario_nuevo}'.")
        return None

def listar_todos_los_usuarios_admin(admin_id):
    """
    Permite a un administrador listar todos los usuarios.
    Retorna: lista de usuarios si tiene permiso, None si no.
    """
    if not models.tiene_permiso(admin_id, 'administrar_usuarios'):
        print(f"Controlador: Usuario {admin_id} no tiene permiso para listar usuarios.")
        return None
    return models.listar_usuarios()

def obtener_detalles_usuario_admin(admin_id, usuario_a_ver_id):
    """
    Permite a un administrador ver detalles de un usuario específico.
    Retorna: dict con info del usuario si tiene permiso, None si no.
    """
    if not models.tiene_permiso(admin_id, 'administrar_usuarios'):
        print(f"Controlador: Usuario {admin_id} no tiene permiso para ver detalles de otros usuarios.")
        return None

    usuario = models.obtener_usuario_por_id(usuario_a_ver_id)
    if usuario:
        # Convertir sqlite3.Row a dict para facilitar su uso
        return dict(usuario)
    return None


def modificar_usuario_admin(admin_id, usuario_id_a_modificar, nombre_usuario=None, rol=None,
                            pregunta1=None, respuesta1=None, pregunta2=None, respuesta2=None, nueva_contrasena=None):
    """
    Permite a un administrador modificar datos de un usuario, incluyendo resetear contraseña.
    Retorna: True si la modificación fue exitosa, False si no o no tiene permiso.
    """
    if not models.tiene_permiso(admin_id, 'administrar_usuarios'):
        print(f"Controlador: Usuario {admin_id} no tiene permiso para modificar usuarios.")
        return False

    # Actualizar datos básicos
    actualizado = models.actualizar_info_usuario(usuario_id_a_modificar, nombre_usuario, rol,
                                                pregunta1, respuesta1, pregunta2, respuesta2)

    # Si se provee una nueva contraseña, cambiarla también
    if nueva_contrasena:
        # Necesitamos el nombre de usuario para cambiar la contraseña con la función actual de models
        usuario_actual = models.obtener_usuario_por_id(usuario_id_a_modificar)
        if usuario_actual:
            nombre_usuario_para_pass = nombre_usuario if nombre_usuario else usuario_actual['nombre_usuario']
            cambio_pass = models.cambiar_contrasena(nombre_usuario_para_pass, nueva_contrasena)
            actualizado = actualizado or cambio_pass # Es exitoso si cualquiera de las operaciones lo fue
        else: # No debería pasar si el usuario_id_a_modificar es válido
            print(f"Controlador: Error, no se encontró usuario {usuario_id_a_modificar} para resetear contraseña.")
            return False

    if actualizado:
        print(f"Controlador: Usuario ID {usuario_id_a_modificar} modificado por admin {admin_id}.")
    else:
        print(f"Controlador: No se realizaron cambios o falló la modificación para usuario ID {usuario_id_a_modificar}.")
    return actualizado


def eliminar_usuario_admin(admin_id, usuario_id_a_eliminar):
    """
    Permite a un administrador eliminar un usuario.
    Retorna: True si la eliminación fue exitosa, False si no o no tiene permiso.
    """
    if not models.tiene_permiso(admin_id, 'administrar_usuarios'):
        print(f"Controlador: Usuario {admin_id} no tiene permiso para eliminar usuarios.")
        return False

    # Lógica de negocio adicional: No permitir eliminar al único administrador.
    # O no permitir que un admin se elimine a sí mismo si es el único.
    # Esta lógica puede volverse compleja. Por ahora, una verificación simple:
    if admin_id == usuario_id_a_eliminar:
        usuario_actual = models.obtener_usuario_por_id(admin_id)
        if usuario_actual and usuario_actual['rol'] == 'administrador':
            admins = [u for u in models.listar_usuarios() if u['rol'] == 'administrador']
            if len(admins) <= 1:
                print(f"Controlador: No se puede eliminar al único administrador o a sí mismo si es el único.")
                return False

    if models.eliminar_usuario(usuario_id_a_eliminar):
        print(f"Controlador: Usuario ID {usuario_id_a_eliminar} eliminado por admin {admin_id}.")
        return True
    else:
        print(f"Controlador: Error al eliminar usuario ID {usuario_id_a_eliminar}.")
        return False

def obtener_permisos_de_usuario_admin(admin_id, usuario_id_objetivo):
    """
    Admin obtiene la lista de todos los permisos posibles y cuáles tiene el usuario objetivo.
    Retorna: un dict {'todos_los_permisos': [...], 'permisos_usuario': set(...)} o None.
    """
    if not models.tiene_permiso(admin_id, 'administrar_usuarios'):
        print(f"Controlador: Usuario {admin_id} no tiene permiso para ver permisos.")
        return None

    conn = models.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_permiso FROM Permisos ORDER BY nombre_permiso")
    todos_los_permisos_db = [row['nombre_permiso'] for row in cursor.fetchall()]
    conn.close()

    permisos_del_usuario = models.obtener_permisos_usuario(usuario_id_objetivo)

    return {
        'todos_los_permisos': todos_los_permisos_db,
        'permisos_usuario': permisos_del_usuario
    }

def gestionar_permiso_usuario_admin(admin_id, usuario_id_objetivo, nombre_permiso, otorgar):
    """
    Admin otorga o revoca un permiso específico a un usuario.
    Retorna: True si la operación fue exitosa, False si no o no tiene permiso.
    """
    if not models.tiene_permiso(admin_id, 'administrar_usuarios'):
        print(f"Controlador: Usuario {admin_id} no tiene permiso para gestionar permisos.")
        return False

    if otorgar:
        return models.asignar_permiso_usuario(usuario_id_objetivo, nombre_permiso, otorgado=True)
    else:
        # Aquí hay una decisión de diseño: revocar explícitamente vs. quitar de UsuariosPermisos.
        # Si queremos que la ausencia en UsuariosPermisos signifique que hereda del rol,
        # entonces revocar significaría insertar con otorgado=False.
        # Si queremos que la ausencia signifique "no tiene el permiso", entonces revocar sería eliminar la fila.
        # El modelo actual con `asignar_permiso_usuario(..., otorgado=False)` establece explícitamente
        # que no lo tiene, incluso si el rol sí lo daría. Esto es más granular.
        return models.asignar_permiso_usuario(usuario_id_objetivo, nombre_permiso, otorgado=False)


# --- Funciones para el propio usuario logueado ---
def cambiar_contrasena_propia(usuario_id, contrasena_actual, nueva_contrasena):
    """
    Permite al usuario logueado cambiar su propia contraseña.
    """
    usuario = models.obtener_usuario_por_id(usuario_id)
    if not usuario:
        return "Usuario no encontrado."

    # Verificar contraseña actual
    if models.verificar_credenciales(usuario['nombre_usuario'], contrasena_actual):
        if models.cambiar_contrasena(usuario['nombre_usuario'], nueva_contrasena):
            return "Contraseña cambiada exitosamente."
        else:
            return "Error al cambiar la contraseña."
    else:
        return "La contraseña actual es incorrecta."

def actualizar_preguntas_seguridad_propias(usuario_id, contrasena_actual, p1, r1, p2, r2):
    """
    Permite al usuario logueado cambiar sus propias preguntas/respuestas de seguridad.
    Requiere contraseña actual para confirmar identidad.
    """
    usuario = models.obtener_usuario_por_id(usuario_id)
    if not usuario:
        return "Usuario no encontrado."

    if models.verificar_credenciales(usuario['nombre_usuario'], contrasena_actual):
        if models.actualizar_info_usuario(usuario_id, pregunta_seguridad_1=p1, respuesta_seguridad_1=r1, pregunta_seguridad_2=p2, respuesta_seguridad_2=r2):
            return "Preguntas y respuestas de seguridad actualizadas."
        else:
            return "Error al actualizar las preguntas y respuestas."
    else:
        return "La contraseña actual es incorrecta."


if __name__ == '__main__':
    print("--- Probando Funciones del Controlador ---")
    # Asegurarse de que la base de datos y el usuario admin existen
    # models.inicializar_datos_base() # Ya se ejecuta si models.py se corre solo.

    # Simular login admin
    admin_data = intentar_login('usuario', 'admin')
    if admin_data:
        admin_id_logueado = admin_data['id']
        print(f"Admin '{admin_data['nombre_usuario']}' (ID: {admin_id_logueado}) logueado.")

        # 1. Admin crea un nuevo empleado
        print("\n1. Admin creando empleado 'empleado_ctrl_test'...")
        nuevo_empleado_id = crear_nuevo_usuario_admin(
            admin_id_logueado, 'empleado_ctrl_test', 'password123', 'empleado',
            'Color', 'Rojo', 'Animal', 'Gato'
        )
        if nuevo_empleado_id:
            print(f"Empleado 'empleado_ctrl_test' creado con ID: {nuevo_empleado_id}")

            # 2. Admin lista usuarios
            print("\n2. Admin listando usuarios...")
            usuarios = listar_todos_los_usuarios_admin(admin_id_logueado)
            if usuarios:
                for u in usuarios: print(f"  - {u}")

            # 3. Admin obtiene detalles del nuevo empleado
            print(f"\n3. Admin obteniendo detalles de empleado ID {nuevo_empleado_id}...")
            detalles_empleado = obtener_detalles_usuario_admin(admin_id_logueado, nuevo_empleado_id)
            if detalles_empleado:
                print(f"  Detalles: {detalles_empleado}")

            # 4. Admin modifica al empleado (cambia rol a admin)
            print(f"\n4. Admin modificando empleado ID {nuevo_empleado_id} a rol 'administrador'...")
            modificado = modificar_usuario_admin(admin_id_logueado, nuevo_empleado_id, rol='administrador', nueva_contrasena='newpass123')
            if modificado:
                detalles_mod = obtener_detalles_usuario_admin(admin_id_logueado, nuevo_empleado_id)
                print(f"  Empleado modificado: {detalles_mod}")
                # Verificar login con nueva contraseña
                intento_login_mod = intentar_login(detalles_mod['nombre_usuario'], 'newpass123')
                print(f"  Intento de login para usuario modificado: {'Exitoso' if intento_login_mod else 'Fallido'}")


            # 5. Admin gestiona permisos del (ahora) nuevo admin
            print(f"\n5. Admin gestionando permisos para el nuevo admin (ID: {nuevo_empleado_id})...")
            permisos_info = obtener_permisos_de_usuario_admin(admin_id_logueado, nuevo_empleado_id)
            if permisos_info:
                print(f"  Permisos actuales de '{detalles_mod['nombre_usuario']}': {permisos_info['permisos_usuario']}")

                # Otorgar un permiso que podría no tener (aunque como admin ya debería tenerlos todos por rol)
                # Para probar, vamos a revocar uno que sí debería tener por rol de admin y luego otorgarlo de nuevo
                print(f"  Revocando 'gestionar_stock' a '{detalles_mod['nombre_usuario']}'...")
                gestionar_permiso_usuario_admin(admin_id_logueado, nuevo_empleado_id, 'gestionar_stock', otorgar=False)
                permisos_info_despues_revocar = obtener_permisos_de_usuario_admin(admin_id_logueado, nuevo_empleado_id)
                print(f"  Permisos después de revocar 'gestionar_stock': {permisos_info_despues_revocar['permisos_usuario']}")

                print(f"  Otorgando de nuevo 'gestionar_stock' a '{detalles_mod['nombre_usuario']}'...")
                gestionar_permiso_usuario_admin(admin_id_logueado, nuevo_empleado_id, 'gestionar_stock', otorgar=True)
                permisos_info_despues_otorgar = obtener_permisos_de_usuario_admin(admin_id_logueado, nuevo_empleado_id)
                print(f"  Permisos después de otorgar 'gestionar_stock': {permisos_info_despues_otorgar['permisos_usuario']}")


            # 6. Probar recuperación de contraseña para el empleado_ctrl_test (ahora admin)
            print(f"\n6. Probando recuperación de contraseña para '{detalles_mod['nombre_usuario']}'...")
            info_recup = iniciar_recuperacion_contrasena(detalles_mod['nombre_usuario'])
            if info_recup:
                print(f"  Preguntas para '{info_recup['nombre_usuario']}': {info_recup['pregunta_1']}, {info_recup['pregunta_2']}")
                recup_exitosa = verificar_respuestas_y_establecer_nueva_contrasena(
                    info_recup['nombre_usuario'], 'Rojo', 'Gato', 'recoveredpass'
                )
                if recup_exitosa:
                    print(f"  Recuperación exitosa. Nueva contraseña: 'recoveredpass'")
                    intento_login_recup = intentar_login(info_recup['nombre_usuario'], 'recoveredpass')
                    print(f"  Intento de login post-recuperación: {'Exitoso' if intento_login_recup else 'Fallido'}")

            # 7. Admin elimina al usuario 'empleado_ctrl_test'
            print(f"\n7. Admin eliminando usuario '{detalles_mod['nombre_usuario']}' (ID: {nuevo_empleado_id})...")
            eliminado = eliminar_usuario_admin(admin_id_logueado, nuevo_empleado_id)
            if eliminado:
                print(f"  Usuario '{detalles_mod['nombre_usuario']}' eliminado.")
                usuarios_final = listar_todos_los_usuarios_admin(admin_id_logueado)
                if usuarios_final:
                    print("  Usuarios restantes:")
                    for u in usuarios_final: print(f"    - {u}")
        else:
            print("Fallo al crear 'empleado_ctrl_test'.")

        # 8. Usuario 'usuario' (admin) cambia su propia contraseña
        print("\n8. Usuario 'usuario' cambiando su propia contraseña...")
        resultado_cambio_pass = cambiar_contrasena_propia(admin_id_logueado, 'admin', 'admin123')
        print(f"  Resultado: {resultado_cambio_pass}")
        if "exitosa" in resultado_cambio_pass:
            # Verificar login con nueva contraseña
            intento_login_propio = intentar_login('usuario', 'admin123')
            print(f"  Intento de login con 'admin123': {'Exitoso' if intento_login_propio else 'Fallido'}")
            # Revertir para no afectar otras pruebas
            cambiar_contrasena_propia(admin_id_logueado, 'admin123', 'admin')
            print("  Contraseña de 'usuario' revertida a 'admin'.")

        # 9. Usuario 'usuario' (admin) cambia sus preguntas de seguridad
        print("\n9. Usuario 'usuario' cambiando sus preguntas de seguridad...")
        resultado_cambio_preguntas = actualizar_preguntas_seguridad_propias(
            admin_id_logueado, 'admin',
            'Nueva Pregunta 1', 'Nueva Respuesta 1',
            'Nueva Pregunta 2', 'Nueva Respuesta 2'
        )
        print(f"  Resultado: {resultado_cambio_preguntas}")
        if "actualizadas" in resultado_cambio_preguntas:
            detalles_usuario_actualizado = obtener_detalles_usuario_admin(admin_id_logueado, admin_id_logueado)
            print(f"  Nuevas preguntas/respuestas (parcial): P1='{detalles_usuario_actualizado['pregunta_seguridad_1']}', R1='{detalles_usuario_actualizado['respuesta_seguridad_1']}'")
            # Revertir
            actualizar_preguntas_seguridad_propias(admin_id_logueado, 'admin', 'Nombre de tu primera mascota', 'Max', 'Ciudad donde naciste', 'CDMX')
            print("  Preguntas de 'usuario' revertidas.")

    else:
        print("Fallo de login inicial del admin 'usuario'. Revisar models.py o base de datos.")

    # Prueba de no poder eliminar al único admin
    admin_data_test_elim = intentar_login('usuario', 'admin')
    if admin_data_test_elim:
        admin_id_test_elim = admin_data_test_elim['id']
        print(f"\nIntentando eliminar al admin '{admin_data_test_elim['nombre_usuario']}' (ID: {admin_id_test_elim}) por él mismo (debería fallar si es el único)...")
        # Asegurarse de que no haya otros admins creados por pruebas anteriores que no se hayan borrado
        # Por simplicidad, asumimos que 'usuario' es el único admin en este punto de las pruebas si las anteriores limpiaron bien.
        resultado_auto_eliminacion = eliminar_usuario_admin(admin_id_test_elim, admin_id_test_elim)
        print(f"Resultado del intento de auto-eliminación del único admin: {'Falló como se esperaba' if not resultado_auto_eliminacion else 'Error, se eliminó'}")

    else:
        print("No se pudo loguear como admin para la prueba de eliminación.")

# --- Controladores para Inventario ---

# Categorías
def crear_nueva_categoria_admin(admin_id, nombre_categoria, descripcion=None):
    if not models.tiene_permiso(admin_id, 'gestionar_categorias') and not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    cat_id = models.crear_categoria(nombre_categoria, descripcion)
    if cat_id:
        return {"id": cat_id, "nombre_categoria": nombre_categoria, "descripcion": descripcion}
    return {"error": "Error al crear categoría (posiblemente ya existe)"}

def obtener_todas_las_categorias_usuario(usuario_id): # Puede ser admin o empleado con permiso de ver
    if not models.tiene_permiso(usuario_id, 'ver_inventario') and not models.tiene_permiso(usuario_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    return models.listar_categorias()

def actualizar_categoria_admin(admin_id, categoria_id, nombre_categoria=None, descripcion=None):
    if not models.tiene_permiso(admin_id, 'gestionar_categorias') and not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    if models.actualizar_categoria(categoria_id, nombre_categoria, descripcion):
        return {"success": True, "mensaje": "Categoría actualizada"}
    return {"error": "Error al actualizar categoría"}

def eliminar_categoria_admin(admin_id, categoria_id):
    if not models.tiene_permiso(admin_id, 'gestionar_categorias') and not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    # Podríamos verificar si hay productos en esta categoría antes de eliminar
    productos_en_categoria = models.listar_productos(categoria_id=categoria_id, limit=1)
    if productos_en_categoria:
        return {"error": "No se puede eliminar. Existen productos asociados a esta categoría."}
    if models.eliminar_categoria(categoria_id):
        return {"success": True, "mensaje": "Categoría eliminada"}
    return {"error": "Error al eliminar categoría"}

# Proveedores
def crear_nuevo_proveedor_admin(admin_id, nombre_proveedor, contacto=None, telefono=None, email=None, direccion=None):
    if not models.tiene_permiso(admin_id, 'gestionar_proveedores') and not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    prov_id = models.crear_proveedor(nombre_proveedor, contacto, telefono, email, direccion)
    if prov_id:
        return {"id": prov_id, "nombre_proveedor": nombre_proveedor}
    return {"error": "Error al crear proveedor"}

def obtener_todos_los_proveedores_usuario(usuario_id):
    if not models.tiene_permiso(usuario_id, 'ver_inventario') and not models.tiene_permiso(usuario_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    return models.listar_proveedores()

def actualizar_proveedor_admin(admin_id, proveedor_id, **kwargs):
    if not models.tiene_permiso(admin_id, 'gestionar_proveedores') and not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    if models.actualizar_proveedor(proveedor_id, **kwargs):
        return {"success": True, "mensaje": "Proveedor actualizado"}
    return {"error": "Error al actualizar proveedor"}

def eliminar_proveedor_admin(admin_id, proveedor_id):
    if not models.tiene_permiso(admin_id, 'gestionar_proveedores') and not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    # Verificar si hay productos asociados
    productos_del_proveedor = models.listar_productos(proveedor_id=proveedor_id, limit=1)
    if productos_del_proveedor:
        return {"error": "No se puede eliminar. Existen productos asociados a este proveedor."}
    if models.eliminar_proveedor(proveedor_id):
        return {"success": True, "mensaje": "Proveedor eliminado"}
    return {"error": "Error al eliminar proveedor"}

# Productos
def crear_nuevo_producto_admin(admin_id, **kwargs):
    if not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    # 'nombre_producto' y 'precio_venta_menudeo' son obligatorios en el modelo
    if not kwargs.get('nombre_producto') or kwargs.get('precio_venta_menudeo') is None:
        return {"error": "Nombre del producto y precio de venta menudeo son requeridos."}

    prod_id = models.crear_producto(**kwargs)
    if prod_id:
        return {"id": prod_id, "nombre_producto": kwargs.get('nombre_producto')}
    return {"error": "Error al crear producto (posiblemente código de barras duplicado o datos faltantes)"}

def obtener_productos_para_vista(usuario_id, page=1, limit=25, nombre_filtro=None, categoria_id_filtro=None):
    if not models.tiene_permiso(usuario_id, 'ver_inventario') and not models.tiene_permiso(usuario_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}

    # Determinar si el usuario puede ver el precio de compra
    puede_ver_costo = models.tiene_permiso(usuario_id, 'ver_precio_compra') or \
                      models.tiene_permiso(usuario_id, 'gestionar_inventario') # Admin/gestor de inventario siempre ve costo

    productos_db = models.listar_productos(
        nombre=nombre_filtro,
        categoria_id=categoria_id_filtro,
        page=page,
        limit=limit
    )

    productos_vista = []
    if isinstance(productos_db, list): # Asegurarse que es una lista (no un dict de error)
        for prod in productos_db:
            prod_dict = dict(prod) # Convertir Row a dict
            if not puede_ver_costo:
                prod_dict.pop('precio_compra', None) # Remover precio_compra si no tiene permiso
            productos_vista.append(prod_dict)
        return productos_vista
    return productos_db # Devolver el error si lo hubo


def obtener_detalles_producto_admin(admin_id, producto_id):
    if not models.tiene_permiso(admin_id, 'gestionar_inventario'): # Solo admin/gestor puede ver todos los detalles para editar
        # Un usuario con 'ver_inventario' podría tener una función más restringida
        return {"error": "Permiso denegado"}
    producto = models.obtener_producto_por_id(producto_id)
    return producto if producto else {"error": "Producto no encontrado"}


def actualizar_producto_admin(admin_id, producto_id, **kwargs):
    if not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    if models.actualizar_producto(producto_id, **kwargs):
        return {"success": True, "mensaje": "Producto actualizado"}
    return {"error": "Error al actualizar producto"}

def eliminar_producto_admin(admin_id, producto_id): # Eliminación suave por defecto
    if not models.tiene_permiso(admin_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    if models.eliminar_producto(producto_id, suave=True): # Usar eliminación suave
        return {"success": True, "mensaje": "Producto marcado como inactivo"}
    return {"error": "Error al eliminar producto"}

def registrar_entrada_stock_usuario(usuario_id, producto_id, cantidad, notas=None):
    if not models.tiene_permiso(usuario_id, 'ajustar_stock') and not models.tiene_permiso(usuario_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    if cantidad <=0: return {"error": "La cantidad debe ser positiva."}

    if models.registrar_movimiento_stock(producto_id, cantidad, 'entrada', notas):
        nuevo_stock_info = models.obtener_producto_por_id(producto_id)
        return {"success": True, "mensaje": "Entrada de stock registrada.", "nuevo_stock": nuevo_stock_info['stock_actual'] if nuevo_stock_info else "N/A"}
    return {"error": "Error al registrar entrada de stock."}

# Nota: La salida de stock se manejará principalmente a través del módulo de Ventas.
# Una función para ajuste manual de salida podría ser:
def registrar_ajuste_salida_stock_usuario(usuario_id, producto_id, cantidad, notas):
    if not models.tiene_permiso(usuario_id, 'ajustar_stock') and not models.tiene_permiso(usuario_id, 'gestionar_inventario'):
        return {"error": "Permiso denegado"}
    if cantidad <=0: return {"error": "La cantidad debe ser positiva."}
    if not notas: return {"error": "Se requiere una nota o justificación para el ajuste de salida."}

    producto_actual = models.obtener_producto_por_id(producto_id)
    if not producto_actual: return {"error": "Producto no encontrado."}
    if producto_actual['stock_actual'] < cantidad: return {"error": f"Stock insuficiente. Disponible: {producto_actual['stock_actual']}"}

    if models.registrar_movimiento_stock(producto_id, cantidad, 'salida', f"AJUSTE MANUAL: {notas}"):
        nuevo_stock_info = models.obtener_producto_por_id(producto_id)
        return {"success": True, "mensaje": "Ajuste de salida de stock registrado.", "nuevo_stock": nuevo_stock_info['stock_actual'] if nuevo_stock_info else "N/A"}
    return {"error": "Error al registrar ajuste de salida de stock."}

# --- Controladores para Ventas ---
def procesar_nueva_venta_usuario(usuario_id, carrito_items, total_calculado_carrito, **kwargs):
    """
    Procesa una nueva venta.
    carrito_items: lista de dicts con {'producto_id', 'cantidad', 'precio_unitario_actual', 'nombre_producto'}
                   'precio_unitario_actual' es el precio del producto al momento de agregarlo al carrito.
    kwargs puede incluir: cliente_nombre, cliente_identificacion, monto_recibido, tipo_pago, notas
    """
    if not models.tiene_permiso(usuario_id, 'realizar_ventas'):
        return {"error": "Permiso denegado para realizar ventas."}
    if not carrito_items:
        return {"error": "El carrito está vacío."}

    detalles_para_db = []
    subtotal_general = 0

    # Validar stock y preparar detalles para la base de datos
    for item_carrito in carrito_items:
        producto_db = models.obtener_producto_por_id(item_carrito['producto_id'])
        if not producto_db:
            return {"error": f"Producto '{item_carrito.get('nombre_producto', 'Desconocido')}' no encontrado en la base de datos."}
        if producto_db['stock_actual'] < item_carrito['cantidad']:
            return {"error": f"Stock insuficiente para '{producto_db['nombre_producto']}'. Disponible: {producto_db['stock_actual']}, Solicitado: {item_carrito['cantidad']}."}

        precio_venta_final = item_carrito['precio_unitario_actual'] # Podría incluir lógica de mayoreo aquí si se desea
        # Ejemplo de lógica de mayoreo (si no se manejó al agregar al carrito):
        # if producto_db.get('cantidad_para_mayoreo') and item_carrito['cantidad'] >= producto_db['cantidad_para_mayoreo'] and producto_db.get('precio_venta_mayoreo'):
        #     precio_venta_final = producto_db['precio_venta_mayoreo']

        subtotal_linea_calculado = item_carrito['cantidad'] * precio_venta_final
        subtotal_general += subtotal_linea_calculado

        detalles_para_db.append({
            'producto_id': item_carrito['producto_id'],
            'cantidad': item_carrito['cantidad'],
            'precio_unitario_venta': precio_venta_final, # Precio al que se vende realmente
            'subtotal_linea': subtotal_linea_calculado,
            # 'descuento_linea': 0 # Asumir 0 por ahora, se podría añadir lógica
        })

    # Verificar si el total_calculado_carrito (que podría tener descuentos generales) coincide con el subtotal_general
    # Por ahora, usaremos el total_calculado_carrito que viene de la UI.
    # En un sistema más complejo, se recalcularía aquí o se validaría estrictamente.

    monto_recibido = kwargs.get('monto_recibido')
    cambio_entregado = None
    if monto_recibido is not None and kwargs.get('tipo_pago') == 'efectivo':
        try:
            monto_recibido_float = float(monto_recibido)
            if monto_recibido_float < total_calculado_carrito:
                return {"error": "El monto recibido es menor que el total de la venta."}
            cambio_entregado = monto_recibido_float - total_calculado_carrito
        except ValueError:
            return {"error": "Monto recibido inválido."}

    venta_id = models.registrar_nueva_venta(
        usuario_id=usuario_id,
        detalles_productos=detalles_para_db,
        total_venta=total_calculado_carrito, # Usar el total que ya podría incluir descuentos globales
        cliente_nombre=kwargs.get('cliente_nombre'),
        cliente_identificacion=kwargs.get('cliente_identificacion'),
        monto_recibido=monto_recibido,
        cambio_entregado=cambio_entregado,
        tipo_pago=kwargs.get('tipo_pago', 'efectivo'),
        estado_venta=kwargs.get('estado_venta', 'completada'),
        notas=kwargs.get('notas')
    )

    if venta_id:
        return {"success": True, "venta_id": venta_id, "cambio": cambio_entregado, "mensaje": "Venta registrada exitosamente."}
    else:
        # El modelo ya imprime el error específico de SQLite, aquí un mensaje genérico.
        return {"error": "Error al registrar la venta en la base de datos. Verifique el stock o contacte al administrador."}


def obtener_historial_ventas_usuario(usuario_id_solicitante, **kwargs_filtros):
    """
    Obtiene el historial de ventas.
    Si el usuario tiene permiso 'ver_historial_ventas_todas', puede ver todas.
    Sino, solo sus propias ventas (si tiene 'ver_historial_ventas_propias').
    kwargs_filtros: fecha_inicio, fecha_fin, cliente_filtro, page, limit, usuario_id_filtro (este último solo si tiene permiso_todas)
    """
    puede_ver_todas = models.tiene_permiso(usuario_id_solicitante, 'ver_historial_ventas_todas')
    puede_ver_propias = models.tiene_permiso(usuario_id_solicitante, 'ver_historial_ventas_propias')

    if not puede_ver_todas and not puede_ver_propias:
        return {"error": "Permiso denegado para ver historial de ventas."}

    filtros_modelo = {
        "fecha_inicio": kwargs_filtros.get('fecha_inicio'),
        "fecha_fin": kwargs_filtros.get('fecha_fin'),
        "cliente_filtro": kwargs_filtros.get('cliente_filtro'),
        "page": kwargs_filtros.get('page', 1),
        "limit": kwargs_filtros.get('limit', 25)
    }

    if puede_ver_todas:
        # Si se especificó un usuario para filtrar Y tiene permiso para ver todas, se aplica.
        if 'usuario_id_filtro' in kwargs_filtros:
            filtros_modelo['usuario_id_filtro'] = kwargs_filtros['usuario_id_filtro']
    else: # Solo puede ver propias, forzar el filtro de usuario_id
        filtros_modelo['usuario_id_filtro'] = usuario_id_solicitante
        # Ignorar cualquier intento de filtrar por otro usuario si no tiene permiso_todas
        if 'usuario_id_filtro' in kwargs_filtros and kwargs_filtros['usuario_id_filtro'] != usuario_id_solicitante:
            print(f"Advertencia: Usuario {usuario_id_solicitante} intentó filtrar por usuario {kwargs_filtros['usuario_id_filtro']} sin permiso 'ver_historial_ventas_todas'. Se listarán solo propias.")


    resultado = models.listar_ventas_modelo(**filtros_modelo)
    return resultado # Devuelve el dict con 'ventas', 'total_registros', etc.

def obtener_detalles_venta_usuario(usuario_id_solicitante, venta_id_buscada):
    # Para ver detalles, se asume que si puede ver la lista de ventas, puede ver el detalle.
    # Podría requerir un permiso más específico si fuera necesario.
    puede_ver_todas = models.tiene_permiso(usuario_id_solicitante, 'ver_historial_ventas_todas')
    puede_ver_propias = models.tiene_permiso(usuario_id_solicitante, 'ver_historial_ventas_propias')

    if not puede_ver_todas and not puede_ver_propias:
        return {"error": "Permiso denegado para ver detalles de venta."}

    venta_detalle = models.obtener_venta_por_id(venta_id_buscada)

    if not venta_detalle:
        return {"error": "Venta no encontrada."}

    # Si no puede ver todas, verificar que sea una venta propia
    if not puede_ver_todas and venta_detalle['usuario_id'] != usuario_id_solicitante:
        return {"error": "Permiso denegado para ver detalles de esta venta."}

    return venta_detalle

# --- Controladores para Reportes ---
def generar_reporte_ventas_periodo_ctrl(usuario_id, fecha_inicio, fecha_fin):
    if not models.tiene_permiso(usuario_id, 'generar_reportes_ventas'):
        return {"error": "Permiso denegado para generar reportes."}

    # Validar fechas (básico)
    if not fecha_inicio or not fecha_fin:
        return {"error": "Fechas de inicio y fin son requeridas."}
    # Aquí podrían ir validaciones más complejas de formato de fecha.

    datos_reporte = models.obtener_resumen_ventas_periodo(fecha_inicio, fecha_fin)
    # El controlador podría enriquecer o transformar estos datos si fuera necesario
    # antes de pasarlos al generador de archivos.
    return datos_reporte

def generar_reporte_productos_mas_vendidos_ctrl(usuario_id, fecha_inicio, fecha_fin, top_n=10):
    if not models.tiene_permiso(usuario_id, 'generar_reportes_ventas'):
        return {"error": "Permiso denegado."}
    if not fecha_inicio or not fecha_fin:
        return {"error": "Fechas de inicio y fin son requeridas."}
    try:
        top_n_int = int(top_n)
        if top_n_int <= 0: raise ValueError()
    except ValueError:
        return {"error": "Top N debe ser un número positivo."}

    datos_reporte = models.obtener_productos_mas_vendidos(fecha_inicio, fecha_fin, top_n_int)
    return datos_reporte

def generar_reporte_ventas_por_usuario_ctrl(usuario_id_solicitante, fecha_inicio, fecha_fin):
    # Este reporte podría ser sensible, así que el permiso 'generar_reportes_ventas' es clave.
    # Adicionalmente, si no es un admin global, podría limitarse a sus propias ventas si tuviera sentido,
    # pero usualmente los reportes de "ventas por usuario" son para supervisión.
    if not models.tiene_permiso(usuario_id_solicitante, 'generar_reportes_ventas') or \
       not models.tiene_permiso(usuario_id_solicitante, 'ver_historial_ventas_todas'): # Requiere ver todas las ventas
        return {"error": "Permiso denegado para generar este reporte."}
    if not fecha_inicio or not fecha_fin:
        return {"error": "Fechas de inicio y fin son requeridas."}

    datos_reporte = models.obtener_ventas_agrupadas_por_usuario(fecha_inicio, fecha_fin)
    return datos_reporte

# --- Controladores para Importación/Exportación ---
import db_utils # Importar el nuevo módulo
import report_generator # Añadido para exportar productos

def exportar_database_completa_ctrl(usuario_id):
    if not models.tiene_permiso(usuario_id, 'exportar_bd'):
        return {"error": "Permiso denegado para exportar la base de datos."}

    filepath = db_utils.export_database_to_sql()
    if filepath:
        return {"success": True, "filepath": filepath, "mensaje": f"Base de datos exportada a {filepath}"}
    else:
        return {"error": "Ocurrió un error durante la exportación de la base de datos."}

def importar_database_desde_sql_ctrl(usuario_id, sql_filepath):
    if not models.tiene_permiso(usuario_id, 'importar_bd'):
        return {"error": "Permiso denegado para importar la base de datos."}

    # Aquí se podría añadir lógica para hacer un backup antes de importar, si se desea.
    # Por ejemplo, llamar a exportar_database_completa_ctrl y guardar la ruta del backup.

    success = db_utils.import_database_from_sql(sql_filepath)
    if success:
        # IMPORTANTE: Después de una importación, especialmente si cambia la estructura o datos críticos,
        # la aplicación podría necesitar reiniciarse o recargar ciertos datos en memoria.
        # Esta lógica no se maneja aquí, pero es una consideración para la app completa.
        return {"success": True, "mensaje": f"Base de datos importada desde {sql_filepath}. Se recomienda reiniciar la aplicación."}
    else:
        # Si se hizo backup, aquí se podría ofrecer restaurarlo o informar al usuario.
        return {"error": "Ocurrió un error durante la importación de la base de datos."}

def exportar_productos_a_excel_ctrl(usuario_id):
    if not models.tiene_permiso(usuario_id, 'exportar_datos_productos'):
        return {"error": "Permiso denegado para exportar datos de productos."}

    # Obtener todos los productos. Usar un límite muy alto o modificar listar_productos para no tener límite.
    # Por ahora, asumimos que listar_productos sin 'limit' devuelve todos, o usamos un límite grande.
    productos_data = models.listar_productos(limit=None, solo_activos=False) # Exportar activos e inactivos

    if isinstance(productos_data, list): # Asegurarse de que no es un dict de error
        # Llamar a la función de report_generator para crear el Excel
        # (Esta función se creará en el siguiente paso del plan para report_generator.py)
        try:
            # Asumimos que report_generator.generar_excel_productos existirá
            filepath = report_generator.generar_excel_productos(productos_data)
            if filepath:
                return {"success": True, "filepath": filepath, "mensaje": f"Datos de productos exportados a {filepath}"}
            else:
                return {"error": "Error al generar el archivo Excel de productos."}
        except AttributeError: # Si generar_excel_productos aún no existe en report_generator
            return {"error": "Funcionalidad de exportación de productos a Excel no implementada completamente en report_generator."}
        except Exception as e:
            return {"error": f"Error inesperado al exportar productos: {e}"}
    else:
        return {"error": "No se pudieron obtener los datos de los productos para exportar."}

def importar_productos_desde_excel_ctrl(usuario_id, excel_filepath):
    if not models.tiene_permiso(usuario_id, 'importar_datos_productos'):
        return {"error": "Permiso denegado para importar datos de productos."}

    if not os.path.exists(excel_filepath):
        return {"error": f"Archivo Excel no encontrado en: {excel_filepath}"}

    try:
        workbook = openpyxl.load_workbook(excel_filepath)
        sheet = workbook.active # Asumir la primera hoja activa

        headers = [cell.value for cell in sheet[1]] # Primera fila como cabeceras
        # Validar cabeceras esperadas (ejemplo básico)
        expected_headers = ['Nombre Producto', 'Código Barras', 'Precio Venta'] # Mínimo esperado
        if not all(h in headers for h in expected_headers):
            return {"error": f"Cabeceras faltantes o incorrectas. Se esperan al menos: {', '.join(expected_headers)}"}

        resultados_importacion = []
        productos_creados = 0
        productos_actualizados = 0
        errores_filas = 0

        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if all(cell is None for cell in row): # Saltar filas completamente vacías
                continue

            fila_dict = dict(zip(headers, row))

            # Limpiar Nones explícitos que openpyxl podría leer de celdas vacías
            fila_dict_clean = {k: v for k, v in fila_dict.items() if v is not None}

            if not fila_dict_clean.get('Nombre Producto'): # Si no hay nombre, es probable fin de datos o fila inválida
                # print(f"Fila {row_idx} sin nombre de producto, omitiendo.")
                continue

            resultado_fila = models.procesar_fila_producto_excel(fila_dict_clean)
            resultados_importacion.append({
                "fila": row_idx,
                "nombre_original": fila_dict_clean.get('Nombre Producto', 'N/A'),
                "status": resultado_fila.get('status'),
                "mensaje": resultado_fila.get('mensaje')
            })
            if resultado_fila.get('status') == 'creado':
                productos_creados += 1
            elif resultado_fila.get('status') == 'actualizado':
                productos_actualizados += 1
            elif resultado_fila.get('status') == 'error':
                errores_filas +=1

        resumen = f"Importación completada. Creados: {productos_creados}, Actualizados: {productos_actualizados}, Errores: {errores_filas}."
        return {"success": True, "mensaje": resumen, "detalles": resultados_importacion}

    except Exception as e:
        return {"error": f"Error al procesar el archivo Excel: {e}"}


if __name__ == '__main__':
    # ... (pruebas existentes) ...

    admin_data_inv = intentar_login('usuario', 'admin')
    if admin_data_inv:
        admin_id_log = admin_data_inv['id']
        # ... (pruebas de inventario existentes, se pueden comentar para brevedad si es necesario) ...

        # Pruebas de Controladores de Importación/Exportación
        print("\n--- Probando Controladores de Importación/Exportación ---")

        # Exportación DB SQL
        # ... (código de prueba de exportación SQL) ...

        # Exportación Productos Excel
        # ... (código de prueba de exportación Excel productos) ...

        # Prueba de Importación de Productos desde Excel
        # 1. Crear un archivo Excel de prueba manualmente o usando la función de exportación
        #    Nombre del archivo: 'test_import_products.xlsx' en la raíz del proyecto.
        #    Columnas: ID, Código Barras, Nombre Producto, Descripción, Categoría, Proveedor,
        #              Precio Compra, Precio Venta, Precio Mayoreo, Cant. Mayoreo,
        #              Stock Actual, Stock Mínimo, Unidad Medida, Activo
        #    Ejemplo de fila para crear: ,TESTCB001,Producto de Prueba Importado,Desc Import,LácteosCTRL,LalaCTRL,10,20,18,5,30,5,unidad,Sí
        #    Ejemplo de fila para actualizar (usar un ID o CB existente de la DB de prueba): 1,TESTCB001,Producto Actualizado por Import,Nueva Desc,,,,,,,,,,Sí

        if not models.tiene_permiso(admin_id_log, 'importar_datos_productos'):
            print("Otorgando permiso 'importar_datos_productos' al admin para prueba...")
            gestionar_permiso_usuario_admin(admin_id_log, admin_id_log, 'importar_datos_productos', otorgar=True)

        # Crear un archivo Excel de prueba para importar
        test_excel_filename = "test_import_products.xlsx"
        wb_test = openpyxl.Workbook()
        ws_test = wb_test.active
        ws_test.title = "ProductosAImportar"
        test_headers = [
            "ID", "Código Barras", "Nombre Producto", "Descripción", "Categoría", "Proveedor",
            "Precio Compra", "Precio Venta", "Precio Mayoreo", "Cant. Mayoreo",
            "Stock Actual", "Stock Mínimo", "Unidad Medida", "Activo"
        ]
        ws_test.append(test_headers)
        # Producto nuevo
        ws_test.append([None, "IMP001", "Producto Importado Nuevo", "Desc Nuevo", "LácteosCTRL", "LalaCTRL", 10.0, 15.0, None, None, 50, 5, "unidad", "Sí"])
        # Producto para actualizar (asumir que existe un producto con ID 1 o CB específico)
        # Para que la prueba de actualización funcione consistentemente, deberíamos asegurar que un producto exista.
        # Por ahora, si no existe, se creará uno nuevo si el CB es único.
        # ws_test.append([1, "750000123", "Leche Lala 1L Re-Importada", "Actualizada via Excel", "LácteosCTRL", "LalaCTRL", 18.5, 26.0, 24.0, 6, 100, 10, "unidad", "Sí"])
        wb_test.save(test_excel_filename)
        print(f"Archivo Excel de prueba '{test_excel_filename}' creado.")

        import_result_excel = importar_productos_desde_excel_ctrl(admin_id_log, test_excel_filename)
        print(f"\nResultado Importación Productos Excel: {import_result_excel.get('mensaje')}")
        if import_result_excel.get('detalles'):
            for detalle in import_result_excel.get('detalles', []):
                print(f"  - Fila {detalle['fila']}: {detalle['nombre_original']} - {detalle['status']} - {detalle['mensaje']}")

        # Limpiar archivo de prueba
        # if os.path.exists(test_excel_filename):
        #     os.remove(test_excel_filename)
        #     print(f"Archivo Excel de prueba '{test_excel_filename}' eliminado.")


    else:
        print("Fallo login admin, no se pueden probar controladores.")
