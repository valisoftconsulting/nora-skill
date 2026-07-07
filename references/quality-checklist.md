# Checklist de calidad pre-release (definition of done)

Recórrela ítem por ítem antes de `nora release push` y reporta al usuario el
estado de cada punto. Un "no aplica" justificado es válido; un "no lo revisé"
no.

## Contrato

- [ ] `nora.json` pasa `validate_manifest.py` sin errores.
- [ ] Todos los inputs tienen `description` (el operador la ve en el formulario).
- [ ] Los outputs declarados se publican SIEMPRE (también en corridas con 0 items).
- [ ] `version` refleja el cambio (nora package hace bump automático).

## Seguridad

- [ ] Cero credenciales/URLs internas hardcodeadas: todo por `asset()` o inputs.
- [ ] Ningún `.env` ni secreto dentro de la carpeta empaquetable (`nora package --list` para verificar).
- [ ] Los logs NO imprimen valores de assets ni datos sensibles (¡ni en errores!).
- [ ] Assets declarados en `required_assets` del proceso (token del job acotado).

## Robustez

- [ ] Excepciones clasificadas: datos inválidos → `BusinessError`/`fail_business`; el resto propaga → `fail_system`.
- [ ] Sin reintentos manuales alrededor de transacciones (los hace la plataforma).
- [ ] `should_stop()` chequeado en cada iteración de loops largos.
- [ ] Recursos liberados en `finally`/`end()` (navegador, sesiones, archivos).
- [ ] El robot es re-ejecutable: si el job se relanza, no duplica trabajo
      (referencias de cola, checks de existencia).

## Observabilidad

- [ ] `log()` en hitos: inicio con parámetros, por transacción (referencia + resultado), resumen final.
- [ ] `update_progress()` con porcentaje real en jobs de más de ~1 minuto.
- [ ] Outputs con contadores: procesados / fallidos_negocio / fallidos_sistema.

## Empaque

- [ ] `requirements.txt` presente si hay deps de terceros, con versiones fijadas.
- [ ] `.noraignore` excluye tests/, data local y artefactos.
- [ ] Python ≥ 3.10; sin rutas absolutas de tu máquina en el código.
- [ ] README del robot: qué hace, inputs/outputs, cola y assets que necesita.

## Validación

- [ ] Niveles 1–4 de `testing-and-validation.md` en verde.
- [ ] Tras publicar: smoke e2e (`nora_smoke.py`) en verde.
