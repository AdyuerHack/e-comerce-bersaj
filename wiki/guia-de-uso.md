# Guía de uso

## Rutas web

| Ruta | Función |
|---|---|
| `/` | Catálogo de productos, tallas y precios en COP/USD |
| `/tienda/checkout/` | Formulario de compra |
| `/tienda/aliado/` | Catálogo consumido del servicio aliado |
| `/admin/` | Administración de Django |

El selector de idioma permite alternar entre español e inglés. Las traducciones se gestionan con gettext.

## Compra

1. Desde el catálogo, selecciona una prenda y talla.
2. En el checkout, selecciona cliente, dirección y cantidad.
3. Envía el formulario para registrar el pedido.
4. La confirmación muestra el identificador y total del pedido; la notificación se solicita de forma asíncrona.

El envío base es de 8.000 COP para pedidos con productos. Los clientes, direcciones y productos iniciales se cargan con `seed_data`; Flask inicializa sus datos de catálogo en su base SQLite.

## Respuestas del sistema

- `/tienda/checkout/` es el formulario para usuarios.
- `/checkout/` y `/api/v1/checkout/` son endpoints REST que reciben `POST`; una solicitud `GET` puede responder `405 Method Not Allowed`.
