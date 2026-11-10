# Documento de Arquitectura de Software 2026-I
## Entrega No. 2: Migración a Microservicios, Integración y Resiliencia
**Proyecto:** E-Commerce Bersaj  
**Profesor:** Nicolás Ramírez Vélez  
**Equipo:** Adyuer De Jesus Ojeda Badel, Alejandro Cadavid Osorio, Santiago Lafont Díaz  

---

## 1. Visión General del Sistema y Strangler Pattern

En esta segunda entrega, el monolito desarrollado en Django evoluciona hacia una **arquitectura híbrida orientada a microservicios** mediante la aplicación del **Strangler Fig Pattern (Patrón Estrangulador)**.

La lógica del **Catálogo de Productos e Inventario** ha sido estrangulada y extraída hacia un microservicio independiente en **Flask**, con su propio almacén de datos relacional (`catalog.db`). El monolito en Django ahora orquesta las compras mediante un Gateway HTTP interno (`CatalogGateway`) con inversión de dependencias.

```mermaid
flowchart TD
    Client["Navegador Web / Cliente API / Equipo Aliado"]

    subgraph AWS["Instancia EC2 AWS Academy (IP Elástica)"]
        subgraph Gateway["Capa de Enrutamiento & Ingress"]
            Nginx["Nginx API Gateway (:80)<br>Reverse Proxy & Traffic Router"]
        end

        subgraph Core["Monolito Residual - Django Core (:8000)"]
            DjangoViews["Vistas Web & DRF APIView"]
            CheckoutSvc["CheckoutService & PedidoBuilder"]
            CatalogClient["CatalogGateway (Strangler Pattern)"]
            AdapterDIP["CurrencyExchangePort (DIP)"]
            AllyClient["AllyServiceClient"]
            i18n["gettext i18n Engine (ES / EN)"]
            DjangoDB[("SQLite db.sqlite3<br>Clientes, Direcciones, Pedidos")]
        end

        subgraph Microservice["Microservicio Independiente - Flask (:5001)"]
            FlaskAPI["Flask REST API"]
            CatalogEngine["Lógica de Stock & Precios"]
            PublicAPI["Servicio a Proveer (/api/v1/public/catalog)"]
            CatalogDB[("SQLite catalog.db<br>Productos y Tallas")]
        end

        subgraph Asynchronous["Capa de Resiliencia y Asincronía"]
            Redis[("Redis Message Broker (:6379)")]
            CeleryWorker["Celery Worker<br>Tareas en Background"]
        end
    end

    subgraph External["Ecosistema Externo"]
        ThirdPartyAPI["API Externa Divisas<br>(open.er-api.com)"]
        AllyAPI["API del Equipo Aliado"]
    end

    %% Flujos de Red
    Client -->|HTTP :80| Nginx
    Nginx -->|"/api/v1/products, /api/v1/public"| FlaskAPI
    Nginx -->|"/, /tienda, /api/v1/checkout"| DjangoViews

    CatalogClient -.->|"HTTP REST Interno (:5001)"| FlaskAPI
    CheckoutSvc --> CatalogClient
    CheckoutSvc --> DjangoDB
    CheckoutSvc -->|Dispara Evento| Redis
    Redis --> CeleryWorker

    AdapterDIP -->|HTTP JSON| ThirdPartyAPI
    AllyClient -->|HTTP JSON| AllyAPI

    FlaskAPI --> CatalogEngine
    CatalogEngine --> CatalogDB
```

---

## 2. Descripción de Componentes Arquitectónicos

### 2.1. API Gateway (Nginx)
Configurado como punto de entrada único (*Reverse Proxy*):
* Enruta el tráfico hacia el microservicio en Flask (`/api/v1/products`, `/api/v1/public/catalog`, `/api/v1/inventory`).
* Enruta el tráfico hacia Django Core para la interfaz de usuario, checkout y administración (`/`, `/tienda/`, `/checkout/`).
* Aplica control de timeouts y trazabilidad mediante headers `X-Forwarded-*`.

### 2.2. Microservicio de Catálogo e Inventario (Flask)
* Aislamiento total de dominio: gestiona productos, tallas, verificación de existencias y descuento atómico.
* **Servicio a Proveer (Requerimiento 2.3):** Expone `GET /api/v1/public/catalog` con los productos, precios y disponibilidad en formato JSON estructurado para el consumo de equipos aliados.

### 2.3. Resiliencia y Comunicación Asíncrona (Celery + Redis)
* Para evitar que las llamadas a servicios externos o el envío de correos bloqueen el ciclo de vida de la petición HTTP, `CheckoutService` delega la confirmación a `store.tasks.enviar_confirmacion_asincrona` encolada en **Redis**.
* El contenedor `celery_worker` procesa los eventos en segundo plano de manera tolerante a fallos.

### 2.4. Patrón Adapter e Inversión de Dependencias (DIP)
* Para cumplir el Requerimiento 2.3, el sistema define la abstracción `CurrencyExchangePort`.
* `OpenExchangeRateAdapter` consume la API pública en tiempo real de tipo de cambio USD/COP.
* `MockExchangeRateAdapter` permite ejecutar pruebas deterministas sin dependencia de red.
* La capa de presentación consume el puerto sin conocer los detalles de implementación de la API externa.

### 2.5. Consumo del Servicio del Equipo Aliado
* `AllyServiceClient` consume el endpoint público del equipo aliado y renderiza su catálogo en la vista `/tienda/aliado/`. Incluye fallback resiliente si el servidor aliado no se encuentra disponible.

### 2.6. Internacionalización Completa (i18n con gettext)
* Soporte bilingüe (Español / Inglés).
* Cero textos quemados: todos los mensajes de validación, respuestas y etiquetas de UI utilizan `gettext` (`_()`).
* Compilación binaria de catálogos `.mo` mediante script multiplataforma `compile_po.py`.

---

## 3. Diagrama de Secuencia: Checkout Asíncrono con Strangler Pattern

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as Cliente Web
    participant Gateway as Nginx API Gateway
    participant Django as Django Core (CheckoutService)
    participant Flask as Flask Microservice (Catalog)
    participant Redis as Redis Message Broker
    participant Celery as Celery Worker
    participant Adapter as Exchange Adapter (DIP)

    Usuario->>Gateway: POST /tienda/checkout/ (cliente, dirección, prendas)
    Gateway->>Django: Enruta petición de compra
    Django->>Flask: POST /api/v1/inventory/decrease (validación y descuento atómico)
    Flask-->>Django: 200 OK (Inventario actualizado)
    Django->>Django: Guarda Pedido en Base de Datos (Estado: Confirmado)
    Django->>Redis: Encola tarea enviar_confirmacion_asincrona.delay()
    Django-->>Gateway: Renderiza confirmación con ID de Pedido
    Gateway-->>Usuario: Respuesta 200/201 inmediata al usuario
    Note over Redis,Celery: Procesamiento en Segundo Plano
    Redis->>Celery: Entrega payload de la tarea
    Celery->>Celery: Ejecuta envío de confirmación y logging
```

---

## 4. Rúbrica ABET y Verificación de Requerimientos

| Criterio | Peso | Implementación en Bersaj | Estado |
|---|:---:|---|:---:|
| **Correcciones E1** | 10% | Modelos, Builder, Service Layer desacoplado y validaciones SRP refinadas. | Cumplido |
| **Arquitectura** | 10% | Diagramas completos C4/Mermaid (AWS, Nginx, Flask, Redis, Celery, DB) en este documento. | Cumplido |
| **Servicios** | 30% | Endpoint a proveer (`/api/v1/public/catalog`), consumo de aliado (`/tienda/aliado/`) y Adapter con DIP (`CurrencyExchangePort`). | Cumplido |
| **Infraestructura** | 30% | Docker Compose orquestando 5 servicios + Nginx API Gateway + Guía de despliegue en AWS EC2 con IP Elástica. | Cumplido |
| **Resiliencia y UX** | 20% | Broker Redis/Celery para eventos en fondo, soporte i18n gettext (ES/EN) y UI interactiva Bootstrap 5. | Cumplido |
