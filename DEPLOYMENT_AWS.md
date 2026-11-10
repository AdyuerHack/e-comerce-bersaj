# Guía de Despliegue en AWS Academy EC2
## E-Commerce Bersaj - Entrega No. 2

Esta guía detalla paso a paso cómo desplegar la arquitectura completa en una instancia **EC2 de AWS Academy** utilizando **Docker Compose** y una **IP Elástica**, tal como lo exige el entregable.

---

### Paso 1: Iniciar el Laboratorio en AWS Academy
1. Inicie sesión en **AWS Academy Learner Lab**.
2. Haga clic en **Start Lab** y espere a que el indicador se torne en color verde.
3. Haga clic en **AWS Details** y luego en la consola de administración de **AWS**.

---

### Paso 2: Crear la Instancia EC2
1. Vaya al servicio **EC2** y haga clic en **Launch Instance**.
2. **Nombre:** `bersaj-ecommerce-server`
3. **AMI:** `Ubuntu Server 24.04 LTS` o `Ubuntu Server 22.04 LTS` (64-bit x86).
4. **Tipo de Instancia:** `t2.micro` o `t3.small` (apta para capa de laboratorio).
5. **Key Pair (Par de Claves):** Cree una nueva clave (ej. `bersaj-key.pem`) o seleccione una existente y descárguela en su equipo.
6. **Network Settings (Configuración de Seguridad):**
   * Crear Security Group con las siguientes reglas de entrada (**Inbound Rules**):
     * **SSH (Puerto 22):** Origen `Anywhere (0.0.0.0/0)`
     * **HTTP (Puerto 80):** Origen `Anywhere (0.0.0.0/0)` (para el API Gateway Nginx)
     * **HTTPS (Puerto 443):** Origen `Anywhere (0.0.0.0/0)`
7. Haga clic en **Launch Instance**.

---

### Paso 3: Asignar una IP Elástica (Requisito Obligatorio)
> La rúbrica exige compartir la **IP elástica** de AWS en la entrega institucional.
1. En el menú lateral izquierdo de EC2, vaya a **Network & Security** > **Elastic IPs**.
2. Haga clic en **Allocate Elastic IP address** > **Allocate**.
3. Seleccione la IP asignada, haga clic en **Actions** > **Associate Elastic IP address**.
4. Seleccione su instancia `bersaj-ecommerce-server` y haga clic en **Associate**.
5. ¡Copie esta IP pública elástica! Esta será la URL de entrega (ejemplo: `http://54.210.xxx.xxx`).

---

### Paso 4: Conectarse por SSH a la Instancia
Abra su terminal (PowerShell o Git Bash) y conéctese:
```bash
ssh -i /ruta/a/bersaj-key.pem ubuntu@<TU_IP_ELASTICA>
```

---

### Paso 5: Instalar Docker y Docker Compose en la Instancia
Ejecute los siguientes comandos en la terminal de la máquina virtual Ubuntu:

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
sudo apt install -y docker.io docker-compose-v2 git

# Habilitar e iniciar el servicio de Docker
sudo systemctl enable --now docker

# Agregar el usuario ubuntu al grupo docker
sudo usermod -aG docker ubuntu

# Aplicar los permisos sin reiniciar
newgrp docker
```

---

### Paso 6: Clonar el Repositorio y Desplegar
```bash
# Clonar el proyecto (rama main o dev)
git clone https://github.com/AdyuerHack/e-comerce-bersaj.git
cd e-comerce-bersaj

# Verificar que estemos en la rama correcta
git checkout dev

# Construir y levantar todos los contenedores en segundo plano
docker compose up -d --build
```

---

### Paso 7: Verificación del Despliegue
1. Verifique que los 5 contenedores estén corriendo (`Up`):
   ```bash
   docker compose ps
   ```
   Debe observar activos:
   * `bersaj_api_gateway` (Nginx :80)
   * `bersaj_django_core` (Django Core)
   * `bersaj_flask_catalog` (Flask :5001)
   * `bersaj_redis_broker` (Redis :6379)
   * `bersaj_celery_worker` (Celery)

2. Verifique los logs en tiempo real:
   ```bash
   docker compose logs -f
   ```

3. Abra su navegador web e ingrese a:
   * **Tienda Web:** `http://<TU_IP_ELASTICA>/`
   * **Catálogo Público (Servicio a Proveer):** `http://<TU_IP_ELASTICA>/api/v1/public/catalog`
   * **Productos (Microservicio Flask ruteado por Nginx):** `http://<TU_IP_ELASTICA>/api/v1/products`
   * **Integración Aliado:** `http://<TU_IP_ELASTICA>/tienda/aliado/`
   * **Healthcheck Gateway:** `http://<TU_IP_ELASTICA>/health`

---

### Recordatorio Crucial para la Sustentación
> [!WARNING]
> Recuerde encender la instancia EC2 al menos 15 minutos antes de la sustentación con el profesor y verificar que responda en la IP elástica.
