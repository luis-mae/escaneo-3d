"""Comprobación reproducible de API e interfaz en una instancia ya levantada.

Uso: python -m tools.verificar_mvp --url http://127.0.0.1:8000
No ejecuta COLMAP ni sustituye la prueba con fotografías reales.
"""
import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen


def comprobar(base):
    url = urlsplit(base)
    if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost")
            or not url.port or url.username or url.password or url.path not in ("", "/")
            or url.query or url.fragment):
        raise ValueError("Este chequeo inicial solo admite un servidor HTTP local con puerto explícito")
    comprobaciones = (
        ("/api/salud", b"colmap_detectado"),
        ("/", b"ESCANEO 3D"),
        ("/app.js", b"MAX_FOTOS"),
        ("/styles.css", b"body"),
        ("/api/proyectos", b"proyectos"),
        ("/api/proyectos/00000000000000000000000000000000", b"Proyecto no encontrado"),
        ("/api/proyectos/id_invalido", b"Proyecto no encontrado"),
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
                    resultados[ruta]["ok"] = (isinstance(salud.get("colmap_detectado"), bool)
                        and salud.get("reconstruccion_densa") in ("disponible_sujeta_a_GPU_y_recursos", "no_disponible")
                        and isinstance(salud.get("trabajos_en_cola"), int)
                        and isinstance(salud.get("limite_trabajos"), int))
                if ruta == "/api/proyectos" and correcto:
                    datos = json.loads(cuerpo)
                    resultados[ruta]["ok"] = isinstance(datos.get("proyectos"), list)
                if ruta == "/" and correcto:
                    resultados[ruta]["ok"] = b"app.js" in cuerpo and b"styles.css" in cuerpo
        except HTTPError as exc:
            if ruta in ("/api/proyectos/00000000000000000000000000000000", "/api/proyectos/id_invalido") and exc.code == 404:
                try:
                    error = json.loads(exc.read(4096))
                    valido = isinstance(error, dict) and error.get("detail") == "Proyecto no encontrado"
                except (ValueError, UnicodeError):
                    valido = False
                resultados[ruta] = {"ok": valido, "http": 404}
            else:
                resultados[ruta] = {"ok": False, "error": str(exc)}
        except (URLError, TimeoutError, ValueError) as exc:
            resultados[ruta] = {"ok": False, "error": str(exc)}
    return resultados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--solo-api", action="store_true",
                        help="Verifica interfaz y rutas sin exigir COLMAP instalado")
    args = parser.parse_args()
    resultados = comprobar(args.url)
    print(json.dumps(resultados, indent=2, ensure_ascii=False))
    if not all(item["ok"] for item in resultados.values()):
        raise SystemExit(1)
    if not args.solo_api and not resultados["/api/salud"].get("colmap_detectado"):
        print("ERROR: COLMAP no está detectado; la reconstrucción de fotos no funcionará.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
