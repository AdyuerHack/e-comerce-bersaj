# Wiki técnica — E-Commerce Bersaj

Sistema de comercio electrónico . Esta wiki resume la arquitectura, los flujos principales y la operación del sistema.

## Contenido

- [Arquitectura](wiki/arquitectura.md)
- [Guía de uso](wiki/guia-de-uso.md)
- [API](wiki/api.md)
- [Desarrollo y operación](wiki/desarrollo-y-operacion.md)
- [Despliegue en AWS Academy](wiki/despliegue-aws.md)
- [Documento de arquitectura](ARCHITECTURE.md)

## Resumen

La solución combina un núcleo web en **Django**, un microservicio de **catálogo e inventario en Flask**, **Nginx** como API Gateway y **Redis/Celery** para procesamiento asíncrono. El sistema incorpora conversión de divisas mediante Adapter, integración HTTP con un servicio aliado e internacionalización español/inglés con gettext.

## Servicios

| Servicio | Función |
|---|---|
| Nginx | Entrada HTTP y enrutamiento hacia los servicios internos |
| Django | Interfaz, checkout, clientes, direcciones y pedidos |
| Flask Catalog | Productos, tallas, inventario y catálogo público |
| Redis | Broker y backend de resultados para Celery |
| Celery Worker | Procesamiento de tareas en segundo plano |

La ejecución local se inicia con `docker compose up -d --build`. Las rutas de acceso y verificación están en [Despliegue en AWS Academy](wiki/despliegue-aws.md).
