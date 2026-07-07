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
