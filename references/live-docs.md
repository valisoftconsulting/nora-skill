# Docs vivas de NORA — cuándo y cómo consultarlas

Documentación oficial: **https://docs.valisoftconsulting.com** (español).

## Formatos para agentes de IA

| URL | Contenido | Cuándo |
| --- | --- | --- |
| `/llms.txt` | índice de todas las páginas | para descubrir qué existe |
| `/llms-small.txt` | resumen compacto de toda la plataforma | contexto general rápido |
| `/llms-full.txt` | TODO el sitio en un archivo | ⚠ grande — evita cargarlo entero; prefiere fetch selectivo de páginas del índice |
| `/referencia/operar-con-ia/` | guía escrita PARA agentes (modelo mental + recetas tarea→API) | operación |

## Regla de decisión

- **Contratos estables** (firmas del SDK, esquema de nora.json, endpoints,
  semántica business/system): usa las references de ESTE skill — están
  verificadas contra el código y `self_check.py` detecta drift.
- **Lo volátil**: planes y precios, límites por plan, features nuevas,
  tutoriales extensos, troubleshooting de instalación del agente → consulta
  las docs vivas (WebFetch de la página concreta del índice `/llms.txt`).
- **Conflicto entre este skill y las docs vivas** → ganan las docs vivas.
  Avisa al usuario del desfase para que actualice el skill (y se registre en
  CHANGELOG.md).

## Páginas más útiles por tarea

| Tarea | Página |
| --- | --- |
| Primer robot paso a paso | `/tutoriales/primer-robot-minimo/` |
| Colas end-to-end (RPA Challenge) | `/tutoriales/rpa-challenge-colas/` |
| Instalación del agente en una máquina | `/guia/instalacion-agente/` |
| Argumentos in/out | `/guia/argumentos/` |
| Planes y facturación | `/guia/planes-y-facturacion/` |
| Flujos DAG multi-proceso | `/guia/flujos-dag/` |
| Endpoints de gestión (crear colas/assets/procesos) | `/api/gestion/` |
| Cheat sheet SDK+CLI+API | `/referencia/lamina-comandos/` |
| Migración UiPath / AA | `/migracion/desde-uipath/` · `/migracion/desde-automation-anywhere/` |
