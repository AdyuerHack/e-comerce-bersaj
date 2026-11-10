# Microservicio de Catálogo e Inventario (Flask)

Microservicio extraído del monolito Django aplicando el **Strangler Fig Pattern**. Encargado exclusivamente de la gestión del catálogo de productos, tallas, verificación y descuento atómico de inventario, y exposición del catálogo público para el equipo aliado.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Healthcheck del servicio |
| `GET` | `/api/v1/products` | Lista todos los productos activos con sus tallas y stock |
| `GET` | `/api/v1/products/<id>` | Detalle de un producto específico |
| `GET` | `/api/v1/tallas/<id>` | Detalle de una talla (precio, producto, stock) |
| `POST` | `/api/v1/inventory/check` | Verifica disponibilidad de stock para una lista de ítems |
| `POST` | `/api/v1/inventory/decrease` | Descuenta stock atómicamente si hay disponibilidad |
| `GET` | `/api/v1/public/catalog` | **Servicio a Proveer:** Catálogo público en formato JSON para el equipo aliado |

## Ejecución local
```bash
pip install -r requirements.txt
python app.py
```
El servicio iniciará en `http://localhost:5001`.

## Ejecución de pruebas
```bash
pytest test_catalog.py
```

