"""Comprobación reproducible de API e interfaz en una instancia ya levantada.

Uso: python -m tools.verificar_mvp --url http://127.0.0.1:8000
No ejecuta COLMAP ni sustituye la prueba con fotografías reales.
"""
import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen


def comprobar(base):
    if not base.startswith(("http://127.0.0.1:", "http://localhost:")):
        raise ValueError("Este chequeo inicial solo admite un servidor local")
    comprobaciones = (
        ("/api/salud", b"colmap_detectado"),
        ("/", b"ESCANEO 3D"),
        ("/app.js", b"MAX_FOTOS"),
    )
    resultados = {}
    for ruta, marca in comprobaciones:
        try:
            with urlopen(urljoin(base.rstrip("/") + "/", ruta.lstrip("/")), timeout=10) as respuesta:
                cuerpo = respuesta.read(2_000_000)
                correcto = respuesta.status == 200 and marca in cuerpo
                resultados[ruta] = {"ok": correcto, "http": respuesta.status}
                if ruta == "/api/salud" and correcto:
                    salud = json.loads(cuerpo)
                    resultados[ruta]["colmap_detectado"] = bool(salud.get("colmap_detectado"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            resultados[ruta] = {"ok": False, "error": str(exc)}
    return resultados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    resultados = comprobar(args.url)
    print(json.dumps(resultados, indent=2, ensure_ascii=False))
    if not all(item["ok"] for item in resultados.values()):
        raise SystemExit(1)
    if not resultados["/api/salud"].get("colmap_detectado"):
        print("AVISO: la interfaz responde, pero COLMAP no está detectado.")


if __name__ == "__main__":
    main()
