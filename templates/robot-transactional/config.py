"""Configuración del robot. Solo constantes — nada de lógica."""

# Nombre EXACTO de la cola en NORA (créala antes con la consola o
# `nora_queue.py create`). max_retries de la cola gobierna los reintentos
# de las excepciones de sistema.
QUEUE = "mi-cola"

# Assets que este robot lee en runtime. Decláralos también en el proceso
# (required_assets) para que el token del job quede acotado a ellos.
ASSETS = {
    # "app_credenciales": "credential",  # nombre → tipo (documentativo)
}
