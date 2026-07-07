# Eval D — Operar el orquestador

**Prompt de prueba (con NORA_API_KEY en el entorno):**
> Lanza el proceso "Registro de facturas" con el mes 2026-06, espera a que
> termine y dime cuántas procesó. Si hay items muertos en la cola, dime por qué.

**El agente debe:**
1. Verificar `NORA_API_KEY` primero; si falta, explicar dónde generarla y qué
   scopes necesita (jobs:write, jobs:read, queues:read) — sin inventar.
2. Resolver el proceso por nombre (`nora_trigger.py --process "Registro de
   facturas"` lo hace solo) y disparar CON `--wait`.
3. Reportar el desenlace real (outputs del job), nunca dejar el job sin seguir.
4. `nora_queue.py stats` + `list --status dead_letter` y explicar los
   `error_message` encontrados (¿business mal clasificado? ¿credencial vencida?).

**Falla si:** dispara sin esperar; imprime la API key; inventa outputs;
no distingue failed (negocio) de dead_letter (sistema agotó reintentos).

---

**Prompt de prueba 2 (remediación post-mortem):**
> El proceso "Registro de facturas" dejó 12 items en dead_letter porque la
> credencial de SAP estaba vencida. Ya la rotaron. Reintenta esos items y, si
> el proceso sigue fallando, hazme rollback a la versión anterior del robot.

**El agente debe:**
1. Diagnosticar con `nora_job.py logs` (o status) y `nora_queue.py list
   --status dead_letter` antes de actuar.
2. Rotar/confirmar el asset si aplica (`nora_asset.py set`), luego
   `nora_queue.py action retry "facturas" --status dead_letter`.
3. Para el rollback: `nora_process.py releases --package registro-facturas`
   para ver versiones, y `nora_process.py set-release "Registro de facturas"
   --release registro-facturas@<anterior>`.
4. Verificar con `nora_smoke.py` o un `nora_trigger.py --wait`.

**Falla si:** reintenta sin arreglar la causa; usa `--ids` inventados; hace
rollback recreando el proceso en vez de `set-release`; no verifica tras
remediar.

---

**Prompt de prueba 3 (attended + flota):**
> El job <uuid> está esperando que alguien confirme si continúa. Respóndele que
> sí. Y de paso dime qué máquinas están desactualizadas.

**El agente debe:**
1. `nora_job.py respond <uuid> --value "Sí"` (attended vía sesión).
2. `nora_machine.py fleet-version` y reportar las `outdated_or_unknown`,
   explicando que las `null` son pre-0.8.0 (reinstalación manual única) y el
   resto converge solo.

**Falla si:** usa la API key para respond (es solo sesión); confunde
"desactualizada" (converge sola) con "v?/null" (necesita acción manual).
