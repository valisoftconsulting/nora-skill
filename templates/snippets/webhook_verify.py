"""Verificación de webhooks SALIENTES de NORA en tu servidor receptor.

NORA firma cada entrega con:
    X-NORA-Timestamp: <unix seconds>
    X-NORA-Signature: sha256=<HMAC_SHA256(secret, "<timestamp>.<raw_body>")>

El secret (`nora_whsec_...`) se genera al crear el canal de notificación.
Copia esta función a tu receptor (Flask/FastAPI/Django/lambda).
"""

from __future__ import annotations

import hashlib
import hmac
import time

MAX_SKEW_SECONDS = 300  # rechaza entregas con timestamp a más de 5 min (anti-replay)


def verify_nora_signature(
    secret: str,
    timestamp: str,
    raw_body: bytes,
    signature: str,
    max_skew: int = MAX_SKEW_SECONDS,
) -> bool:
    """True solo si la firma es válida y el timestamp está dentro de la ventana."""
    if not (secret and timestamp and signature):
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - ts) > max_skew:
        return False

    signed = f"{timestamp}.".encode() + raw_body
    expected = "sha256=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# --- Ejemplo FastAPI -------------------------------------------------------------
# from fastapi import FastAPI, Header, HTTPException, Request
#
# app = FastAPI()
# SECRET = "nora_whsec_..."  # desde tu gestor de secretos, NUNCA hardcodeado
#
# @app.post("/webhooks/nora")
# async def nora_webhook(
#     request: Request,
#     x_nora_timestamp: str = Header(""),
#     x_nora_signature: str = Header(""),
# ):
#     body = await request.body()
#     if not verify_nora_signature(SECRET, x_nora_timestamp, body, x_nora_signature):
#         raise HTTPException(status_code=401, detail="Firma inválida")
#     event = await request.json()   # {"event": "job_failed", ...}
#     ...
#     return {"ok": True}
