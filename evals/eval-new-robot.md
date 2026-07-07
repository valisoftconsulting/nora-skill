# Eval A — Robot nuevo desde cero

**Prompt de prueba:**
> Necesito un robot NORA que lea las facturas pendientes de un CSV, las
> registre una por una en el sistema contable (web) y me deje un resumen.
> Las credenciales del contable no pueden ir en el código. Si una factura no
> tiene RUC, no hay que reintentarla.

**El agente debe:**
1. Hacer la entrevista mínima (volumen, disparo, aprobación humana).
2. Elegir `robot-dispatcher-performer` (CSV = fuente, registro = performer) o
   `robot-transactional` con carga inicial — justificando.
3. Escribir `nora.json` PRIMERO y validarlo con `validate_manifest.py`.
4. Credenciales → asset `credential`; "sin RUC" → `BusinessError`
   (`fail_business`), errores web → system.
5. Usar `nora_helpers.py`; jamás llamar al SDK desde la lógica.
6. Recorrer la pirámide de validación (al menos niveles 1–3 sin credenciales)
   y dejar documentados los pasos 4–6.

**Falla si:** credenciales hardcodeadas; reintentos manuales; sin
`should_stop()` en el loop; publica sin validar; clasifica el RUC faltante
como system.
