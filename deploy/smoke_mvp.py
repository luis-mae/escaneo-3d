#!/usr/bin/env python3
"""Prueba del servidor ESCANEO 3D publicado sin subir fotografías."""
import argparse
import json
import sys
import urllib.error
import urllib.request


def solicitar(base, ruta, token=None, datos=None):
    cabeceras = {"Accept": "application/json"}
    if token:
        cabeceras["Authorization"] = "Bearer " + token
    if datos is not None:
        cabeceras["Content-Type"] = "application/json"
        datos = json.dumps(datos).encode("utf-8")
    req = urllib.request.Request(base.rstrip("/") + ruta, data=datos, headers=cabeceras,
                                 method="POST" if datos is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as respuesta:
            return respuesta.status, json.load(respuesta)
    except urllib.error.HTTPError as error:
        try:
            cuerpo = json.load(error)
        except (ValueError, OSError):
            cuerpo = {}
        return error.code, cuerpo


def verificar(base, usuario, clave):
    if not base.startswith("https://") and not base.startswith("http://127.0.0.1:"):
        raise ValueError("Se exige HTTPS, salvo prueba local en 127.0.0.1")
    estado, salud = solicitar(base, "/api/salud")
    assert estado == 200, f"Salud HTTP {estado}"
    assert salud.get("modo") == "remoto_autenticado", "Servidor no configurado como remoto privado"
    assert salud.get("colmap_detectado"), "COLMAP no está instalado en el servidor"
    print("OK: HTTPS/local, API y COLMAP")
    estado, _ = solicitar(base, "/api/proyectos")
    assert estado == 401, f"API sin credenciales debería devolver 401, devolvió {estado}"
    print("OK: proyectos privados")
    estado, datos = solicitar(base, "/api/sesion", datos={"usuario": usuario, "clave": clave})
    assert estado == 200 and datos.get("token"), f"Inicio de sesión fallido: HTTP {estado}"
    print("OK: inicio de sesión")
    estado, listado = solicitar(base, "/api/proyectos", token=datos["token"])
    assert estado == 200 and isinstance(listado.get("proyectos"), list), f"Listado: HTTP {estado}"
    print("OK: listado autenticado; proyectos:", len(listado["proyectos"]))
    print("PASS: servidor listo para probar subida de fotos; NO certifica reconstrucción 3D.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="https://dominio o http://127.0.0.1:8000")
    parser.add_argument("--usuario", required=True)
    args = parser.parse_args()
    from getpass import getpass
    try:
        verificar(args.url, args.usuario, getpass("Contraseña MVP: "))
    except (AssertionError, ValueError, OSError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
