"""Configuración del robot. Solo constantes — nada de lógica."""

# Nombre EXACTO de la cola en NORA.
QUEUE = "mi-cola"

# Campo del registro fuente que identifica de forma única cada item.
# Se usa como `reference` del queue item → idempotencia: si el dispatcher
# corre dos veces, no duplica trabajo.
REFERENCE_FIELD = "id"
