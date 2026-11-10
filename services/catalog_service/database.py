import os
import sqlite3
from decimal import Decimal

DB_PATH = os.getenv("CATALOG_DB_PATH", os.path.join(os.path.dirname(__file__), "catalog.db"))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        precio DECIMAL(10, 2) NOT NULL,
        activo INTEGER DEFAULT 1,
        categoria TEXT DEFAULT 'Moda'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tallas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        talla TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (producto_id) REFERENCES productos (id) ON DELETE CASCADE,
        UNIQUE (producto_id, talla)
    );
    """)

    # Seed initial data if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM productos;")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
        INSERT INTO productos (id, nombre, descripcion, precio, activo, categoria)
        VALUES 
            (1, 'Camiseta Básica Oversize', 'Algodón 100% peinado de alta calidad', 45000.00, 1, 'Camisetas'),
            (2, 'Pantalón Cargo Denim', 'Jeans estilo cargo corte relajado con múltiples bolsillos', 110000.00, 1, 'Pantalones'),
            (3, 'Chaqueta Bomber Bersaj', 'Chaqueta impermeable con forro térmico', 160000.00, 1, 'Chaquetas');
        """)

        cursor.execute("""
        INSERT INTO tallas (id, producto_id, talla, stock)
        VALUES 
            (1, 1, 'S', 10),
            (2, 1, 'M', 15),
            (3, 1, 'L', 8),
            (4, 2, '30', 5),
            (5, 2, '32', 12),
            (6, 2, '34', 6),
            (7, 3, 'M', 4),
            (8, 3, 'L', 7);
        """)

    conn.commit()
    conn.close()

