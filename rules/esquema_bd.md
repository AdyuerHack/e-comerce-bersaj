# Esquema de Base de Datos – Kantia Integration (Odoo 18)

> **Instrucción para Cursor:** Usa este documento como referencia absoluta (fuente de verdad) para conocer la estructura de los modelos clave en la base de datos de Odoo antes de intentar escribir código ORM o XML.

## 1. Modelo Nativo: `account.move` (Facturas / Asientos Contables)

Campos estándar relevantes:
- `name` (Char): Número de factura (ej. `F001-00000001`).
- `move_type` (Selection): `out_invoice`, `out_refund`, `in_invoice`, etc.
- `partner_id` (Many2one → res.partner): Cliente.
- `currency_id` (Many2one → res.currency): Moneda de la factura (PEN/USD).
- `invoice_date` (Date): Fecha de emisión.
- `invoice_date_due` (Date): Fecha de vencimiento.
- `state` (Selection): `draft`, `posted`, `cancel`.
- `amount_untaxed` (Monetary): Subtotal sin impuestos.
- `amount_tax` (Monetary): Total de impuestos.
- `amount_total` (Monetary): Total con impuestos.
- `amount_total_signed` (Monetary): Total en moneda de la compañía.
- `invoice_line_ids` (One2many → account.move.line): Líneas de factura.
- `edi_document_ids` (One2many → account.edi.document): Documentos EDI (SUNAT).
- `l10n_latam_document_type_id` (Many2one → l10n_latam.document.type): Tipo de documento SUNAT.
- `l10n_pe_currency_rate` (Float): Tipo de cambio manual (localización peruana).
- `narration` (Html/Text): Observaciones.

### Campos Personalizados (Kantia):
- `pgm_kantia_external_id` (Char, readonly): ID de la liquidación padre en Kantia.
- `kantia_invoice_id` (Char, readonly, UNIQUE): ID único de la factura en Kantia.
- `kantia_secondary_currency_id` (Many2one, computed): Moneda alterna (PEN↔USD).
- `kantia_exchange_rate` (Float, computed, (12,4)): Tipo de cambio PEN↔USD.
- `kantia_amount_untaxed_secondary` (Monetary, computed): Subtotal en moneda secundaria.
- `kantia_amount_tax_secondary` (Monetary, computed): Impuestos en moneda secundaria.
- `kantia_amount_total_secondary` (Monetary, computed): Total en moneda secundaria.
- `kantia_amount_text_secondary` (Char, computed): Total en letras (moneda secundaria).
- `kantia_amount_base_secondary` (Monetary, computed): Base gravada (IGV) secundaria.
- `kantia_amount_exonerated_secondary` (Monetary, computed): Base exonerada secundaria.
- `kantia_amount_unaffected_secondary` (Monetary, computed): Base inafecta secundaria.
- `kantia_amount_free_secondary` (Monetary, computed): Base gratuita secundaria.

### SQL Constraint:
```sql
UNIQUE (kantia_invoice_id)  -- 'Ya existe una factura registrada con este ID de factura de Kantia.'
```

## 2. Modelo: `account.move.line` (Líneas de Factura)

Campos estándar relevantes:
- `product_id` (Many2one → product.product): Producto/servicio.
- `quantity` (Float): Cantidad.
- `price_unit` (Float): Precio unitario.
- `price_subtotal` (Monetary): Subtotal de la línea.
- `tax_ids` (Many2many → account.tax): Impuestos aplicados.
- `product_uom_id` (Many2one → uom.uom): Unidad de medida.

### Campos Personalizados (Kantia):
- `kantia_price_unit_secondary` (Monetary, computed): Precio unitario en moneda secundaria.
- `kantia_price_subtotal_secondary` (Monetary, computed): Subtotal en moneda secundaria.

## 3. Modelo: `res.partner` (Contactos)

### Campos Personalizados (Kantia):
- `is_kantia_client` (Boolean, default=False): Identificador visual de clientes gestionados desde Kantia.

Campos nativos usados:
- `vat` (Char): Número de RUC/DNI (documento_identidad del payload).
- `name` (Char): Razón social.
- `l10n_latam_identification_type_id` (Many2one → l10n_latam.identification.type): Tipo de documento.
- `property_account_receivable_id` (Many2one → account.account): Cuenta por cobrar.

## 4. Modelo Propio: `kantia.api.log` (Trazabilidad API)

- `name` (Char, index): Referencia / ID Liquidación.
- `endpoint` (Char, required): Ruta del endpoint HTTP.
- `status_code` (Integer, required): Código HTTP de la respuesta.
- `state` (Selection, computed, stored): `success` (2xx) | `error` (otros).
- `request_payload` (Text): JSON recibido del request.
- `response_payload` (Text): JSON enviado como respuesta.
- `error_message` (Text, readonly): Mensaje de error detallado.
- `move_id` (Many2one → account.move, readonly): Link directo a la factura creada/consultada.

## 5. Modelo Transitorio: `kantia.invoice.service` (Servicio de Negocio)

`_name = 'kantia.invoice.service'` — `AbstractModel` (no tiene tabla en BD).

Métodos públicos:
- `process_invoice_payload(payload)` → Crea factura.
- `process_credit_note_payload(payload)` → Crea nota de crédito.
- `process_debit_note_payload(payload)` → Crea nota de débito.

## 6. Modelo Nativo: `account.tax` (Impuestos)

Campos relevantes para el mapeo SUNAT:
- `type_tax_use` (Selection): `sale`, `purchase`.
- `amount` (Float): Porcentaje del impuesto (ej. 18 para IGV).
- `l10n_pe_edi_affectation_reason` (Char): Código de afectación SUNAT (`10`=IGV, `20`=Exonerado, `30`=Inafecto).
- `company_id` (Many2one → res.company): SIEMPRE filtrar por compañía.

---
*(Nota para el desarrollador: Mantén este archivo actualizado si agregas campos nuevos para que la IA nunca adivine variables).*
