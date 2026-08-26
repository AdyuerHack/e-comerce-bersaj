# E-Commerce Bersaj

## Descripción del proyecto

Aplicación desarrollada en **Django** que simula el proceso de checkout de una tienda en línea. El proyecto tiene como objetivo aplicar principios de arquitectura limpia y patrones de diseño de software vistos en clase, separando claramente las responsabilidades entre la capa web, la lógica de negocio y la infraestructura.

## Objetivo

Demostrar la aplicación práctica de patrones de diseño (**Builder**, **Factory Method**) y del principio de **inyección de dependencias**, en un caso de uso real: el registro de un pedido y el envío de su confirmación.

## Arquitectura del proyecto

```
ecommerce/              # Configuración general del proyecto Django
store/
├── models.py            # Modelo Pedido
├── views.py             # Capa HTTP (CheckoutView)
├── services.py          # Lógica de negocio (CheckoutService)
├── domain/
│   └── pedido_builder.py    # Construcción y validación del Pedido
└── infra/
    ├── notification_interface.py  # Contrato de notificación
    ├── email_service.py           # Notificación "real"
    ├── mock_email_service.py      # Notificación simulada
    └── factory.py                 # Selección de la implementación a usar
```

## Patrones de diseño aplicados

| Patrón | Dónde se aplica | Propósito |
|---|---|---|
| **Builder** | `PedidoBuilder` | Construir el objeto `Pedido` paso a paso, centralizando las validaciones (cliente, dirección y total obligatorios). |
| **Strategy / Interface** | `NotificationService` | Definir un contrato común que implementan `EmailService` y `MockEmailService`, permitiendo intercambiarlas sin afectar el resto del código. |
| **Factory Method** | `NotificationFactory` | Decidir en tiempo de ejecución qué implementación de notificación usar, según la variable de entorno `EMAIL_MODE`. |
| **Inyección de dependencias** | `CheckoutService` | Recibir el servicio de notificación por constructor en lugar de crearlo internamente, facilitando las pruebas y el desacoplamiento. |

## ¿Por qué organizamos el proyecto así?

La estructura base es la típica de Django (un proyecto `ecommerce/`
con la configuración, y una app `store/` adentro), pero dentro de
`store/` decidimos no meter todo en `models.py` y `views.py` como
viene por defecto, porque con los patrones que nos pidieron (Builder,
Factory, Service Layer) eso se iba a volver un caos rápido.

## La idea detrás de cada carpeta:

- **`models.py`** lo dejamos solo para las clases que realmente se
  guardan en la base de datos, con sus validaciones básicas (que el
  precio no sea negativo, que no se pueda vender más stock del que
  hay, etc.). Nada más.
- **`domain/`** es para el `PedidoBuilder`. No lo pusimos en
  `models.py` porque no es una tabla, es solo la lógica que arma el
  pedido paso a paso antes de guardarlo — nos pareció más limpio
  separarlo.
- **`infra/`** agrupa todo lo que tiene que ver con servicios
  externos (mandar el WhatsApp o el correo). Lo aislamos detrás de
  una interfaz y una Factory para que, si un día cambiamos de
  proveedor de notificaciones, solo tocamos esta carpeta y no
  rompemos nada más.
- **`services.py`** es básicamente donde armamos todo el flujo de
  "crear un pedido": valida, arma el pedido con el Builder, descuenta
  stock, notifica. Esto lo hicimos aparte de las vistas justo por lo
  que pide la rúbrica: nada de lógica de negocio metida en
  `views.py`.
- **`views.py`** quedó bien simple a propósito, solo recibe el
  request y le pasa la pelota al service.

No creamos apps nuevas de Django (tipo `pedidos/`, `productos/`, etc.)
porque para el tamaño actual del proyecto nos pareció innecesario
complicarlo — con separar por carpetas dentro de la misma app
ya se cumple con la idea de tener las responsabilidades bien
divididas, y si más adelante el proyecto crece, esta base ya nos
deja el camino fácil para pasar a Django Rest Framework sin tener
que mover el dominio ni los servicios.


## Flujo del proceso de compra

1. El cliente envía una solicitud `POST /checkout/` con los datos `cliente`, `direccion` y `total`.
2. `CheckoutView` obtiene el servicio de notificación mediante `NotificationFactory` y delega el procesamiento a `CheckoutService`.
3. `CheckoutService` valida los datos recibidos y, con ayuda de `PedidoBuilder`, construye y valida el pedido (cliente y dirección no vacíos, total mayor que cero).
4. El pedido se guarda en la base de datos.
5. Se envía la notificación de confirmación al cliente.
6. Se retorna una respuesta en formato JSON, indicando éxito o el error correspondiente.

## Endpoint disponible

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/checkout/` | Procesa una compra y registra el pedido |

**Parámetros esperados:** `cliente`, `direccion`, `total`

## Autores

Adyuer De Jesus Ojeda Badel.

Alejandro Cadavid Osorio.

Santiago Lafont Díaz.
