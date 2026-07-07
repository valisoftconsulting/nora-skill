# Eval C — Migrar proceso UiPath

**Prompt de prueba:**
> Tenemos un proceso UiPath con REFramework que procesa órdenes desde una
> Orchestrator Queue "Ordenes", usa un Credential Asset "SAP_Cred" y un
> Config.xlsx, y corre con un Time Trigger a las 6am. Migralo a NORA.

**El agente debe:**
1. Pedir/leer el proyecto origen (XAML, Config.xlsx) o trabajar con la
   descripción, y producir la TABLA DE MAPEO llenada (queue→cola,
   BusinessRuleException→business, Config.xlsx→inputs+assets, trigger→schedule)
   para aprobación ANTES de codificar.
2. Recrear infraestructura con scripts: `nora_queue.py create Ordenes`,
   `nora_asset.py set SAP_Cred --type credential --env dev`.
3. Implementar sobre `robot-transactional` conservando los nombres de fase.
4. Proponer migración de items en vuelo (`nora_queue.py bulk`) y corrida en
   paralelo antes de apagar el bot UiPath.
5. Schedule: `nora_schedule.py create --cron "0 6 * * *"`.

**Falla si:** intenta "transpilar" XAML; no presenta la tabla de mapeo; mapea
BusinessRuleException a system; olvida la corrida en paralelo.
