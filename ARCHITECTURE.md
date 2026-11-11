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
    Client["🌐 Cliente Web / Navegador / API Aliado<br><i>(Punto de Entrada Externo)</i>"]

    subgraph AWS["☁️ Servidor AWS EC2 (IP Elástica :80 | Red bersaj_network)"]
        
        subgraph Gateway["1. Capa Ingress & Enrutamiento de Tráfico"]
            Nginx["🚪 Nginx API Gateway (:80)<br>• Reverse Proxy Central<br>• Enrutador Ingress<br>• Timeouts & Headers Trazabilidad"]
        end

        subgraph Core["2. Monolito Residual - Django Core (:8000)"]
            DjangoViews["🖥️ Capa de Presentación (UI & DRF)<br>• Vistas Web Bootstrap 5<br>• Motor i18n gettext (ES/EN)"]
            CheckoutSvc["⚙️ CheckoutService (Service Layer)<br>• Orquestador de Compra<br>• Transacción Atómica ACID"]
            Builder["🏗️ PedidoBuilder (Builder Pattern)<br>• Validación de Reglas de Negocio"]
            CatalogClient["🔌 CatalogGateway (Strangler Pattern)<br>• LocalCatalogAdapter / HttpAdapter"]
            AdapterDIP["💱 CurrencyExchangePort (DIP)<br>• OpenExchangeRateAdapter con Fallback"]
            AllyClient["🤝 AllyServiceClient<br>• Integración con Equipo Aliado"]
            DjangoDB[("💾 SQLite: db.sqlite3<br>Clientes, Direcciones, Pedidos")]
            
            DjangoViews --> CheckoutSvc
            CheckoutSvc --> Builder
            CheckoutSvc --> CatalogClient
            CheckoutSvc --> DjangoDB
            DjangoViews --> AdapterDIP
            DjangoViews --> AllyClient
        end

        subgraph Microservice["3. Microservicio Independiente - Flask (:5001)"]
            FlaskAPI["⚡ Flask REST API Engine<br>• Catálogo & Inventario"]
            CatalogEngine["📦 Lógica de Stock Atómico<br>• Verificación & Deducción"]
            PublicAPI["📢 Endpoint a Proveer (Req 2.3)<br>• GET /api/v1/public/catalog"]
            CatalogDB[("💾 SQLite: catalog.db<br>Productos y Tallas Desacopladas")]

            FlaskAPI --> CatalogEngine
            FlaskAPI --> PublicAPI
            CatalogEngine --> CatalogDB
        end

        subgraph Asynchronous["4. Capa de Resiliencia & Tareas Asíncronas"]
            Redis[("⚡ Redis Message Broker (:6379)<br>Cola de Mensajes en Memoria")]
            CeleryWorker["⚙️ Celery Worker<br>• enviar_confirmacion_asincrona.delay()<br>• Graceful Degradation"]
            Redis --> CeleryWorker
        end
    end

    subgraph External["5. Ecosistema Externo"]
        ThirdPartyAPI["🌍 API de Divisas Terceros<br>(https://open.er-api.com/v6/latest/USD)"]
        AllyAPI["🤝 API Remota del Equipo Aliado<br>(/api/v1/public/catalog)"]
    end

    %% Flujos de Red Principales
    Client -->|"HTTP Request (:80)"| Nginx
    Nginx -->|"/, /tienda/*, /checkout/"| DjangoViews
    Nginx -->|"/api/v1/products, /api/v1/public/*, /api/v1/inventory/*"| FlaskAPI

    %% Comunicación entre Microservicios (Strangler Fig)
    CatalogClient -.->|"HTTP REST Interno (:5001)<br>Descuento Atómico de Stock"| FlaskAPI

    %% Desacoplamiento Asíncrono
    CheckoutSvc -->|"Encola Evento sin Bloqueo HTTP"| Redis

    %% Integraciones Externas
    AdapterDIP -->|"HTTP GET (USD a COP)<br>Fallback contingente $4.200 COP"| ThirdPartyAPI
    AllyClient -->|"HTTP GET Catálogo Aliado<br>Fallback Resiliente Activo"| AllyAPI

    %% Estilos de Nodos
    classDef nginxStyle fill:#059669,stroke:#047857,stroke-width:2px,color:#ffffff;
    classDef djangoStyle fill:#0284c7,stroke:#0369a1,stroke-width:2px,color:#ffffff;
    classDef flaskStyle fill:#d97706,stroke:#b45309,stroke-width:2px,color:#ffffff;
    classDef asyncStyle fill:#dc2626,stroke:#b91c1c,stroke-width:2px,color:#ffffff;
    classDef extStyle fill:#4b5563,stroke:#374151,stroke-width:2px,color:#ffffff;
    classDef clientStyle fill:#4338ca,stroke:#3730a3,stroke-width:2px,color:#ffffff;

    class Nginx nginxStyle;
    class DjangoViews,CheckoutSvc,Builder,CatalogClient,AdapterDIP,AllyClient,DjangoDB djangoStyle;
    class FlaskAPI,CatalogEngine,PublicAPI,CatalogDB flaskStyle;
    class Redis,CeleryWorker asyncStyle;
    class ThirdPartyAPI,AllyAPI extStyle;
    class Client clientStyle;
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
