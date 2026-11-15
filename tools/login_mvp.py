"""Autenticación privada de un operador MVP mediante PBKDF2-SHA256.

Configurar ESCANEO3D_MVP_PASSWORD_HASH como
pbkdf2_sha256$600000$<sal_hex_16_bytes>$<hash_hex_32_bytes>.
No guardar contraseñas en el repositorio ni variables en texto plano.
"""
import base64
import hashlib
import hmac
import json
import os
import time


def comprobar_clave(clave):
    almacenado = os.environ.get("ESCANEO3D_MVP_PASSWORD_HASH", "")
    try:
        algoritmo, iteraciones, sal, esperado = almacenado.split("$")
        if algoritmo != "pbkdf2_sha256" or not 600000 <= int(iteraciones) <= 1200000:
            return False
        sal_bytes = bytes.fromhex(sal)
        esperado_bytes = bytes.fromhex(esperado)
        if len(sal_bytes) < 16 or len(esperado_bytes) != 32:
            return False
        obtenido = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal_bytes,
                                       int(iteraciones), dklen=32)
        return hmac.compare_digest(obtenido, esperado_bytes)
    except (ValueError, TypeError, OverflowError, AttributeError):
        return False


def emitir_token(usuario):
    secreto = os.environ["ESCANEO3D_JWT_SECRET"]
    if len(secreto.encode("utf-8")) < 32:
        raise RuntimeError("Secreto JWT demasiado corto")
    ahora = int(time.time())
    cabecera = {"alg": "HS256", "typ": "JWT"}
    cuerpo = {"sub": usuario, "iss": os.environ["ESCANEO3D_JWT_ISSUER"],
              "aud": os.environ["ESCANEO3D_JWT_AUDIENCE"], "iat": ahora,
              "exp": ahora + 3600}
    def codificar(valor):
        return base64.urlsafe_b64encode(json.dumps(valor, separators=(",", ":")).encode()).rstrip(b"=").decode()
    mensaje = codificar(cabecera) + "." + codificar(cuerpo)
    firma = base64.urlsafe_b64encode(hmac.new(secreto.encode(), mensaje.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    return mensaje + "." + firma
