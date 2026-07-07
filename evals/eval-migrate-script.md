# Eval B — Migrar script Python

**Setup:** dale al agente un script con: credenciales hardcodeadas, un loop
`for fila in csv.reader(...)` de 500 filas, `print()` por todos lados,
`except Exception: continue`, y un `time.sleep(3600)` en un `while True`.

**Prompt de prueba:**
> Migra este script a un robot NORA profesional.

**El agente debe:**
1. Presentar el INVENTARIO al usuario antes de tocar código (entradas,
   secretos, salidas, loops, excepts, el sleep).
2. Proponer: credenciales → assets; 500 filas → cola (regla >20 items);
   `while True + sleep` → schedule cron; `except: continue` → `fail_system`
   con mensaje.
3. Portar la lógica sin reescribirla (mismas transformaciones de datos).
4. Validar niveles 1–3 y comparar el comportamiento contra el script original.

**Falla si:** empieza a escribir código sin mostrar el inventario; reescribe
la lógica de negocio desde cero; deja el `except: continue`; no detecta el
cron implícito.
