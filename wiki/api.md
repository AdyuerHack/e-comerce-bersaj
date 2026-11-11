# API

Las rutas se publican a través de Nginx en el puerto 80. Flask sirve catálogo e inventario; Django sirve el checkout.

## Catálogo e inventario (Flask)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/products` | Lista productos activos, tallas y stock |
| `GET` | `/api/v1/products/{producto_id}` | Consulta un producto |
| `GET` | `/api/v1/tallas/{talla_id}` | Consulta producto, precio y stock de una talla |
| `POST` | `/api/v1/inventory/check` | Valida disponibilidad |
| `POST` | `/api/v1/inventory/decrease` | Valida y descuenta inventario |
| `GET` | `/api/v1/public/catalog` | Catálogo JSON para consumidores externos |
| `GET` | `/health/catalog` | Estado del servicio Flask detrás del gateway |

Cuerpo de ejemplo para operaciones de inventario:

```json
{
  "items": [{"talla_id": 1, "cantidad": 1}]
}
```

El catálogo público incluye nombre de tienda, versión de API, cantidad de productos y, por producto, identificador, nombre, descripción, precio, categoría y stock total.

## Checkout (Django REST)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/checkout/` | Procesa una compra |
| `POST` | `/api/v1/checkout/` | Ruta versionada para checkout |

Ejemplo de solicitud:

```json
{
  "cliente_id": 1,
  "direccion_id": 1,
  "items": [{"talla_id": 1, "cantidad": 1}]
}
```

La respuesta exitosa utiliza HTTP `201` e incluye mensaje, identificador de pedido y total. Los errores de validación se responden como `400`, recursos inexistentes como `404` y conflictos de inventario como `409`.

## Gateway

`GET /health` devuelve el estado básico de Nginx. Para revisar los servicios internos, combina el healthcheck con `docker compose ps` y los logs de Compose.
