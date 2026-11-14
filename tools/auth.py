"""Validación mínima de tokens JWT HS256 emitidos por un proveedor de identidad externo.

No emite tokens ni reemplaza un proveedor OIDC. En modo remoto exige un secreto
aleatorio de 256 bits y valida firma, emisor, audiencia y expiración.
"""
import base64
import hashlib
import hmac
import json
import os
import time


class TokenInvalido(ValueError):
    pass


def _decodificar(segmento):
    try:
        return base64.urlsafe_b64decode(segmento + "=" * (-len(segmento) % 4))
    except Exception as exc:
        raise TokenInvalido("Token mal formado") from exc


def validar_token(authorization):
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise TokenInvalido("Se requiere Bearer token")
    secreto = os.environ.get("ESCANEO3D_JWT_SECRET", "")
    if len(secreto.encode()) < 32:
        raise RuntimeError("ESCANEO3D_JWT_SECRET debe tener al menos 32 bytes")
    partes = authorization[7:].strip().split(".")
    if len(partes) != 3:
        raise TokenInvalido("JWT mal formado")
    try:
        cabecera = json.loads(_decodificar(partes[0]))
        claims = json.loads(_decodificar(partes[1]))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TokenInvalido("JWT mal formado") from exc
    if cabecera.get("alg") != "HS256" or cabecera.get("typ", "JWT") != "JWT":
        raise TokenInvalido("Algoritmo JWT no admitido")
    firmado = (partes[0] + "." + partes[1]).encode("ascii")
    esperado = hmac.new(secreto.encode(), firmado, hashlib.sha256).digest()
    if not hmac.compare_digest(esperado, _decodificar(partes[2])):
        raise TokenInvalido("Firma JWT inválida")
    ahora = int(time.time())
    if type(claims.get("exp")) is not int or claims["exp"] <= ahora:
        raise TokenInvalido("Token vencido o sin expiración")
    if "nbf" in claims and (type(claims["nbf"]) is not int or claims["nbf"] > ahora):
        raise TokenInvalido("Token todavía no válido")
    if claims.get("iss") != os.environ.get("ESCANEO3D_JWT_ISSUER"):
        raise TokenInvalido("Emisor JWT inválido")
    audiencia = os.environ.get("ESCANEO3D_JWT_AUDIENCE")
    claim_aud = claims.get("aud")
    if not (claim_aud == audiencia or (isinstance(claim_aud, list) and audiencia in claim_aud)):
        raise TokenInvalido("Audiencia JWT inválida")
    if "iat" in claims and (type(claims["iat"]) is not int or claims["iat"] > ahora + 30):
        raise TokenInvalido("Fecha de emisión JWT inválida")
    if "iat" in claims and claims["exp"] <= claims["iat"]:
        raise TokenInvalido("Intervalo de validez JWT inválido")
    if claims["exp"] - ahora > 86400:
        raise TokenInvalido("La vigencia máxima del token es de 24 horas")
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 200:
        raise TokenInvalido("Identidad JWT inválida")
    return subject.strip()
