BEGIN TRANSACTION;
CREATE TABLE Categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_categoria TEXT UNIQUE NOT NULL,
        descripcion TEXT
    );
INSERT INTO "Categorias" VALUES(2,'Panadería',NULL);
CREATE TABLE DetallesVenta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario_venta REAL NOT NULL, -- Precio al momento de la venta
        subtotal_linea REAL NOT NULL, -- cantidad * precio_unitario_venta (después de descuentos de línea si los hubiera)
        descuento_linea REAL DEFAULT 0, -- Monto del descuento aplicado a esta línea específica
        FOREIGN KEY (venta_id) REFERENCES Ventas(id) ON DELETE CASCADE, -- Si se borra una venta, se borran sus detalles
        FOREIGN KEY (producto_id) REFERENCES Productos(id) ON DELETE RESTRICT -- No permitir borrar producto si está en un detalle de venta
    );
CREATE TABLE Permisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_permiso TEXT UNIQUE NOT NULL
        -- Ejemplos: 'gestionar_stock', 'realizar_ventas', 'generar_reportes_ventas',
        -- 'administrar_usuarios', 'modificar_configuracion_app',
        -- 'exportar_datos_productos', 'importar_datos_productos',
        -- 'exportar_bd', 'importar_bd', 'ver_dashboard_ventas'
    );
INSERT INTO "Permisos" VALUES(1,'gestionar_stock');
INSERT INTO "Permisos" VALUES(2,'realizar_ventas');
INSERT INTO "Permisos" VALUES(3,'generar_reportes_ventas');
INSERT INTO "Permisos" VALUES(4,'administrar_usuarios');
INSERT INTO "Permisos" VALUES(5,'modificar_configuracion_app');
INSERT INTO "Permisos" VALUES(6,'exportar_datos_productos');
INSERT INTO "Permisos" VALUES(7,'importar_datos_productos');
INSERT INTO "Permisos" VALUES(8,'exportar_bd');
INSERT INTO "Permisos" VALUES(9,'importar_bd');
INSERT INTO "Permisos" VALUES(10,'ver_dashboard_ventas');
INSERT INTO "Permisos" VALUES(11,'acceder_panel_administracion');
INSERT INTO "Permisos" VALUES(23,'gestionar_inventario');
INSERT INTO "Permisos" VALUES(24,'ver_inventario');
INSERT INTO "Permisos" VALUES(25,'ajustar_stock');
INSERT INTO "Permisos" VALUES(26,'gestionar_categorias');
INSERT INTO "Permisos" VALUES(27,'gestionar_proveedores');
INSERT INTO "Permisos" VALUES(28,'ver_precio_compra');
INSERT INTO "Permisos" VALUES(47,'cancelar_ventas');
INSERT INTO "Permisos" VALUES(48,'ver_historial_ventas_propias');
INSERT INTO "Permisos" VALUES(49,'ver_historial_ventas_todas');
INSERT INTO "Permisos" VALUES(50,'aplicar_descuentos_venta');
CREATE TABLE Productos (
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
    );
INSERT INTO "Productos" VALUES(1,'750000123','Leche Entera Lala 1L',NULL,1,1,18.0,25.0,NULL,NULL,65,0,'unidad','2025-06-29 04:11:54','2025-06-29 04:11:54',0);
CREATE TABLE Proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_proveedor TEXT NOT NULL,
        contacto_principal TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        UNIQUE (nombre_proveedor, telefono) -- Evitar duplicados básicos
    );
CREATE TABLE RolesPermisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rol TEXT NOT NULL,
        permiso_id INTEGER NOT NULL,
        FOREIGN KEY (permiso_id) REFERENCES Permisos(id),
        UNIQUE (rol, permiso_id)
    );
INSERT INTO "RolesPermisos" VALUES(1,'administrador',1);
INSERT INTO "RolesPermisos" VALUES(2,'administrador',2);
INSERT INTO "RolesPermisos" VALUES(3,'administrador',3);
INSERT INTO "RolesPermisos" VALUES(4,'administrador',4);
INSERT INTO "RolesPermisos" VALUES(5,'administrador',5);
INSERT INTO "RolesPermisos" VALUES(6,'administrador',6);
INSERT INTO "RolesPermisos" VALUES(7,'administrador',7);
INSERT INTO "RolesPermisos" VALUES(8,'administrador',8);
INSERT INTO "RolesPermisos" VALUES(9,'administrador',9);
INSERT INTO "RolesPermisos" VALUES(10,'administrador',10);
INSERT INTO "RolesPermisos" VALUES(11,'administrador',11);
INSERT INTO "RolesPermisos" VALUES(12,'empleado',2);
INSERT INTO "RolesPermisos" VALUES(13,'empleado',10);
INSERT INTO "RolesPermisos" VALUES(25,'administrador',23);
INSERT INTO "RolesPermisos" VALUES(26,'administrador',24);
INSERT INTO "RolesPermisos" VALUES(27,'administrador',25);
INSERT INTO "RolesPermisos" VALUES(28,'administrador',26);
INSERT INTO "RolesPermisos" VALUES(29,'administrador',27);
INSERT INTO "RolesPermisos" VALUES(30,'administrador',28);
INSERT INTO "RolesPermisos" VALUES(69,'administrador',47);
INSERT INTO "RolesPermisos" VALUES(70,'administrador',48);
INSERT INTO "RolesPermisos" VALUES(71,'administrador',49);
INSERT INTO "RolesPermisos" VALUES(72,'administrador',50);
CREATE TABLE Usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT UNIQUE NOT NULL,
        hash_contrasena TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('administrador', 'empleado')),
        pregunta_seguridad_1 TEXT,
        respuesta_seguridad_1 TEXT,
        pregunta_seguridad_2 TEXT,
        respuesta_seguridad_2 TEXT
    );
INSERT INTO "Usuarios" VALUES(1,'usuario','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918','administrador','Nombre de tu primera mascota','Max','Ciudad donde naciste','CDMX');
INSERT INTO "Usuarios" VALUES(2,'empleado_test','03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4','empleado','Color favorito','Azul','Comida favorita','Pizza');
CREATE TABLE UsuariosPermisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        permiso_id INTEGER NOT NULL,
        otorgado BOOLEAN NOT NULL DEFAULT 1, -- 1 para otorgado, 0 para revocado
        FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (permiso_id) REFERENCES Permisos(id) ON DELETE CASCADE,
        UNIQUE (usuario_id, permiso_id)
    );
INSERT INTO "UsuariosPermisos" VALUES(13,2,1,1);
INSERT INTO "UsuariosPermisos" VALUES(14,2,2,0);
CREATE TABLE Ventas (
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
    );
CREATE INDEX idx_productos_nombre ON Productos (nombre_producto);
CREATE INDEX idx_productos_categoria_id ON Productos (categoria_id);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('Permisos',50);
INSERT INTO "sqlite_sequence" VALUES('Usuarios',7);
INSERT INTO "sqlite_sequence" VALUES('RolesPermisos',97);
INSERT INTO "sqlite_sequence" VALUES('UsuariosPermisos',20);
INSERT INTO "sqlite_sequence" VALUES('Categorias',2);
INSERT INTO "sqlite_sequence" VALUES('Proveedores',1);
INSERT INTO "sqlite_sequence" VALUES('Productos',1);
COMMIT;
