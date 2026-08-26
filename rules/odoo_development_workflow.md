# 🤖 Reglas de Desarrollo en Odoo (AI System Instructions)

Este documento define las reglas estrictas, principios de desarrollo y el algoritmo de ejecución secuencial que toda Inteligencia Artificial (o desarrollador) debe seguir al abordar una Historia de Usuario (HU) o proyecto en Odoo.

**El objetivo principal es entregar código limpio, escalable, mantenible y estrictamente apegado a los estándares de Odoo.**

---

## 💎 1. Principios de Desarrollo de Alto Valor

Antes de escribir código, se deben interiorizar y aplicar estos principios universales adaptados al ecosistema Odoo:

*   **DRY (Don't Repeat Yourself):** Utiliza al máximo el ORM y las funciones nativas de Odoo. No reescribas lógica que ya existe en los módulos core (ej. cálculo de impuestos, movimientos de stock).
*   **KISS (Keep It Simple, Stupid):** Aprovecha los widgets y vistas estándar de Odoo. Evita crear componentes web (OWL/JS) complejos si una vista `form` o `tree` estándar cumple el objetivo.
*   **YAGNI (You Aren't Gonna Need It):** Limítate estrictamente a los Criterios de Aceptación de la HU. No crees campos, modelos o métodos "por si acaso se necesitan en el futuro".
*   **SOLID (Responsabilidad Única):** La lógica de un módulo debe permanecer en su dominio. Si haces una HU de Ventas que afecta Inventario, no metas toda la lógica en `sale.order`. Extiende `stock.picking` mediante un módulo puente si es necesario.
*   **Clean Code & Odoo Guidelines:**
    *   Respeta PEP-8.
    *   Evita consultas SQL crudas (`self.env.cr.execute`) a menos que el ORM sea un cuello de botella comprobado.
    *   Nombra los campos booleanos con el prefijo `is_` (ej. `is_active`).
    *   Nombra los campos relacionales One2many o Many2many en plural (ej. `line_ids`).
    *   Nombra los campos Many2one en singular terminando en `_id` (ej. `partner_id`).

---

## 🏗️ 2. Algoritmo de Ejecución Secuencial (El Flujo de Trabajo)

La IA debe seguir estrictamente este orden al generar e implementar la solución:

### Paso 1: Análisis y Arquitectura
1.  **Entender:** Leer la HU y extraer las entidades (Modelos), los datos (Campos) y la lógica de negocio (Métodos).
2.  **Impacto:** Identificar dependencias necesarias (ej. `base`, `sale_management`, `stock`).
3.  **Decisión:** Elegir entre herencia (`_inherit`) o modelo nuevo (`_name`).

### Paso 2: Configuración Inicial
1.  Crear `__manifest__.py` con `name`, `version`, `depends`, y la estructura `data`.
2.  Crear `__init__.py` raíz y en subcarpetas.

### Paso 3: Backend (Modelos - `models/`)
1.  **Campos:** Definir campos simples y relacionales.
2.  **Constraints:** Definir restricciones lógicas (`_sql_constraints` o `@api.constrains`).
3.  **Cálculos:** Implementar métodos computados (`@api.depends`).
4.  **Eventos:** Implementar métodos Onchange (`@api.onchange`).
5.  **Lógica:** Sobrescribir métodos core (`create`, `write`, `action_confirm`) usando `super()`.

### Paso 4: Seguridad (`security/`)
1.  **Grupos:** Crear `ir.model.category` y `res.groups` en archivos XML (si se requiere control de acceso específico).
2.  **Permisos:** Configurar `ir.model.access.csv` (1,1,1,1 o según aplique).
3.  **Reglas de Registro:** Definir `ir.rule` para limitar visibilidad de registros.

### Paso 5: Frontend (Vistas - `views/`)
1.  **Vistas:** Crear o heredar vistas XML (`form`, `tree`, `kanban`).
2.  **Herencia Segura:** Usar XPATH con cuidado (preferir `position="after"` o `position="before"`; evitar `position="replace"` a menos que sea indispensable).
3.  **Acciones:** Crear `ir.actions.act_window`.
4.  **Menús:** Definir `menuitem` y su jerarquía.

### Paso 6: Integración y Manifest
1.  Asegurar que todos los archivos XML de seguridad y vistas estén correctamente ordenados en el array `'data'` del `__manifest__.py`. **Regla de oro: Seguridad va primero, luego vistas.**

---

## 🛡️ 3. Validación de Buenas Prácticas (Checklist de la IA)

Antes de entregar el código al usuario o dar la tarea por finalizada, la IA **DEBE** auto-validar lo siguiente:

> [!WARNING]
> **Checklist de Rendimiento y ORM:**
> - [ ] **No hay queries N+1:** ¿Las búsquedas en bucles usan `mapped()`, `filtered()` o lecturas en lote de `self`?
> - [ ] **Dependencias de Computados:** ¿Todos los métodos `@api.depends` incluyen TODOS los campos que afectan el cálculo?
> - [ ] **Almacenamiento de Computados:** ¿Se justificó correctamente el uso de `store=True` en campos computados (solo si se necesita buscar o agrupar por ese campo)?

> [!IMPORTANT]
> **Checklist de Seguridad y Arquitectura:**
> - [ ] **Llamadas a `super()` seguras:** Al sobrescribir `create` o `write`, ¿se retorna el resultado de `super()` correctamente?
> - [ ] **Permisos base:** ¿Todo modelo nuevo tiene al menos una regla en `ir.model.access.csv`?
> - [ ] **Dependencias Manifest:** ¿Si se usó un campo o vista de un módulo externo, se agregó dicho módulo al array `'depends'`?

> [!TIP]
> **Checklist de Interfaz (Vistas):**
> - [ ] **Campos requeridos invisibles:** Si un campo es requerido (`required=True`), ¿está presente en la vista formulario (aunque sea invisible) para evitar errores del ORM?
> - [ ] **Widgets nativos:** ¿Se usaron los widgets nativos correctos (ej. `widget="monetary"`, `widget="many2many_tags"`) para mejorar la UX?

---
*Fin de las instrucciones. La IA debe procesar las siguientes peticiones del usuario asumiendo y aplicando todo lo establecido en este documento.*
