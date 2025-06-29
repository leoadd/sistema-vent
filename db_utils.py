import sqlite3
import os
from datetime import datetime

DATABASE_NAME = 'pos_database.db'
BACKUP_DIR = "backup"

def _ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def export_database_to_sql():
    """
    Genera un volcado SQL de la base de datos completa.
    Retorna la ruta al archivo SQL generado o None en caso de error.
    """
    if not os.path.exists(DATABASE_NAME):
        print(f"Error: La base de datos '{DATABASE_NAME}' no existe.")
        return None

    _ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = os.path.join(BACKUP_DIR, f"pos_backup_{timestamp}.sql")

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        with open(backup_filename, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        conn.close()
        print(f"Base de datos exportada exitosamente a: {backup_filename}")
        return backup_filename
    except Exception as e:
        print(f"Error al exportar la base de datos: {e}")
        return None

if __name__ == '__main__':
    print("Probando la exportación de la base de datos...")
    filepath = export_database_to_sql()
    if filepath:
        print(f"Prueba de exportación exitosa. Archivo generado: {os.path.abspath(filepath)}")
    else:
        print("Prueba de exportación fallida.")

def import_database_from_sql(sql_filepath):
    """
    Importa datos desde un archivo SQL a la base de datos actual.
    ADVERTENCIA: Esta operación puede ser destructiva y reemplazar datos existentes.
    Se recomienda hacer un backup antes.
    Retorna True si la importación fue exitosa, False en caso de error.
    """
    if not os.path.exists(sql_filepath):
        print(f"Error: El archivo SQL '{sql_filepath}' no existe.")
        return False

    # Opcional: Hacer un backup automático antes de importar
    # backup_path_auto = export_database_to_sql()
    # if not backup_path_auto:
    #     print("Error: No se pudo crear el backup automático antes de la importación. Operación cancelada.")
    #     return False
    # print(f"Backup automático creado en: {backup_path_auto}")

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        with open(sql_filepath, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            # SQLite3 puede ejecutar múltiples sentencias con executescript
            # Sin embargo, iterdump() genera COMMITs. Si el script de importación
            # ya tiene BEGIN TRANSACTION / COMMIT, podríamos tener problemas con executescript anidando transacciones.
            # Una forma más segura podría ser cerrar la conexión actual, renombrar/borrar la DB
            # y recrearla desde el script. Pero para una importación simple, executescript suele funcionar.
            # Por ahora, asumimos que el script SQL es un volcado estándar.

            # Para una restauración más limpia, podríamos borrar las tablas existentes primero,
            # pero esto debe hacerse con mucho cuidado y usualmente el script de dump
            # ya incluye sentencias DROP TABLE IF EXISTS.

            cursor.executescript(sql_script)
        conn.commit() # Asegurar que todos los cambios de executescript se guarden
        conn.close()
        print(f"Base de datos importada exitosamente desde: {sql_filepath}")
        return True
    except sqlite3.Error as e:
        print(f"Error al importar la base de datos desde SQL: {e}")
        # Considerar restaurar el backup automático si se implementó y la importación falló.
        return False
    except Exception as e:
        print(f"Error inesperado durante la importación: {e}")
        return False

if __name__ == '__main__':
    print("Probando la exportación de la base de datos...")
    filepath = export_database_to_sql()
    if filepath:
        print(f"Prueba de exportación exitosa. Archivo generado: {os.path.abspath(filepath)}")

        # Prueba de importación (¡CUIDADO! Esto modificará la DB actual)
        # Para una prueba real, se debería usar una DB de prueba o asegurar un backup restaurable.
        # print(f"\nIntentando importar desde el archivo recién creado: {filepath}")
        # import_success = import_database_from_sql(filepath)
        # if import_success:
        #     print("Prueba de importación exitosa.")
        # else:
        #     print("Prueba de importación fallida.")
        #     # Aquí se podría intentar restaurar el backup_path_auto si se implementó.
    else:
        print("Prueba de exportación fallida.")
