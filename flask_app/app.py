from flask import Flask, jsonify, request
import uuid

app = Flask(__name__)

@app.route('/checkout/', methods=['POST'])
def procesar_compra():
    try:
        data = request.get_json()
        if not data or 'cliente' not in data or 'items' not in data:
            return jsonify({"error": "Faltan datos requeridos (cliente, items)."}), 400
        
        # Simulamos el procesamiento pesado de checkout (Microservicio Flask)
        pedido_id = str(uuid.uuid4())
        total = sum(item.get('cantidad', 1) * 10.0 for item in data['items']) # Simulacion
        
        respuesta = {
            "mensaje": "Compra realizada correctamente (Microservicio Flask)",
            "pedido_id": pedido_id,
            "total": str(total)
        }
        return jsonify(respuesta), 201
    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
