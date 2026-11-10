import os
from decimal import Decimal
from flask import Flask, jsonify, request
from database import get_connection, init_db

app = Flask(__name__)

# Ensure DB is initialized
init_db()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "catalog_inventory_service",
        "version": "1.0.0"
    }), 200


@app.route("/api/v1/products", methods=["GET"])
def list_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos WHERE activo = 1;")
    productos = [dict(row) for row in cursor.fetchall()]

    for prod in productos:
        prod["precio"] = float(prod["precio"])
        cursor.execute("SELECT id, talla, stock FROM tallas WHERE producto_id = ?;", (prod["id"],))
        prod["tallas"] = [dict(t) for t in cursor.fetchall()]

    conn.close()
    return jsonify(productos), 200


@app.route("/api/v1/products/<int:producto_id>", methods=["GET"])
def get_product(producto_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos WHERE id = ?;", (producto_id,))
    prod = cursor.fetchone()

    if not prod:
        conn.close()
        return jsonify({"error": f"Producto con ID {producto_id} no encontrado."}), 404

    prod_dict = dict(prod)
    prod_dict["precio"] = float(prod_dict["precio"])

    cursor.execute("SELECT id, talla, stock FROM tallas WHERE producto_id = ?;", (producto_id,))
    prod_dict["tallas"] = [dict(t) for t in cursor.fetchall()]

    conn.close()
    return jsonify(prod_dict), 200


@app.route("/api/v1/tallas/<int:talla_id>", methods=["GET"])
def get_talla(talla_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT t.id, t.talla, t.stock, p.id as producto_id, p.nombre as producto_nombre, p.precio
    FROM tallas t
    JOIN productos p ON t.producto_id = p.id
    WHERE t.id = ?;
    """
    cursor.execute(query, (talla_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": f"Talla con ID {talla_id} no encontrada."}), 404

    res = dict(row)
    res["precio"] = float(res["precio"])
    return jsonify(res), 200


@app.route("/api/v1/inventory/check", methods=["POST"])
def check_stock():
    data = request.get_json() or {}
    items = data.get("items", [])

    if not items:
        return jsonify({"error": "Debe enviar al menos un item para verificar."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    issues = []
    for item in items:
        talla_id = item.get("talla_id")
        cantidad = item.get("cantidad", 1)

        cursor.execute("SELECT id, talla, stock FROM tallas WHERE id = ?;", (talla_id,))
        talla = cursor.fetchone()

        if not talla:
            issues.append({"talla_id": talla_id, "error": "No existe"})
        elif talla["stock"] < cantidad:
            issues.append({
                "talla_id": talla_id,
                "talla": talla["talla"],
                "solicitado": cantidad,
                "disponible": talla["stock"],
                "error": "Stock insuficiente"
            })

    conn.close()

    if issues:
        return jsonify({"available": False, "issues": issues}), 409

    return jsonify({"available": True, "message": "Stock verificado correctamente."}), 200


@app.route("/api/v1/inventory/decrease", methods=["POST"])
def decrease_stock():
    data = request.get_json() or {}
    items = data.get("items", [])

    if not items:
        return jsonify({"error": "Debe enviar al menos un item para descontar."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Atomic verification first
        for item in items:
            talla_id = item.get("talla_id")
            cantidad = item.get("cantidad", 1)

            cursor.execute("SELECT id, talla, stock FROM tallas WHERE id = ?;", (talla_id,))
            talla = cursor.fetchone()

            if not talla:
                conn.rollback()
                conn.close()
                return jsonify({"error": f"La talla {talla_id} no existe."}), 404

            if talla["stock"] < cantidad:
                conn.rollback()
                conn.close()
                return jsonify({
                    "error": f"Stock insuficiente para talla {talla['talla']}. Disponible: {talla['stock']}, Solicitado: {cantidad}."
                }), 409

        # Deduct stock
        for item in items:
            talla_id = item.get("talla_id")
            cantidad = item.get("cantidad", 1)
            cursor.execute("UPDATE tallas SET stock = stock - ? WHERE id = ?;", (cantidad, talla_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": f"Error al actualizar inventario: {str(e)}"}), 500

    conn.close()
    return jsonify({"success": True, "message": "Inventario descontado correctamente."}), 200


# =====================================================================
# SERVICIO A PROVEER (Requerimiento 2.3 de la Rúbrica)
# Endpoint público para que el equipo aliado consuma datos de la tienda
# =====================================================================
@app.route("/api/v1/public/catalog", methods=["GET"])
def public_catalog():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT p.id, p.nombre, p.descripcion, p.precio, p.categoria, 
           SUM(t.stock) as stock_total
    FROM productos p
    LEFT JOIN tallas t ON p.id = t.producto_id
    WHERE p.activo = 1
    GROUP BY p.id;
    """)
    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "nombre": r["nombre"],
            "descripcion": r["descripcion"],
            "precio": float(r["precio"]),
            "categoria": r["categoria"],
            "stock_total": r["stock_total"] or 0
        })

    return jsonify({
        "tienda": "E-Commerce Bersaj",
        "version_api": "v1",
        "descripcion": "Catálogo público de productos disponibles para aliados comerciales",
        "total_productos": len(items),
        "productos": items
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)

