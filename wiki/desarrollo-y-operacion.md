# Desarrollo y operación

## Configuración

Compose lee variables del archivo `.env` en la raíz. Variables principales:

| Variable | Función |
|---|---|
| `DEBUG` y `SECRET_KEY` | Configuración de seguridad de Django |
| `EMAIL_MODE` | Selecciona notificación (`CELERY`, `ASYNC`, `REAL` o `MOCK`) |
| `USE_CATALOG_MICROSERVICE` | Activa el gateway HTTP de Flask |
| `CATALOG_SERVICE_URL` | URL interna del catálogo, normalmente `http://flask_catalog:5001` |
| `CELERY_BROKER_URL` y `CELERY_RESULT_BACKEND` | Configuración de Redis para Celery |
| `EXCHANGE_API_MODE` | Adapter de divisas (`REAL` o `MOCK`) |
| `ALLY_SERVICE_URL` | URL base del catálogo del equipo aliado |

Para una instancia pública, configura `DEBUG=False` y una clave secreta única. Mantén `.env` fuera del control de versiones.

## Ejecución local

Desde la raíz:

```bash
docker compose up -d --build
docker compose ps
```

Los cinco servicios esperados son `nginx`, `django_web`, `flask_catalog`, `redis` y `celery_worker`.

## Pruebas y traducciones

```bash
python manage.py test
pytest services/catalog_service/test_catalog.py
```

Para compilar los catálogos gettext después de modificarlos:

```bash
python compile_po.py
```

## Logs y tareas asíncronas

```bash
docker compose logs --tail=100
docker compose logs --tail=100 celery_worker
```

Después de una compra, el log del worker permite comprobar la recepción y ejecución de `store.enviar_correo_confirmacion`.

## Diagnóstico rápido

- `no configuration file provided`: sitúate en la carpeta que contiene `docker-compose.yml`.
- `405` en `/checkout/`: usa el método `POST`; para la interfaz utiliza `/tienda/checkout/`.
- Advertencia de `version` obsoleta: Compose v2 ignora ese campo; no impide el arranque.
- Un servicio no está activo: consulta `docker compose ps` y `docker compose logs <servicio>`.
