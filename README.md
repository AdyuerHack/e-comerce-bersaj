# E-Commerce Bersaj 2.0: Migración a Microservicios, Integración y Resiliencia

Proyecto desarrollado para la asignatura **Arquitectura de Software 2026-I**  
**Profesor:** Nicolás Ramírez Vélez  

---

##  Autores
* **Adyuer De Jesus Ojeda Badel**
* **Alejandro Cadavid Osorio**
* **Santiago Lafont Díaz**

---

##  Visión General del Proyecto (Entrega No. 2)

El proyecto evoluciona de la arquitectura monolítica inicial hacia un **ecosistema distribuido, híbrido y resiliente**, aplicando los siguientes principios y patrones arquitectónicos:

1. **Strangler Fig Pattern (Patrón Estrangulador):** Extracción del catálogo de productos e inventario hacia un microservicio independiente en **Flask**, desacoplado de la persistencia central.
2. **API Gateway (Nginx):** Enrutador central que unifica el tráfico externo hacia Django Core y el Microservicio de Flask, gestionando proxies inversos y timeouts.
3. **Comunicación Asíncrona & Message Broker (Redis + Celery):** Procesamiento en segundo plano de notificaciones y confirmación de pedidos, evitando el bloqueo del hilo HTTP principal.
4. **Patrón Adapter (Inversión de Dependencias - DIP):** Integración con API externa de terceros (conversión de divisas USD/COP en tiempo real) a través de una interfaz abstracta (`CurrencyExchangePort`).
5. **Integración con Equipo Aliado:** Exposición de un endpoint JSON público (`GET /api/v1/public/catalog`) y consumo del catálogo provisto por el equipo aliado en la interfaz web.
6. **Internacionalización Completa (i18n gettext):** Soporte bilingüe (Español / Inglés) sin textos quemados en vistas, serializadores o plantillas.
7. **Orquestación con Docker Compose:** Empaquetado de 5 servicios (Nginx, Django, Flask, Redis, Celery) listo para desplegar en **AWS Academy EC2** con IP Elástica.

---

##  Arquitectura del Sistema

```
                       ┌────────────────────────────────────────┐
                       │        NGINX (API Gateway :80)         │
                       │   Ruteo / Ingress / Proxy Inverso      │
                       └────┬─────────────────────────────┬─────┘
                            │ /api/v1/checkout, /, /tienda│ /api/v1/products, /api/v1/public
                            ▼                             ▼
                 ┌────────────────────┐        ┌────────────────────┐
                 │   Django Core      │        │  Microservicio     │
                 │  - Checkout Orq.   │        │     Flask          │
                 │  - Adapter Terceros│        │  - Catálogo        │
                 │  - Integrac. Aliado│        │  - Inventario      │
                 │  - i18n (gettext)  │        │  - Servicio Proveer│
                 └─────────┬──────────┘        └────────────────────┘
                           │ Dispara evento
                           ▼
                 ┌────────────────────┐
                 │   Redis (Broker)   │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │   Celery Worker    │ (Procesos en background)
                 └────────────────────┘
```

Para consultar el diagrama C4 detallado y el flujo de secuencia, revise [**`ARCHITECTURE.md`**](ARCHITECTURE.md).

Para documentación navegable del proyecto, consulte la [**Wiki de E-Commerce Bersaj**](Wiki.md).

---

##  Estructura del Repositorio

```text
e-comerce-bersaj/
├── docker-compose.yml              # Orquestación de todo el ecosistema
├── Dockerfile                      # Imagen Docker de Django Core
├── requirements.txt                # Dependencias Django, Celery, Redis, DRF
├── compile_po.py                   # Compilador binario de traducciones i18n (.po a .mo)
├── ARCHITECTURE.md                 # Documento formal de arquitectura y diagramas
├── DEPLOYMENT_AWS.md               # Guía paso a paso de despliegue en AWS EC2
├── ecommerce/                      # Configuración central Django & Celery
│   ├── celery.py                   # Configuración del worker Celery
│   ├── settings.py                 # Configuración de apps, middleware, i18n y Redis
│   └── urls.py                     # Enrutador principal y selector de idiomas
├── store/                          # Aplicación monolítica residual
│   ├── models.py                   # Entidades Cliente, DireccionEnvio, Pedido
│   ├── services.py                 # CheckoutService con inyección de dependencias
│   ├── domain/
│   │   └── pedido_builder.py       # Patrón Builder para pedidos
│   ├── infra/
│   │   ├── catalog_client.py       # Strangler Gateway hacia Flask
│   │   ├── ally_service_client.py  # Cliente para consumir API del equipo aliado
│   │   ├── async_email_service.py  # Notificaciones asíncronas vía Celery
│   │   └── adapters/               # Patrón Adapter con Inversión de Dependencias (DIP)
│   │       ├── exchange_rate_port.py   # Contrato / Puerto abstracto
│   │       ├── open_exchange_adapter.py# Adaptador API pública de divisas
│   │       └── mock_exchange_adapter.py# Adaptador para pruebas unitarias
│   ├── views.py                    # API REST (DRF APIView)
│   ├── views_ui.py                 # Vistas interactivas web (Catálogo, Checkout, Aliado)
│   └── tests.py                    # 14 pruebas unitarias e integración
├── services/
│   └── catalog_service/            # Microservicio Flask (Catálogo e Inventario)
│       ├── app.py                  # Endpoints REST y Servicio a Proveer
│       ├── database.py             # Persistencia independiente SQLite
│       ├── test_catalog.py         # 9 pruebas unitarias con pytest
│       └── Dockerfile              # Contenedor del microservicio
├── nginx/
│   ├── nginx.conf                  # Configuración de rutas y upstream como API Gateway
│   └── Dockerfile                  # Contenedor de Nginx
├── locale/                         # Archivos gettext de traducción
│   ├── es/LC_MESSAGES/django.po    # Traducciones en Español
│   └── en/LC_MESSAGES/django.po    # Traducciones en Inglés
└── templates/                      # Plantillas Web Bootstrap 5 (Usabilidad & UX)
    ├── base.html                   # Layout base y selector de idioma
    ├── catalog.html                # Catálogo con precios en COP y USD
    ├── checkout.html               # Formulario robusto de checkout
    ├── ally.html                   # Integración con el equipo aliado
    └── order_success.html          # Confirmación de pedido asíncrono
```

---

##  Ejecución Local con Docker Compose

La forma recomendada de ejecutar todo el ecosistema con un solo comando:

```bash
docker compose up --build
```

Una vez levantado:
* **Tienda Web:** [http://localhost/](http://localhost/)
* **Catálogo del Microservicio (Flask):** [http://localhost/api/v1/products](http://localhost/api/v1/products)
* **Servicio a Proveer (Equipo Aliado):** [http://localhost/api/v1/public/catalog](http://localhost/api/v1/public/catalog)
* **Consumo del Aliado en UI:** [http://localhost/tienda/aliado/](http://localhost/tienda/aliado/)
* **Healthcheck Gateway:** [http://localhost/health](http://localhost/health)

---

##  Ejecución de Pruebas Automatizadas

El proyecto cuenta con **23 pruebas unitarias e integrales** que validan el 100% de los componentes:

```bash
# 1. Pruebas de Django (Monolito, Strangler, Adapter, Celery, UI) - 14 pruebas:
python manage.py test

# 2. Pruebas del Microservicio Flask (Inventario, Precios, Stock atómico) - 9 pruebas:
pytest services/catalog_service/test_catalog.py
```

---


