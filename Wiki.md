# Wiki Técnica: E-Commerce Bersaj

## 1. Justificación de la Estructura de Carpetas

La arquitectura del proyecto sigue el principio de **Separación de Responsabilidades (Separation of Concerns)**, utilizando un enfoque orientado al dominio.

- `store/domain/`: Contiene el **Núcleo de Negocio**. Aquí reside la lógica pura, independiente de frameworks (Django, HTTP, BD). En esta carpeta encontramos:
  - `pedido_builder.py`: Implementa el patrón *Builder* para orquestar la compleja creación de pedidos, validando reglas de negocio estables (stock, cálculos).
  - `excepciones.py`: Define errores semánticos (`RecursoNoEncontradoError`, `ConflictoInventarioError`) para que la capa de aplicación pueda comunicar fallos sin acoplarse a respuestas HTTP.
- `store/infra/`: Contiene adaptadores para dependencias externas (bases de datos secundarias, APIs externas, notificaciones). En este caso, agrupa la lógica de envío de correos, abstrayéndolo a través del patrón *Factory* y una interfaz (`notification_interface.py`).
- `store/services.py`: **Capa de Aplicación (Service Layer)**. Actúa como orquestador. Coordina el acceso a datos (Modelos Django), el dominio (Builder), y la infraestructura (Notificaciones), gestionando además las transacciones atómicas de base de datos.
- `store/views.py`: **Capa de Presentación**. Restringida exclusivamente a desempaquetar peticiones HTTP (JSON), delegar el trabajo al servicio, y empaquetar la respuesta HTTP en base a las excepciones arrojadas.

## 2. Diagrama de Secuencia: Flujo de Checkout

A continuación se describe el flujo del caso de uso más complejo (`procesar_compra`):

```mermaid
sequenceDiagram
    participant Client
    participant CheckoutView (DRF)
    participant CheckoutService
    participant PedidoBuilder
    participant BD (Models)
    participant NotificationFactory
    participant EmailService

    Client->>CheckoutView (DRF): POST /checkout/ (cliente, items)
    CheckoutView (DRF)->>CheckoutService: procesar_compra(cliente, dir, items)
    
    loop Para cada item
        CheckoutService->>BD (Models): Buscar Producto
        alt Producto No Existe
            BD (Models)-->>CheckoutService: DoesNotExist
            CheckoutService-->>CheckoutView (DRF): raise RecursoNoEncontradoError
            CheckoutView (DRF)-->>Client: 404 Not Found
        else Producto Existe
            BD (Models)-->>CheckoutService: Producto
            CheckoutService->>PedidoBuilder: add_item(producto, cantidad)
            alt Sin Stock
                PedidoBuilder-->>CheckoutService: raise ConflictoInventarioError
                CheckoutService-->>CheckoutView (DRF): raise ConflictoInventarioError
                CheckoutView (DRF)-->>Client: 409 Conflict
            end
        end
    end
    
    CheckoutService->>PedidoBuilder: build()
    PedidoBuilder-->>CheckoutService: pedido, items
    
    Note over CheckoutService,BD (Models): INICIA TRANSACCIÓN ATÓMICA
    CheckoutService->>BD (Models): pedido.save()
    CheckoutService->>BD (Models): item.save() (Múltiples)
    CheckoutService->>BD (Models): producto.save() (Descontar stock)
    Note over CheckoutService,BD (Models): COMMIT TRANSACCIÓN
    
    CheckoutService->>NotificationFactory: create()
    NotificationFactory-->>CheckoutService: NotificationService (Instancia)
    CheckoutService->>EmailService: enviar_confirmacion(cliente)
    
    CheckoutService-->>CheckoutView (DRF): pedido
    CheckoutView (DRF)-->>Client: 201 Created (pedido_id)
```

## 3. Preparación para API Gateway (Escalabilidad)

El diseño actual del sistema prepara el terreno de manera natural para integrarse con un **API Gateway** por las siguientes razones:

1. **Agnosticismo HTTP en Servicios:** Los flujos de negocio en `services.py` no reciben un objeto `Request` ni retornan un `Response`. El servicio espera diccionarios nativos de Python. Si mañana el tráfico de checkout llega por gRPC, GraphQL o mensajes asíncronos (RabbitMQ) desde el API Gateway, la lógica de negocio se reutiliza 100% sin modificaciones.
2. **Excepciones Traducibles:** Las excepciones de dominio (como `RecursoNoEncontradoError`) son independientes del framework. Permiten al API Gateway o microservicio de presentación centralizar el manejo de errores y traducirlos a los códigos estándar (4xx, 5xx) uniformemente en toda la arquitectura.
3. **Manejo Centralizado de Infraestructura:** Al abstraer dependencias como el correo mediante Factories, el sistema puede cambiar de un `Mock` local a un publicador de eventos (Kafka) para que un microservicio externo envíe las notificaciones, algo esencial cuando se escala detrás de un Gateway.
