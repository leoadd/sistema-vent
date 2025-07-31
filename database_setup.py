import sqlite3

def crear_tablas():
    conn = sqlite3.connect('pos_database.db')
    cursor = conn.cursor()

    # Tabla Usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT UNIQUE NOT NULL,
        hash_contrasena TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('administrador', 'empleado')),
        pregunta_seguridad_1 TEXT,
        respuesta_seguridad_1 TEXT,
        pregunta_seguridad_2 TEXT,
        respuesta_seguridad_2 TEXT
    )
    ''')

    # Tabla Permisos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Permisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_permiso TEXT UNIQUE NOT NULL
        -- Ejemplos: 'gestionar_stock', 'realizar_ventas', 'generar_reportes_ventas',
        -- 'administrar_usuarios', 'modificar_configuracion_app',
        -- 'exportar_datos_productos', 'importar_datos_productos',
        -- 'exportar_bd', 'importar_bd', 'ver_dashboard_ventas'
    )
    ''')

    # Tabla RolesPermisos (Junta los roles con sus permisos por defecto)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS RolesPermisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rol TEXT NOT NULL,
        permiso_id INTEGER NOT NULL,
        FOREIGN KEY (permiso_id) REFERENCES Permisos(id),
        UNIQUE (rol, permiso_id)
    )
    ''')

    # Tabla UsuariosPermisos (Permisos individuales que sobreescriben o complementan los del rol)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS UsuariosPermisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        permiso_id INTEGER NOT NULL,
        otorgado BOOLEAN NOT NULL DEFAULT 1, -- 1 para otorgado, 0 para revocado
        FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (permiso_id) REFERENCES Permisos(id) ON DELETE CASCADE,
        UNIQUE (usuario_id, permiso_id)
    )
    ''')

    # Insertar permisos base si no existen
    permisos_base = [
        'gestionar_stock', 'realizar_ventas', 'generar_reportes_ventas',
        'administrar_usuarios', 'modificar_configuracion_app',
        'exportar_datos_productos', 'importar_datos_productos',
        'exportar_bd', 'importar_bd', 'ver_dashboard_ventas',
        'acceder_panel_administracion' # Permiso general para acceder a funciones de admin
    ]

    for permiso in permisos_base:
        cursor.execute("INSERT OR IGNORE INTO Permisos (nombre_permiso) VALUES (?)", (permiso,))

    # --- Nuevas Tablas para Inventario ---

    # Tabla Categorias
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_categoria TEXT UNIQUE NOT NULL,
        descripcion TEXT
    )
    ''')

    # Tabla Proveedores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_proveedor TEXT NOT NULL,
        contacto_principal TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        UNIQUE (nombre_proveedor, telefono) -- Evitar duplicados básicos
    )
    ''')

    # Tabla Productos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_barras TEXT UNIQUE, -- Puede ser NULL si el producto no tiene, pero si existe debe ser único
        nombre_producto TEXT NOT NULL,
        descripcion TEXT,
        categoria_id INTEGER,
        proveedor_id INTEGER,
        precio_compra REAL NOT NULL DEFAULT 0,
        precio_venta_menudeo REAL NOT NULL,
        precio_venta_mayoreo REAL,
        cantidad_para_mayoreo INTEGER,
        stock_actual INTEGER NOT NULL DEFAULT 0,
        stock_minimo INTEGER DEFAULT 0,
        unidad_medida TEXT DEFAULT 'unidad', -- Ej: 'unidad', 'kg', 'lt', 'pqt'
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_ultima_modificacion TIMESTAMP,
        activo BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (categoria_id) REFERENCES Categorias(id) ON DELETE SET NULL, -- Si se borra categoría, el producto queda sin categoría
        FOREIGN KEY (proveedor_id) REFERENCES Proveedores(id) ON DELETE SET NULL  -- Si se borra proveedor, el producto queda sin proveedor
    )
    ''')
    # Crear índices para búsquedas comunes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON Productos (nombre_producto)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_categoria_id ON Productos (categoria_id)")


    # Nuevos permisos para inventario
    permisos_inventario = [
        'gestionar_inventario', # Permiso general para CRUD de productos, categorías, proveedores
        'ver_inventario',       # Permiso para solo ver productos y stock
        'ajustar_stock',        # Permiso específico para modificar stock (entradas/salidas manuales)
        'gestionar_categorias',
        'gestionar_proveedores',
        'ver_precio_compra'     # Permiso para ver el costo de los productos
    ]
    for permiso in permisos_inventario:
        cursor.execute("INSERT OR IGNORE INTO Permisos (nombre_permiso) VALUES (?)", (permiso,))

    # --- Nuevas Tablas para Ventas ---

    # Tabla Ventas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        usuario_id INTEGER NOT NULL,
        cliente_nombre TEXT,
        cliente_identificacion TEXT, -- Ej. RFC o Cédula
        total_venta REAL NOT NULL,
        monto_recibido REAL,
        cambio_entregado REAL,
        tipo_pago TEXT CHECK(tipo_pago IN ('efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'otro')),
        estado_venta TEXT DEFAULT 'completada' CHECK(estado_venta IN ('completada', 'cancelada', 'pendiente_pago', 'en_proceso')),
        notas TEXT,
        FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
    )
    ''')

    # Tabla DetallesVenta
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DetallesVenta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario_venta REAL NOT NULL, -- Precio al momento de la venta
        subtotal_linea REAL NOT NULL, -- cantidad * precio_unitario_venta (después de descuentos de línea si los hubiera)
        descuento_linea REAL DEFAULT 0, -- Monto del descuento aplicado a esta línea específica
        FOREIGN KEY (venta_id) REFERENCES Ventas(id) ON DELETE CASCADE, -- Si se borra una venta, se borran sus detalles
        FOREIGN KEY (producto_id) REFERENCES Productos(id) ON DELETE RESTRICT -- No permitir borrar producto si está en un detalle de venta
    )
    ''') # ON DELETE RESTRICT para producto_id es importante para integridad referencial.
        # Se podría optar por SET NULL si se permite que los productos sean "borrados" (inactivados).
        # Pero si un producto se elimina físicamente, es mejor que las ventas históricas fallen o se manejen.
        # Dado que tenemos `activo` en Productos, un producto inactivo aún podría estar en ventas antiguas.

    # Nuevos permisos para Ventas
    permisos_ventas = [
        'realizar_ventas', # Ya existe, pero lo ponemos aquí para agrupar mentalmente
        'cancelar_ventas',
        'ver_historial_ventas_propias',
        'ver_historial_ventas_todas', # Ver ventas de todos los usuarios
        'aplicar_descuentos_venta'
    ]
    for permiso in permisos_ventas:
        # El permiso 'realizar_ventas' ya fue insertado, INSERT OR IGNORE lo manejará.
        cursor.execute("INSERT OR IGNORE INTO Permisos (nombre_permiso) VALUES (?)", (permiso,))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    crear_tablas()
    print("Base de datos y tablas creadas/verificadas exitosamente en 'pos_database.db'")
