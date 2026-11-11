# Despliegue en AWS Academy

## Infraestructura

El sistema se despliega en una instancia EC2 Ubuntu y se orquesta con Docker Compose. Asocia una Elastic IP y utiliza el puerto 80 como entrada pública de Nginx. Restringe SSH (`22`) a la IP del equipo administrador; Flask (`5001`) y Redis (`6379`) permanecen en la red privada de Compose.

## Preparación del servidor

Instala Docker Compose y Git:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
```

Clona la rama de entrega:

```bash
git clone --branch main https://github.com/AdyuerHack/e-comerce-bersaj.git
cd e-comerce-bersaj
```

Crea `.env` en la raíz con `DEBUG=False`, una `SECRET_KEY` única y las variables requeridas por Compose. Configura `ALLY_SERVICE_URL` con la URL base acordada con el equipo aliado.

## Arranque y verificación

```bash
sudo docker compose up -d --build
sudo docker compose ps
```

Comprueba que los cinco servicios estén activos y visita, sustituyendo `<IP>` por la Elastic IP:

- `http://<IP>/` — catálogo web
- `http://<IP>/tienda/checkout/` — formulario de compra
- `http://<IP>/tienda/aliado/` — catálogo aliado
- `http://<IP>/api/v1/products` — API de productos
- `http://<IP>/api/v1/public/catalog` — catálogo JSON público
- `http://<IP>/health` — estado básico de Nginx

Para validar el procesamiento asíncrono, registra una compra y consulta:

```bash
sudo docker compose logs --tail=100 celery_worker
```

## Actualización

```bash
cd ~/e-comerce-bersaj
git fetch origin
git switch main
git pull --ff-only origin main
sudo docker compose up -d --build
```

La instancia debe permanecer encendida durante la sustentación. Las bases SQLite son independientes por servicio; planifica su persistencia antes de recrear contenedores con datos que deban conservarse.
