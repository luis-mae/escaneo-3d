"""Conecta una nube COLMAP PLY con el mallador alpha-shape existente."""
import argparse
import json
from pathlib import Path
from scipy.spatial import QhullError, cKDTree
import numpy as np

from .leer_colmap_ply import leer_nube_colmap_ply
from .pipeline_superficie import procesar
from .superficie_nube import generar_superficie
from .superficie_nube import guardar_obj


def filtrar_atipicos(puntos, vecinos=12, umbral=3.0):
    """Elimina puntos aislados usando distancias k-NN y MAD robusta.

    Conserva la nube original si el filtrado dejaría menos de cuatro puntos.
    No presupone que la nube representa solamente el objeto fotografiado.
    """
    puntos = np.asarray(puntos, dtype=np.float64)
    if puntos.ndim != 2 or puntos.shape[1] != 3 or not np.isfinite(puntos).all():
        raise ValueError("Nube XYZ inválida")
    if not isinstance(vecinos, (int, np.integer)) or vecinos < 3:
        raise ValueError("vecinos debe ser entero y >= 3")
    if not np.isfinite(umbral) or umbral <= 0:
        raise ValueError("umbral MAD debe ser positivo y finito")
    if len(puntos) < 16:
        return puntos, {"puntos_descartados": 0, "motivo": "nube_pequena"}
    k = min(max(3, int(vecinos)), len(puntos) - 1)
    distancias, _ = cKDTree(puntos).query(puntos, k=k + 1, workers=1)
    dist_media = np.mean(distancias[:, 1:], axis=1)
    mediana = float(np.median(dist_media))
    mad = float(np.median(np.abs(dist_media - mediana)))
    # Evita dividir por cero en nubes uniformes.
    if mad <= np.finfo(float).eps * max(1.0, abs(mediana)):
        return puntos, {"puntos_descartados": 0, "motivo": "dispersion_nula"}
    limite = mediana + float(umbral) * 1.4826 * mad
    mascara = dist_media <= limite
    if np.count_nonzero(mascara) < 4:
        return puntos, {"puntos_descartados": 0, "motivo": "filtrado_excesivo_evitado"}
    return puntos[mascara], {
        "puntos_descartados": int(len(puntos) - np.count_nonzero(mascara)),
        "vecinos": k, "umbral_mad": float(umbral),
        "distancia_media_limite": limite,
    }


def nube_colmap_a_malla(entrada, salida, alpha, max_puntos=50_000, submuestrear=True, filtrar_ruido=False):
    entrada, salida = Path(entrada).resolve(), Path(salida).resolve()
    if entrada == salida or salida.exists():
        raise FileExistsError("Salida existente o igual a entrada; no sobrescribir")
    if salida.suffix.lower() != ".obj":
        raise ValueError("La salida debe ser OBJ")
    puntos = leer_nube_colmap_ply(entrada, max_puntos=max_puntos,
                                  submuestrear=submuestrear)
    # El mallado tetraédrico exige cuatro puntos geométricamente distintos.
    puntos = np.unique(puntos, axis=0)
    informe_filtrado = {"activado": bool(filtrar_ruido), "puntos_descartados": 0}
    if filtrar_ruido:
        puntos, detalle = filtrar_atipicos(puntos)
        informe_filtrado.update(detalle)
    if len(puntos) < 4:
        raise ValueError("La nube no contiene cuatro puntos 3D distintos")
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("Alpha debe ser positivo y finito")
    if not isinstance(max_puntos, int) or max_puntos < 4:
        raise ValueError("max_puntos debe ser un entero >= 4")
    # Un alpha estimado demasiado pequeño puede no aceptar ningún tetraedro.
    # Reintentar con radios mayores antes de perder las concavidades en una
    # envolvente convexa. Cada intento queda registrado para diagnóstico.
    intentos = []
    resultado_alpha = None
    for factor in (1.0, 2.0, 4.0):
        radio = float(alpha) * factor
        if not np.isfinite(radio):
            intentos.append({"alpha": None, "resultado": "fallido",
                             "motivo": "radio excede el rango numérico"})
            break
        try:
            vertices, caras, informe = procesar(puntos, radio)
            if len(caras) < 4:
                raise ValueError("Malla con menos de cuatro caras")
            informe["metodo_superficie"] = "alpha_shape"
            informe["alpha_efectivo"] = radio
            resultado_alpha = (vertices, caras, informe)
            intentos.append({"alpha": radio, "resultado": "completado"})
            break
        except (ValueError, RuntimeError, MemoryError, QhullError) as exc:
            intentos.append({"alpha": radio, "resultado": "fallido",
                             "motivo": str(exc)[:200]})
            if isinstance(exc, MemoryError):
                # No repetir un mallado que agotó memoria.
                break
    if resultado_alpha is not None:
        vertices, caras, informe = resultado_alpha
    else:
        # Vista preliminar de respaldo: no conserva concavidades.
        vertices, caras, volumen = generar_superficie(puntos)
        informe = {
            "vertices": int(len(vertices)), "caras": int(len(caras)),
            "metodo_superficie": "envolvente_convexa_respaldo",
            "motivo_respaldo": intentos[-1]["motivo"] if intentos else "sin intentos",
            "volumen_unidades_arbitrarias": volumen,
            "apto_para_impresion": False,
            "advertencia": "Envolvente convexa aproximada: no conserva concavidades ni detalles.",
        }
    informe["intentos_alpha"] = intentos
    if not len(caras):
        raise ValueError("No se pudo construir ninguna cara para la malla OBJ")
    # Informar si la malla se generó con una envolvente convexa de respaldo:
    # ese resultado no debe interpretarse como reconstrucción fiel del objeto.
    informe["geometria_de_respaldo"] = informe.get("metodo_superficie") == "envolvente_convexa_respaldo"
    salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_obj(salida, vertices, caras)
    informe.update({"origen": str(entrada), "salida": str(salida),
                    "motor_fotogrametria": "COLMAP",
                    "puntos_procesados": len(puntos),
                    "filtrado_atipicos": informe_filtrado,
                    "submuestreo_determinista": bool(submuestrear)})
    salida.with_suffix(".informe.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path, help="fused.ply o modelo_0.ply de COLMAP")
    p.add_argument("--salida", required=True, type=Path)
    p.add_argument("--alpha", required=True, type=float)
    p.add_argument("--max-puntos", type=int, default=200_000)
    p.add_argument("--filtrar-ruido", action="store_true",
                   help="Eliminar puntos aislados antes del mallado (experimental)")
    args = p.parse_args()
    print(json.dumps(nube_colmap_a_malla(args.entrada, args.salida, args.alpha,
                                        args.max_puntos, filtrar_ruido=args.filtrar_ruido), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
